#!/usr/bin/env bash
#
# Install a git post-commit hook that ingests every new commit into Memcon.
#
# Usage:
#   ./scripts/install_git_hook.sh                 # in any git repo
#   ./scripts/install_git_hook.sh /path/to/repo   # install into another repo
#
# Idempotent. If a post-commit hook already exists, backs it up first.
#
set -euo pipefail

MEMCON_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MEMCON_PY="$MEMCON_ROOT/.venv/bin/python3"
if [ ! -x "$MEMCON_PY" ]; then
    echo "❌ Memcon venv not found at $MEMCON_PY"
    echo "   Run ./install.sh in the Memcon directory first."
    exit 1
fi

TARGET_REPO="${1:-$(pwd)}"
TARGET_REPO="$(cd "$TARGET_REPO" && pwd)"
HOOK_DIR="$TARGET_REPO/.git/hooks"

if [ ! -d "$HOOK_DIR" ]; then
    echo "❌ Not a git repo: $TARGET_REPO  (no .git/hooks/)"
    exit 1
fi

HOOK="$HOOK_DIR/post-commit"

if [ -f "$HOOK" ] && ! grep -q "memcon-ingest" "$HOOK" 2>/dev/null; then
    backup="$HOOK.bak-$(date +%s)"
    mv "$HOOK" "$backup"
    echo "📦 Backed up existing post-commit hook → $backup"
fi

cat > "$HOOK" <<EOF
#!/usr/bin/env bash
# memcon-ingest — auto-ingest each commit into Memcon
# Installed by Memcon's scripts/install_git_hook.sh
"$MEMCON_PY" "$MEMCON_ROOT/scripts/ingest_latest_commit.py" "$TARGET_REPO" >/dev/null 2>&1 &
exit 0
EOF
chmod +x "$HOOK"

echo "✅ Git post-commit hook installed:"
echo "   $HOOK"
echo "   → each new commit auto-ingests into Memcon."
echo ""
echo "   Remove later with:  rm $HOOK"
