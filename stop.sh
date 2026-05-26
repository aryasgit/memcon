#!/bin/bash
cd "$(dirname "$0")"
echo "Stopping memcon..."

# Kill watcher
if [ -f .watcher.pid ]; then
  kill $(cat .watcher.pid) 2>/dev/null && echo "✅ Watcher stopped"
  rm -f .watcher.pid
fi

# Kill uvicorn
pkill -f "uvicorn api.main" 2>/dev/null && echo "✅ API stopped"

# Stop Qdrant
docker compose stop 2>/dev/null && echo "✅ Qdrant stopped"

echo "Done."