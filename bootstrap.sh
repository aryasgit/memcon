#!/usr/bin/env bash
#
# Memcon bootstrap — clone the repo and run the installer in one shot.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh | bash
#
# Environment overrides:
#   MEMCON_DIR    Target directory (default: ~/memcon)
#   MEMCON_REPO   Repo URL        (default: https://github.com/aryasgit/memcon.git)
#   MEMCON_REF    Branch / tag    (default: main)
#   MEMCON_MODEL  Override the RAM-auto model pick (e.g. "qwen2.5-coder:14b")
#
set -euo pipefail

REPO="${MEMCON_REPO:-https://github.com/aryasgit/memcon.git}"
REF="${MEMCON_REF:-main}"
TARGET="${MEMCON_DIR:-$HOME/memcon}"

echo "╔══════════════════════════════════════╗"
echo "║          MEMCON — bootstrap          ║"
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
