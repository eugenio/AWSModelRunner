FROM python:3.11-slim

WORKDIR /app

# Install nadirclaw with dashboard extra
RUN pip install --no-cache-dir "nadirclaw[dashboard]>=0.13" boto3>=1.35

# Fix NadirClaw bug: empty string content on assistant tool_call messages
# becomes None, which Bedrock/Mantle rejects. Preserve empty string instead.
RUN sed -i 's/content = text if text else message.content/content = text if text is not None else message.content/g' \
    /usr/local/lib/python3.11/site-packages/nadirclaw/server.py

# Fix NadirClaw bug: streaming responses return zero token counts (PR #33)
# 1. Add stream_options to request usage data in streaming chunks
RUN sed -i 's/call_kwargs: Dict\[str, Any\] = {"model": litellm_model, "messages": messages, "stream": True}/call_kwargs: Dict[str, Any] = {\n        "model": litellm_model,\n        "messages": messages,\n        "stream": True,\n        "stream_options": {"include_usage": True},\n    }/' \
    /usr/local/lib/python3.11/site-packages/nadirclaw/server.py
# 2. Extract usage before choice-is-None guard so usage-only final chunks aren't dropped
COPY config/patch-streaming-usage.py /tmp/
RUN python /tmp/patch-streaming-usage.py && rm /tmp/patch-streaming-usage.py

# Pre-download the sentence-transformers model so first startup is fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Place config where nadirclaw expects it (skips the interactive setup wizard)
RUN mkdir -p /root/.nadirclaw
COPY config/nadirclaw.env /root/.nadirclaw/.env

EXPOSE 4000

# Bind to 0.0.0.0 inside the container is fine — docker-compose
# restricts the host-side mapping to 127.0.0.1 only.
ENTRYPOINT ["nadirclaw", "serve", "--port", "4000"]
