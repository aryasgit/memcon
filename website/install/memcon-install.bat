@echo off
REM ============================================================
REM  Memcon — one-click installer (Windows)
REM
REM  Double-click this file from File Explorer. A console window
REM  opens and walks you through the install. You can also run it
REM  from a Command Prompt: memcon-install.bat
REM
REM  Read the source first if you want:
REM    https://github.com/aryasgit/memcon/blob/main/bootstrap.ps1
REM    https://github.com/aryasgit/memcon/blob/main/install.bat
REM
REM  Windows Defender SmartScreen may warn that the file is from
REM  an "unrecognized publisher" — that's because it isn't signed.
REM  Click "More info" → "Run anyway" if you trust the source.
REM ============================================================

title Memcon Installer
setlocal EnableDelayedExpansion

cls
echo.
echo  +==========================================================+
echo  ^|                                                          ^|
echo  ^|                M E M C O N   --   installer              ^|
echo  ^|                                                          ^|
echo  ^|   Local memory layer for Claude — auto-query, auto-write.^|
echo  ^|                                                          ^|
echo  +==========================================================+
echo.
echo  About to run:
echo    PowerShell -^> iwr https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.ps1 ^| iex
echo.
echo  This will:
echo    1. Clone Memcon into %USERPROFILE%\memcon
echo    2. Create a Python venv and install dependencies
echo    3. Pull the right Ollama model for your RAM
echo    4. Start Qdrant in Docker
echo    5. Ingest the starter vault
echo    6. Register Memcon in Claude Desktop's config
echo.
echo  Requires: git, docker (Desktop), python, ollama. The installer
echo  will warn if any are missing.
echo.
echo  Read the source first:
echo    https://github.com/aryasgit/memcon/blob/main/bootstrap.ps1
echo    https://github.com/aryasgit/memcon/blob/main/install.bat
echo.

set /p ANS=Continue? [y/N]
if /i not "%ANS%"=="y" if /i not "%ANS%"=="yes" (
  echo.
  echo  Aborted. Nothing was installed.
  echo.
  pause
  exit /b 0
)

echo.
echo  --- Running bootstrap ----------------------------------------
echo.

powershell -ExecutionPolicy Bypass -NoProfile -Command "iwr -useb https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.ps1 | iex"

echo.
echo  --- Done -----------------------------------------------------
echo.
echo  Next steps:
echo    * Fully quit Claude Desktop (right-click tray --^> Quit) and reopen.
echo    * Start the dashboard:  cd %USERPROFILE%\memcon ^&^& start.bat
echo    * Then open:            http://localhost:8000/ui
echo.
pause
