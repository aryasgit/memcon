@echo off
setlocal EnableDelayedExpansion
echo ╔══════════════════════════════════════╗
echo ║     MEMCON — Windows Setup           ║
echo ╚══════════════════════════════════════╝
echo.

REM ── CHECK PYTHON ─────────────────────────
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo ERROR: Python not found. Install from https://python.org
  pause
  exit /b 1
)
echo OK: Python found

REM ── CHECK DOCKER ─────────────────────────
docker --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo ERROR: Docker not found. Install Docker Desktop from https://docker.com
  pause
  exit /b 1
)
echo OK: Docker found

REM ── OPTIONAL: LOCAL LLM (Ollama) ─────────
REM memcon works WITHOUT a local LLM - the assistant (Claude) does the reasoning.
REM Opt in for fully-offline LLM features: set MEMCON_WITH_OLLAMA=1 before running.
set WITH_OLLAMA=0
IF "%MEMCON_WITH_OLLAMA%"=="1" (
  ollama --version >nul 2>&1
  IF !ERRORLEVEL! EQU 0 (
    set WITH_OLLAMA=1
    echo OK: Ollama found
  ) ELSE (
    echo WARNING: Ollama not found - continuing lean. Get it at https://ollama.com/download/windows
  )
) ELSE (
  echo Lean install - no local LLM. Re-run with: set MEMCON_WITH_OLLAMA=1 for offline LLM features.
)

REM ── DETECT RAM ───────────────────────────
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

IF DEFINED MEMCON_MODEL (
  set MODEL=%MEMCON_MODEL%
  echo Overridden via MEMCON_MODEL env var: %MODEL%
)

REM ── CREATE VENV ──────────────────────────
echo Creating Python environment...
python -m venv .venv
call .venv\Scripts\activate.bat

REM ── INSTALL DEPS ─────────────────────────
echo Installing Python packages...
python -m pip install -q --upgrade pip
IF EXIST requirements.txt (
  python -m pip install -q -r requirements.txt
) ELSE (
  python -m pip install -q fastapi uvicorn qdrant-client sentence-transformers ^
    watchdog anthropic python-frontmatter python-dotenv ^
    gitpython rich openai pyyaml mcp
)

REM ── WRITE MODEL INTO CONFIG (only with a local LLM) ─
IF "%WITH_OLLAMA%"=="1" (
  python -c "import re; p='memcon.config.yaml'; s=open(p).read(); s=re.sub(r'(?m)^  model: \".*\"', '  model: \"%MODEL%\"', s); open(p,'w').write(s)"
  echo Config updated with model: %MODEL%
)

REM ── PULL LLM (only with a local LLM) ─────
IF "%WITH_OLLAMA%"=="1" (
  echo Pulling LLM: %MODEL% (may take a few minutes)...
  ollama pull %MODEL%
)

REM ── START QDRANT ─────────────────────────
echo Starting Qdrant...
docker compose up -d
timeout /t 3 >nul

REM ── VAULT STRUCTURE ──────────────────────
echo Setting up vault...
IF NOT EXIST vault\_templates    mkdir vault\_templates
IF NOT EXIST vault\debugging     mkdir vault\debugging
IF NOT EXIST vault\decisions     mkdir vault\decisions
IF NOT EXIST vault\experiments   mkdir vault\experiments
IF NOT EXIST vault\concepts      mkdir vault\concepts
IF NOT EXIST vault\references    mkdir vault\references
IF NOT EXIST vault\meetings      mkdir vault\meetings
IF NOT EXIST vault\breakthroughs mkdir vault\breakthroughs
IF NOT EXIST vault\sessions      mkdir vault\sessions

REM ── INGEST VAULT ─────────────────────────
echo Ingesting vault...
python scripts\ingest_all.py

REM ── REGISTER MCP IN CLAUDE DESKTOP ───────
IF NOT DEFINED MEMCON_SKIP_MCP (
  echo.
  python scripts\register_mcp.py
)

echo.
echo ╔══════════════════════════════════════╗
echo ║        Setup complete!               ║
IF "%WITH_OLLAMA%"=="1" (
  echo ║  Local LLM: %MODEL%
) ELSE (
  echo ║  Mode: lean ^(no local LLM - Claude reasons^)
)
echo ║  Run:   start.bat                    ║
echo ╚══════════════════════════════════════╝
pause
