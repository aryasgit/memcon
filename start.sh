#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate

# Start Qdrant
docker compose up -d
echo "✅ Qdrant at localhost:6333"

# Start watcher in background — but never a DUPLICATE. Two watchers on one vault
# double every ingest and contend on Qdrant/SQLite; the second also orphans the
# first by overwriting .watcher.pid (so stop.sh can never kill it).
STARTED_WATCHER=0
if [ -f .watcher.pid ] && kill -0 "$(cat .watcher.pid)" 2>/dev/null \
   && ps -p "$(cat .watcher.pid)" -o command= 2>/dev/null | grep -q "watcher.py"; then
  WATCHER_PID=$(cat .watcher.pid)
  echo "ℹ️  Vault watcher already running (PID: $WATCHER_PID) — not starting another"
else
  python3 ingestion/watcher.py vault/ &
  WATCHER_PID=$!
  STARTED_WATCHER=1
  echo "$WATCHER_PID" > .watcher.pid
  echo "✅ Vault watcher running (PID: $WATCHER_PID)"
fi

echo "✅ API starting at http://localhost:8000"
echo "✅ Dashboard at http://localhost:8000/ui"
echo ""
echo "Press Ctrl+C to stop"

cleanup() {
  echo ""
  echo "Stopping memcon..."
  # Only kill the watcher if THIS script started it — don't take down a
  # pre-existing watcher we deliberately reused.
  if [ "$STARTED_WATCHER" = "1" ]; then
    kill "$WATCHER_PID" 2>/dev/null
    rm -f .watcher.pid
  fi
  exit 0
}
trap cleanup INT

# Refuse to start a second API on a port that's already serving (clear message
# instead of an opaque bind-failure stack trace).
if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "⚠️  Port 8000 is already in use — another memcon API may be running."
  echo "   Run ./stop.sh first if you want a fresh one."
  exit 1
fi

python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000