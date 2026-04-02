#!/usr/bin/env python3
"""Goose MCP extension: NadirClaw usage stats and cost tracking.

Exposes tools to query token usage, cost breakdown, and budget status
from NadirClaw's request logs. Works as a stdio MCP server.

Usage:
    goose session --with-extension "python /path/to/goose_usage_extension.py"

Or add to ~/.config/goose/config.yaml:
    extensions:
      nadirclaw-usage:
        name: NadirClaw Usage
        cmd: python
        args: ["/path/to/goose_usage_extension.py"]
        enabled: true
        type: stdio
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nadirclaw-usage")

# Model pricing ($ per million tokens) — Bedrock Mantle doesn't return pricing,
# so we estimate from known rates. Update when models/pricing change.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # model_id: (input_$/M, output_$/M)
    "openai/deepseek.v3.2":           (0.28,  0.42),
    "openai/deepseek.v3-v1:0":        (0.28,  0.42),
    "openai/moonshotai.kimi-k2.5":    (1.00,  3.00),
    "openai/minimax.minimax-m2.5":    (0.30,  1.20),
    "openai/minimax.minimax-m2.1":    (0.27,  0.95),
    "openai/zai.glm-5":              (1.00,  3.20),
    "openai/zai.glm-4.7":            (0.60,  2.20),
    "openai/zai.glm-4.7-flash":      (0.00,  0.00),  # free tier
    "openai/qwen.qwen3-coder-next":  (0.30,  1.20),
}

# Default pricing for unknown models
DEFAULT_PRICING = (0.50, 1.50)


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost from token counts using pricing table."""
    in_rate, out_rate = MODEL_PRICING.get(model, DEFAULT_PRICING)
    return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000


# NadirClaw logs location — Docker container mounts host path
NADIRCLAW_LOG = Path(os.environ.get(
    "NADIRCLAW_LOG_PATH",
    Path.home() / ".nadirclaw" / "logs" / "requests.jsonl",
))


def _parse_logs(since_hours: float = 24) -> list[dict]:
    """Parse NadirClaw request log entries since N hours ago."""
    if not NADIRCLAW_LOG.exists():
        return []
    cutoff = datetime.now() - timedelta(hours=since_hours)
    entries = []
    with open(NADIRCLAW_LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = d.get("timestamp", "")
            if ts:
                try:
                    entry_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                    if entry_time < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass
            entries.append(d)
    return entries


@mcp.tool()
def usage_summary(hours: float = 24) -> str:
    """Get token usage and cost summary for the last N hours (default: 24).

    Returns total tokens, cost, request count, and breakdown by model and tier.
    """
    entries = _parse_logs(hours)
    if not entries:
        return json.dumps({"error": f"No requests found in last {hours}h", "log_path": str(NADIRCLAW_LOG)})

    total_in = sum(e.get("prompt_tokens", 0) for e in entries)
    total_out = sum(e.get("completion_tokens", 0) for e in entries)
    total_cost = 0.0
    ok = sum(1 for e in entries if e.get("status") == "ok")
    err = sum(1 for e in entries if e.get("status") == "error")

    by_model: dict[str, dict] = defaultdict(lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0})
    by_tier: dict[str, dict] = defaultdict(lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0})

    for e in entries:
        model = e.get("selected_model", "unknown")
        tier = e.get("tier", "unknown")
        in_tok = e.get("prompt_tokens", 0)
        out_tok = e.get("completion_tokens", 0)
        # Use logged cost if available, otherwise estimate from pricing table
        cost = e.get("cost", 0) or _estimate_cost(model, in_tok, out_tok)
        total_cost += cost
        for bucket in (by_model[model], by_tier[tier]):
            bucket["requests"] += 1
            bucket["input_tokens"] += in_tok
            bucket["output_tokens"] += out_tok
            bucket["cost"] += cost

    return json.dumps({
        "period": f"last {hours}h",
        "total_requests": len(entries),
        "successful": ok,
        "failed": err,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "total_tokens": total_in + total_out,
        "total_cost_usd": round(total_cost, 4),
        "by_model": {k: {**v, "cost": round(v["cost"], 4)} for k, v in sorted(by_model.items(), key=lambda x: -x[1]["cost"])},
        "by_tier": {k: {**v, "cost": round(v["cost"], 4)} for k, v in sorted(by_tier.items(), key=lambda x: -x[1]["cost"])},
    }, indent=2)


@mcp.tool()
def budget_status() -> str:
    """Get current daily and monthly budget status from NadirClaw."""
    entries = _parse_logs(since_hours=720)  # ~30 days
    if not entries:
        return json.dumps({"error": "No log data found"})

    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    daily_cost = sum(
        (e.get("cost", 0) or _estimate_cost(e.get("selected_model", ""), e.get("prompt_tokens", 0), e.get("completion_tokens", 0)))
        for e in entries if e.get("timestamp", "").startswith(today)
    )
    monthly_cost = sum(
        (e.get("cost", 0) or _estimate_cost(e.get("selected_model", ""), e.get("prompt_tokens", 0), e.get("completion_tokens", 0)))
        for e in entries if e.get("timestamp", "").startswith(month)
    )

    daily_budget = float(os.environ.get("NADIRCLAW_DAILY_BUDGET", "5.00"))
    monthly_budget = float(os.environ.get("NADIRCLAW_MONTHLY_BUDGET", "80.00"))

    return json.dumps({
        "daily": {
            "spent": round(daily_cost, 4),
            "budget": daily_budget,
            "remaining": round(daily_budget - daily_cost, 4),
            "percent_used": round(daily_cost / daily_budget * 100, 1) if daily_budget else 0,
        },
        "monthly": {
            "spent": round(monthly_cost, 4),
            "budget": monthly_budget,
            "remaining": round(monthly_budget - monthly_cost, 4),
            "percent_used": round(monthly_cost / monthly_budget * 100, 1) if monthly_budget else 0,
        },
    }, indent=2)


@mcp.tool()
def recent_requests(count: int = 10) -> str:
    """Get the N most recent NadirClaw requests with model, tokens, cost, and status."""
    entries = _parse_logs(since_hours=24)
    recent = entries[-count:] if len(entries) > count else entries

    result = []
    for e in reversed(recent):
        result.append({
            "time": e.get("timestamp", "?"),
            "model": e.get("selected_model", "?"),
            "tier": e.get("tier", "?"),
            "input_tokens": e.get("prompt_tokens", 0),
            "output_tokens": e.get("completion_tokens", 0),
            "cost": round(e.get("cost", 0) or _estimate_cost(e.get("selected_model", ""), e.get("prompt_tokens", 0), e.get("completion_tokens", 0)), 6),
            "status": e.get("status", "?"),
            "latency_ms": e.get("total_latency_ms", 0),
            "prompt_preview": e.get("response_preview", "")[:60],
        })

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()
