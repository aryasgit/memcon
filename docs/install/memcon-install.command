#!/usr/bin/env bash
#
# Memcon — one-click installer (macOS / Linux)
#
# This file is meant to be double-clicked from Finder/Files. macOS opens a
# Terminal window for any .command file and runs it. You can also run it
# from the command line: bash memcon-install.command
#
# What it does:
#   1. Confirms with you before doing anything.
#   2. Downloads the canonical bootstrap script from GitHub.
#   3. Runs it (clones the repo, installs deps, starts Qdrant, ingests the
#      starter vault, registers MCP in Claude Desktop). A local LLM is optional.
#
# You can read the bootstrap script before running it:
#   https://github.com/aryasgit/memcon/blob/main/bootstrap.sh
#
# If macOS says "cannot be opened because it is from an unidentified
# developer" — that's Gatekeeper warning about an unsigned file. Right-click
# the file → Open → confirm. Or remove the quarantine flag once:
#   xattr -d com.apple.quarantine memcon-install.command
#
set -e

# Run inside the user's home, regardless of where the file was double-clicked
cd "$HOME"

clear
cat <<'BANNER'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                  M E M C O N   —   installer                 ║
║                                                              ║
║   Local memory layer for Claude — auto-query, auto-write.    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
BANNER
echo ""
echo "About to run:"
echo "  curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh | bash"
echo ""
echo "This will:"
echo "  1. Clone Memcon into ~/memcon"
echo "  2. Create a Python venv and install dependencies"
echo "  3. Start Qdrant in Docker"
echo "  4. Ingest the starter vault"
echo "  5. Register Memcon in Claude Desktop's config"
echo ""
echo "Lean by default — Claude does the reasoning, no local LLM needed. Want a"
echo "fully-offline local LLM too? Re-run with:"
echo "  MEMCON_WITH_OLLAMA=1 bash memcon-install.command"
echo ""
echo "Requires: git, docker, python3 (a local LLM is optional). The installer warns if any are missing."
echo ""
echo "Read the source first if you want:"
echo "  https://github.com/aryasgit/memcon/blob/main/bootstrap.sh"
echo "  https://github.com/aryasgit/memcon/blob/main/install.sh"
echo ""

# Defensive read — also handles the "double-clicked, no TTY" edge case
if [ -t 0 ]; then
  printf "Continue? [y/N] "
  read -r ans
else
  ans="y"  # if piped without a TTY, assume the user knew what they were doing
fi

case "$ans" in
  [yY]|[yY][eE][sS]) ;;
  *)
    echo ""
    echo "Aborted. Nothing was installed."
    [ -t 0 ] && { printf "Press Enter to close..."; read -r _; }
    exit 0
    ;;
esac

echo ""
echo "─── Running bootstrap ────────────────────────────────────────"
echo ""
curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh | bash

echo ""
echo "─── Done ─────────────────────────────────────────────────────"
echo ""
echo "Next steps:"
echo "  • Fully quit Claude Desktop (Cmd+Q) and reopen — memcon is wired in."
echo "  • Start the dashboard:  cd ~/memcon && ./start.sh"
echo "  • Then open:            http://localhost:8000/ui"
echo ""
[ -t 0 ] && { printf "Press Enter to close..."; read -r _; }
