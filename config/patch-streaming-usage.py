"""Patch NadirClaw server.py for streaming fixes.

Applies three patches to _stream_litellm() and _stream_with_fallback():
1. Reorder usage extraction before choice-is-None guard (usage-only chunks)
2. Add token estimation fallback when upstream doesn't provide usage
3. Add context overflow auto-clamping with error logging

See: https://github.com/NadirRouter/NadirClaw/pull/33
"""

SERVER_PY = "/usr/local/lib/python3.11/site-packages/nadirclaw/server.py"


def apply_patch(content: str, name: str, old: str, new: str) -> str:
    if old not in content:
        print(f"SKIP: {name} — target not found (already applied or NadirClaw changed)")
        return content
    content = content.replace(old, new)
    print(f"OK: {name}")
    return content


with open(SERVER_PY, "r", encoding="utf-8") as f:
    content = f.read()

# Patch 1: Reorder usage extraction in _stream_litellm()
content = apply_patch(
    content,
    "usage-only chunk handling",
    """\
    async for chunk in response:
        choice = chunk.choices[0] if chunk.choices else None
        if choice is None:
            continue
        delta = choice.delta
        delta_dict: dict[str, Any] = {}
        if hasattr(delta, "role") and delta.role:
            delta_dict["role"] = delta.role
        if hasattr(delta, "content") and delta.content is not None:
            delta_dict["content"] = delta.content
        if hasattr(delta, "tool_calls") and delta.tool_calls:
            delta_dict["tool_calls"] = [
                tc.model_dump() if hasattr(tc, "model_dump") else tc
                for tc in delta.tool_calls
            ]

        usage = None
        if hasattr(chunk, "usage") and chunk.usage:
            usage = {
                "prompt_tokens": chunk.usage.prompt_tokens or 0,
                "completion_tokens": chunk.usage.completion_tokens or 0,
            }

        yield delta_dict, usage, choice.finish_reason""",
    """\
    async for chunk in response:
        usage = None
        if hasattr(chunk, "usage") and chunk.usage:
            usage = {
                "prompt_tokens": chunk.usage.prompt_tokens or 0,
                "completion_tokens": chunk.usage.completion_tokens or 0,
            }

        choice = chunk.choices[0] if chunk.choices else None
        if choice is None:
            # Usage-only final chunk (no choices) -- yield usage without content
            if usage:
                yield {}, usage, None
            continue

        delta = choice.delta
        delta_dict: dict[str, Any] = {}
        if hasattr(delta, "role") and delta.role:
            delta_dict["role"] = delta.role
        if hasattr(delta, "content") and delta.content is not None:
            delta_dict["content"] = delta.content
        if hasattr(delta, "tool_calls") and delta.tool_calls:
            delta_dict["tool_calls"] = [
                tc.model_dump() if hasattr(tc, "model_dump") else tc
                for tc in delta.tool_calls
            ]

        yield delta_dict, usage, choice.finish_reason""",
)

# Patch 2: Add token estimation + content accumulation in _stream_with_fallback()
content = apply_patch(
    content,
    "token estimation fallback",
    """\
        content_started = False
        accumulated_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        last_finish = None""",
    """\
        content_started = False
        accumulated_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        accumulated_content = []
        last_finish = None""",
)

# Patch 2b: Track content chunks for estimation
content = apply_patch(
    content,
    "content tracking for estimation",
    """\
                if not delta_dict:
                    continue

                # Add role on first content chunk""",
    """\
                if not delta_dict:
                    continue

                # Track content for token estimation fallback
                if "content" in delta_dict and delta_dict["content"]:
                    accumulated_content.append(delta_dict["content"])

                # Add role on first content chunk""",
)

# Patch 2c: Estimate tokens when upstream doesn't provide them
content = apply_patch(
    content,
    "token estimation before finish chunk",
    """\
            # Stream completed — send finish chunk with usage""",
    """\
            # Estimate tokens if upstream didn't provide them
            if accumulated_usage["prompt_tokens"] == 0 and accumulated_usage["completion_tokens"] == 0:
                prompt_text = " ".join(m.get("content", "") if isinstance(m.get("content"), str) else str(m.get("content", "")) for m in messages)
                completion_text = "".join(accumulated_content)
                # ~4 chars per token is a reasonable estimate for most models
                accumulated_usage["prompt_tokens"] = max(1, len(prompt_text) // 4)
                accumulated_usage["completion_tokens"] = max(1, len(completion_text) // 4)

            # Stream completed — send finish chunk with usage""",
)

# Patch 3: Context overflow clamping + error logging in fallback handler
content = apply_patch(
    content,
    "context overflow clamping",
    """\
            # Pre-content failure — can try fallback
            failed_models.append(model)
            last_error = e
            continue""",
    """\
            # Pre-content failure — check if it's a context overflow we can fix
            import re as _re
            err_str = str(e).lower()
            m = _re.search(r"passed (\\d+) input tokens.*requested (\\d+) output.*context length is only (\\d+)", err_str)
            if m:
                input_tok, req_out, ctx_limit = int(m.group(1)), int(m.group(2)), int(m.group(3))
                clamped = max(1024, ctx_limit - input_tok - 256)
                if clamped < req_out:
                    logger.warning("Context overflow on %s: %d input + %d output > %d ctx. Clamping max_tokens to %d for remaining models",
                                   model, input_tok, req_out, ctx_limit, clamped)
                    request.max_tokens = clamped
            logger.warning("Pre-content streaming error on %s: %s: %s", model, type(e).__name__, str(e)[:300])
            failed_models.append(model)
            last_error = e
            continue""",
)

# Patch 4: Raise max content length from 1M to 4M chars (~1M tokens)
content = apply_patch(
    content,
    "raise max content length to 4M",
    '_MAX_CONTENT_LENGTH = 1_000_000  # 1 MB total across all messages',
    '_MAX_CONTENT_LENGTH = int(os.environ.get("NADIRCLAW_MAX_CONTENT_LENGTH", 4_000_000))',
)

with open(SERVER_PY, "w", encoding="utf-8") as f:
    f.write(content)

print("All patches applied.")
