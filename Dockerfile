FROM python:3.11-slim

WORKDIR /app

# Install nadirclaw with dashboard extra
RUN pip install --no-cache-dir "nadirclaw[dashboard]>=0.13" boto3>=1.35

# Pre-download the sentence-transformers model so first startup is fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Place config where nadirclaw expects it (skips the interactive setup wizard)
RUN mkdir -p /root/.nadirclaw
COPY config/nadirclaw.env /root/.nadirclaw/.env

EXPOSE 4000

# Bind to 0.0.0.0 inside the container is fine — docker-compose
# restricts the host-side mapping to 127.0.0.1 only.
ENTRYPOINT ["nadirclaw", "serve", "--port", "4000"]
