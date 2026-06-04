#!/bin/bash
cd "$(dirname "$0")"
echo "Stopping memcon..."

# Kill watcher — but only if the PID is actually a watcher. PIDs get recycled, so
# a stale .watcher.pid could otherwise kill an unrelated process.
if [ -f .watcher.pid ]; then
  WPID=$(cat .watcher.pid)
  if kill -0 "$WPID" 2>/dev/null && ps -p "$WPID" -o command= 2>/dev/null | grep -q "watcher.py"; then
    kill "$WPID" 2>/dev/null && echo "✅ Watcher stopped"
  else
    echo "ℹ️  .watcher.pid ($WPID) is stale or not a watcher — skipping kill"
  fi
  rm -f .watcher.pid
fi

# Kill uvicorn
pkill -f "uvicorn api.main" 2>/dev/null && echo "✅ API stopped"

# Stop Qdrant
docker compose stop 2>/dev/null && echo "✅ Qdrant stopped"

echo "Done."