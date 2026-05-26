@echo off
echo ╔══════════════════════════════════════╗
echo ║     ENGRAM — Windows Setup           ║
echo ╚══════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo ERROR: Python not found. Install from https://python.org
  pause
  exit /b 1
)
echo OK: Python found

REM Check Docker
docker --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo ERROR: Docker not found. Install Docker Desktop from https://docker.com
  pause
  exit /b 1
)
echo OK: Docker found

REM Detect RAM
for /f "skip=1" %%i in ('wmic computersystem get TotalPhysicalMemory') do (
  set /a RAM_GB=%%i/1073741824
  goto :ram_done
)
:ram_done
echo Detected RAM: %RAM_GB%GB

IF %RAM_GB% GEQ 16 (
  set MODEL=qwen2.5-coder:7b
) ELSE IF %RAM_GB% GEQ 8 (
  set MODEL=qwen2.5-coder:3b
) ELSE (
  set MODEL=llama3.2:1b
)
echo Selected model: %MODEL%

REM Create venv
python -m venv .venv
call .venv\Scripts\activate.bat

REM Install packages
python -m pip install -q fastapi uvicorn qdrant-client sentence-transformers ^
  watchdog anthropic python-frontmatter python-dotenv ^
  gitpython rich openai pyyaml

REM Pull model
ollama pull %MODEL%

REM Start Qdrant
docker compose up -d
timeout /t 3

REM Initial ingest
python scripts\ingest_all.py

echo.
echo Setup complete! Run start.bat to launch.
pause
