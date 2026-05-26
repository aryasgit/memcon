@echo off
echo ╔══════════════════════════════════════╗
echo ║     MEMCON — Windows Setup           ║
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

IF %RAM_GB% GEQ 64 (
  set MODEL=qwen2.5-coder:32b
) ELSE IF %RAM_GB% GEQ 32 (
  set MODEL=qwen2.5-coder:14b
) ELSE IF %RAM_GB% GEQ 16 (
  set MODEL=qwen2.5-coder:7b
) ELSE IF %RAM_GB% GEQ 8 (
  set MODEL=qwen2.5-coder:3b
) ELSE (
  set MODEL=llama3.2:1b
)
echo Selected model: %MODEL%

REM Allow MEMCON_MODEL env var to override the auto-tier
IF DEFINED MEMCON_MODEL (
  set MODEL=%MEMCON_MODEL%
  echo Overridden via MEMCON_MODEL env var: %MODEL%
)

REM Create venv
python -m venv .venv
call .venv\Scripts\activate.bat

REM Install packages from requirements.txt (falls back to manual list)
IF EXIST requirements.txt (
  python -m pip install -q -r requirements.txt
) ELSE (
  python -m pip install -q fastapi uvicorn qdrant-client sentence-transformers ^
    watchdog anthropic python-frontmatter python-dotenv ^
    gitpython rich openai pyyaml mcp
)

REM Write selected model into memcon.config.yaml (anchored regex so we don't
REM clobber embedding_model)
python -c "import re,sys; p='memcon.config.yaml'; s=open(p).read(); s=re.sub(r'(?m)^  model: \".*\"', '  model: \"%MODEL%\"', s); open(p,'w').write(s)"
echo Config updated with model: %MODEL%

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
