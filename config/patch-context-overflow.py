"""Patch NadirClaw server.py to add context overflow routing.

Injects a check right after content-length validation: if the total
content exceeds NADIRCLAW_CONTEXT_OVERFLOW_THRESHOLD chars (~4 chars/token),
force-route to NADIRCLAW_CONTEXT_OVERFLOW_MODEL instead of running
the normal tier classifier.
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

# Inject overflow routing right after the content-length validation,
# before start_time. If content is large enough, skip the entire
# tier classifier and go straight to the overflow model.
content = apply_patch(
    content,
    "context overflow routing (server.py)",
    """\
    start_time = time.time()
    request_id = str(uuid.uuid4())""",
    """\
    # --- Context overflow routing ---
    _overflow_model = os.environ.get("NADIRCLAW_CONTEXT_OVERFLOW_MODEL", "")
    _overflow_char_threshold = int(os.environ.get("NADIRCLAW_CONTEXT_OVERFLOW_THRESHOLD", "256000")) * 4
    if _overflow_model and total_content_len > _overflow_char_threshold:
        import logging as _log
        _log.getLogger("nadirclaw").info(
            "Context overflow: %d chars > %d threshold → routing to %s",
            total_content_len, _overflow_char_threshold, _overflow_model,
        )
        start_time = time.time()
        request_id = str(uuid.uuid4())
        try:
            from nadirclaw.routing import resolve_alias
            _overflow_resolved = resolve_alias(_overflow_model) or _overflow_model
            analysis_info = {
                "strategy": "context_overflow",
                "selected_model": _overflow_resolved,
                "tier": "overflow",
                "confidence": 1.0,
                "complexity_score": 0,
                "estimated_chars": total_content_len,
            }
            provider = None
            response_data, selected_model, fallback_info = await _call_with_fallback(
                _overflow_resolved, request, provider, analysis_info,
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            user_msgs = [m.text_content() for m in request.messages if m.role == "user"]
            prompt_text = user_msgs[-1][:120] if user_msgs else ""
            _log.getLogger("nadirclaw").info(
                "%s  %s  model=%-40s conf=%.3f score=%.2f lat=%dms total=%dms  \\"%s\\"",
                request_id[:8], "overflow", selected_model, 1.0, 0.0, elapsed_ms, elapsed_ms, prompt_text,
            )
            return response_data
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            _log.getLogger("nadirclaw").error("Context overflow failed: %s", e)
            raise HTTPException(status_code=500, detail=f"An internal error occurred. Request ID: {request_id}")

    start_time = time.time()
    request_id = str(uuid.uuid4())""",
)

with open(SERVER_PY, "w", encoding="utf-8") as f:
    f.write(content)

print("Context overflow patch applied.")
