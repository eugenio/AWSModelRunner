FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install nadirclaw from PyPI + dependencies (cached between builds)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system "nadirclaw[dashboard]>=0.13" boto3>=1.35

# Pre-download the sentence-transformers model (cached between builds)
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    && cp -r /root/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2 \
       /root/.cache/torch/ 2>/dev/null || true

# Apply streaming usage + context overflow patches
COPY config/patch-streaming-usage.py /tmp/patch-streaming-usage.py
RUN python /tmp/patch-streaming-usage.py && rm /tmp/patch-streaming-usage.py

# Place config where nadirclaw expects it (skips the interactive setup wizard)
RUN mkdir -p /root/.nadirclaw
COPY config/nadirclaw.env /root/.nadirclaw/.env

EXPOSE 4000

# Bind to 0.0.0.0 inside the container is fine — docker-compose
# restricts the host-side mapping to 127.0.0.1 only.
ENTRYPOINT ["nadirclaw", "serve", "--port", "4000"]
