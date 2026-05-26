@echo off
call .venv\Scripts\activate.bat
docker compose up -d
echo Qdrant started
start /b python scripts\watcher_win.py vault\
echo Watcher started
echo Dashboard: http://localhost:8000/ui
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
