# BARQ Hive Mind — Startup

## 1. Mac terminal
cd ~/barq-hive
docker compose up -d

## 2. Cursor terminal Tab 1 (API)
cd ~/barq-hive && source .venv/bin/activate
uvicorn api.main:app --reload --port 8000

## 3. Cursor terminal Tab 2 (Watcher)
cd ~/barq-hive && source .venv/bin/activate
python ingestion/watcher.py vault/

## Shutdown
Ctrl+C on both Cursor tabs
docker stop barq-qdrant-1
