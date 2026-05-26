#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate

# Start Qdrant
docker compose up -d
echo "✅ Qdrant at localhost:6333"

# Start watcher in background
python3 ingestion/watcher.py vault/ &
WATCHER_PID=$!
echo "✅ Vault watcher running (PID: $WATCHER_PID)"
echo $WATCHER_PID > .watcher.pid

echo "✅ API starting at http://localhost:8000"
echo "✅ Dashboard at http://localhost:8000/ui"
echo ""
echo "Press Ctrl+C to stop"

cleanup() {
  echo ""
  echo "Stopping memcon..."
  kill $WATCHER_PID 2>/dev/null
  rm -f .watcher.pid
  exit 0
}
trap cleanup INT

python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000