FROM python:3.13-slim

WORKDIR /app

# System deps for sentence-transformers / torch on Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Project code
COPY . /app

ENV PYTHONPATH=/app
EXPOSE 8000

# Liveness: the API must answer /health, else the orchestrator can restart it
# (paired with `restart: unless-stopped` in the compose files).
HEALTHCHECK --interval=15s --timeout=3s --start-period=40s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Default: API + vault watcher.
# Watcher writes to vault/ which is bind-mounted; API serves on 8000.
# 0.0.0.0 is correct INSIDE the container; control exposure at run time with a
# localhost port map:  docker run -p 127.0.0.1:8000:8000 ...
CMD ["bash", "-c", "python3 ingestion/watcher.py vault/ & exec uvicorn api.main:app --host 0.0.0.0 --port 8000"]
