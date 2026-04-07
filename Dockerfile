FROM python:3.11-slim

WORKDIR /app

# Install nadirclaw from local fork (includes all enhancements)
COPY nadirclaw-local/ /app/nadirclaw-src/
RUN pip install --no-cache-dir "/app/nadirclaw-src[dashboard]" boto3>=1.35 \
    && rm -rf /app/nadirclaw-src

# Pre-download the sentence-transformers model so first startup is fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Place config where nadirclaw expects it (skips the interactive setup wizard)
RUN mkdir -p /root/.nadirclaw
COPY config/nadirclaw.env /root/.nadirclaw/.env

EXPOSE 4000

# Bind to 0.0.0.0 inside the container is fine — docker-compose
# restricts the host-side mapping to 127.0.0.1 only.
ENTRYPOINT ["nadirclaw", "serve", "--port", "4000"]
