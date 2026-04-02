"""Patch NadirClaw server.py to fix streaming usage-only chunks being dropped.

Moves usage extraction before the `choice is None` guard in _stream_litellm()
so that final chunks with usage data but empty choices are yielded instead of
silently discarded. See: https://github.com/NadirRouter/NadirClaw/pull/33
"""

SERVER_PY = "/usr/local/lib/python3.11/site-packages/nadirclaw/server.py"

OLD = """\
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

        yield delta_dict, usage, choice.finish_reason"""

NEW = """\
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

        yield delta_dict, usage, choice.finish_reason"""

with open(SERVER_PY, "r", encoding="utf-8") as f:
    content = f.read()

if OLD not in content:
    raise RuntimeError("Patch target not found — NadirClaw may have changed. Check PR #33.")

content = content.replace(OLD, NEW)

with open(SERVER_PY, "w", encoding="utf-8") as f:
    f.write(content)

print("OK: streaming usage patch applied")
