FROM python:3.11-slim

WORKDIR /app

# Install nadirclaw with dashboard extra
RUN pip install --no-cache-dir "nadirclaw[dashboard]>=0.13" boto3>=1.35

# Fix NadirClaw bug: empty string content on assistant tool_call messages
# becomes None, which Bedrock/Mantle rejects. Preserve empty string instead.
RUN sed -i 's/content = text if text else message.content/content = text if text is not None else message.content/g' \
    /usr/local/lib/python3.11/site-packages/nadirclaw/server.py

# Fix NadirClaw streaming: token estimation, usage-only chunk handling, context overflow clamping (PR #33)
COPY config/patch-streaming-usage.py /tmp/
RUN python /tmp/patch-streaming-usage.py && rm /tmp/patch-streaming-usage.py

# Add model aliases for Goose VS Code extension which sends gpt-4o-mini (block/goose#8264)
RUN sed -i '/"o4-mini": "o4-mini",/a\    "gpt-4o-mini": "openai/deepseek.v3.2",\n    "gpt-4o": "openai/moonshotai.kimi-k2.5",' \
    /usr/local/lib/python3.11/site-packages/nadirclaw/routing.py

# Pre-download the sentence-transformers model so first startup is fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Place config where nadirclaw expects it (skips the interactive setup wizard)
RUN mkdir -p /root/.nadirclaw
COPY config/nadirclaw.env /root/.nadirclaw/.env

EXPOSE 4000

# Bind to 0.0.0.0 inside the container is fine — docker-compose
# restricts the host-side mapping to 127.0.0.1 only.
ENTRYPOINT ["nadirclaw", "serve", "--port", "4000"]
