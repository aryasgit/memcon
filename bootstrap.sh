#!/usr/bin/env bash
#
# Engram bootstrap — clone the repo and run the installer in one shot.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/aryasgit/engram/main/bootstrap.sh | bash
#
# Environment overrides:
#   ENGRAM_DIR    Target directory (default: ~/engram)
#   ENGRAM_REPO   Repo URL        (default: https://github.com/aryasgit/engram.git)
#   ENGRAM_REF    Branch / tag    (default: main)
#
set -euo pipefail

REPO="${ENGRAM_REPO:-https://github.com/aryasgit/engram.git}"
REF="${ENGRAM_REF:-main}"
TARGET="${ENGRAM_DIR:-$HOME/engram}"

echo "╔══════════════════════════════════════╗"
echo "║          ENGRAM — bootstrap          ║"
echo "╚══════════════════════════════════════╝"
echo "  repo: $REPO"
echo "  ref:  $REF"
echo "  dir:  $TARGET"
echo ""

for cmd in git docker python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ Required command not found: $cmd"
    echo "   Install it first and re-run."
    exit 1
  fi
done

if [ -d "$TARGET/.git" ]; then
  echo "↻  Existing checkout at $TARGET — pulling latest"
  git -C "$TARGET" fetch --quiet origin "$REF"
  git -C "$TARGET" checkout --quiet "$REF"
  git -C "$TARGET" pull --quiet --ff-only origin "$REF"
else
  echo "⇣  Cloning into $TARGET"
  git clone --quiet --branch "$REF" "$REPO" "$TARGET"
fi

cd "$TARGET"
chmod +x install.sh start.sh stop.sh bootstrap.sh 2>/dev/null || true

./install.sh

echo ""
echo "✅ Bootstrap complete."
echo "   cd $TARGET && ./start.sh"
