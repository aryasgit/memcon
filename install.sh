#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║     MEMCON — Installation Setup      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── CHECK DOCKER ─────────────────────────
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. Install from https://docker.com"
  exit 1
fi
# Installed is not enough — the daemon must be RUNNING, or `docker compose up`
# fails later (after we've already built the venv + pulled a multi-GB model).
if ! docker info &> /dev/null; then
  echo "❌ Docker is installed but not running."
  echo "   → Start Docker Desktop (or 'sudo systemctl start docker'), then re-run."
  exit 1
fi
echo "✅ Docker found and running"

# ── CHECK PYTHON (3.10+) ──────────────────
if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 not found. Install Python 3.10+ from https://python.org"
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  PYVER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "unknown")
  echo "❌ Python 3.10+ required (found ${PYVER}). Upgrade Python and re-run."
  exit 1
fi
echo "✅ Python $(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))') found"

# ── OPTIONAL: LOCAL LLM (Ollama) ──────────
# memcon works WITHOUT a local LLM — the assistant (Claude) does the reasoning,
# and the only ML memcon actually needs (embeddings) runs via sentence-
# transformers, NOT Ollama. Install a local LLM ONLY for fully-offline auto-
# structuring / self-contained answers.  Opt in with:
#     MEMCON_WITH_OLLAMA=1 ./install.sh
WITH_OLLAMA=0
SELECTED_MODEL=""
OS=$(uname -s)
if [ "${MEMCON_WITH_OLLAMA:-0}" = "1" ]; then
  if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama (MEMCON_WITH_OLLAMA=1)..."
    curl -fsSL https://ollama.com/install.sh | sh || echo "   ⚠️  Ollama install failed — continuing lean"
  fi
  if command -v ollama &> /dev/null; then
    WITH_OLLAMA=1
    echo "✅ Ollama found"
    if [ "$OS" = "Darwin" ]; then
      TOTAL_RAM_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    elif [ "$OS" = "Linux" ]; then
      TOTAL_RAM_GB=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 / 1024 ))
    else
      TOTAL_RAM_GB=7
    fi
    if   [ "$TOTAL_RAM_GB" -ge 64 ]; then SELECTED_MODEL="qwen2.5-coder:32b"
    elif [ "$TOTAL_RAM_GB" -ge 32 ]; then SELECTED_MODEL="qwen2.5-coder:14b"
    elif [ "$TOTAL_RAM_GB" -ge 16 ]; then SELECTED_MODEL="qwen2.5-coder:7b"
    elif [ "$TOTAL_RAM_GB" -ge 8 ];  then SELECTED_MODEL="qwen2.5-coder:3b"
    else                                  SELECTED_MODEL="llama3.2:1b"
    fi
    [ -n "$MEMCON_MODEL" ] && SELECTED_MODEL="$MEMCON_MODEL"
    echo "   RAM ${TOTAL_RAM_GB}GB → model: $SELECTED_MODEL"
    # Write the model into config (anchored so we never touch embedding_model).
    if [ -f "memcon.config.yaml" ]; then
      # Flip provider to ollama (out of the default "none"/Claude mode) + set model.
      if [ "$OS" = "Darwin" ]; then
        sed -i '' -e "s|^  provider: \".*\"|  provider: \"ollama\"|" -e "s|^  model: \".*\"|  model: \"$SELECTED_MODEL\"|" memcon.config.yaml
      else
        sed -i -e "s|^  provider: \".*\"|  provider: \"ollama\"|" -e "s|^  model: \".*\"|  model: \"$SELECTED_MODEL\"|" memcon.config.yaml
      fi
    fi
  else
    echo "⚠️  Ollama unavailable — continuing lean (Claude does the reasoning)"
  fi
else
  echo "ℹ️  Lean install — no local LLM. Claude does the reasoning; memcon handles"
  echo "   storage + search (embeddings run locally, no Ollama needed)."
  echo "   Want fully-offline LLM features? Re-run with:  MEMCON_WITH_OLLAMA=1 ./install.sh"
fi

# ── CREATE VENV ───────────────────────────
echo "📦 Creating Python environment..."
python3 -m venv .venv
source .venv/bin/activate

# ── INSTALL DEPS ──────────────────────────
echo "📦 Installing Python packages..."
python3 -m pip install -q --upgrade pip
if [ -f "requirements.txt" ]; then
  python3 -m pip install -q -r requirements.txt
else
  python3 -m pip install -q fastapi uvicorn qdrant-client sentence-transformers \
    watchdog anthropic python-frontmatter python-dotenv \
    gitpython rich openai pyyaml mcp
fi

# ── REGISTER MCP IN CLAUDE DESKTOP (EARLY — before anything fragile) ──
# This MUST run before the service steps below. Registration only needs the
# venv + server.py — never Docker/Qdrant/Ollama. Previously it ran LAST, so a
# hiccup in `docker compose`/ingest under `set -e` aborted the whole install
# before Claude was ever configured (the "downloads succeeded but no MCP" bug).
if [ -z "$MEMCON_SKIP_MCP" ]; then
  echo "🔌 Registering Memcon with Claude Desktop..."
  python3 scripts/register_mcp.py || echo "   (registration skipped — re-run later: .venv/bin/python3 scripts/register_mcp.py)"
fi

# ── VAULT STRUCTURE ───────────────────────
# Folders match the v3.1 note kinds (templates.FOLDER_FOR). The writer also
# creates these on demand, so this is just a friendly starting layout.
echo "📁 Setting up vault..."
mkdir -p vault/{_templates,debugging,decisions,experiments,concepts,references,meetings,breakthroughs,sessions}

# ── ENV FILE ─────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  .env created — edit if needed"
fi

# ── RUNTIME (non-fatal) ───────────────────
# Memcon is already registered with Claude above. The steps below bring up the
# runtime; if Docker isn't running or a download hiccups, DON'T abort — the user
# can finish later with ./start.sh. set +e makes these best-effort.
set +e

if [ "$WITH_OLLAMA" = "1" ] && [ -n "$SELECTED_MODEL" ]; then
  echo "📦 Pulling LLM: $SELECTED_MODEL (may take a few minutes)..."
  ollama pull "$SELECTED_MODEL" || echo "   ⚠️  model pull failed — run later: ollama pull $SELECTED_MODEL"
fi

echo "🐳 Starting Qdrant..."
docker compose up -d || echo "   ⚠️  Qdrant didn't start — is Docker running? run later: docker compose up -d"
sleep 3

echo "📥 Ingesting vault..."
python3 scripts/ingest_all.py || echo "   ⚠️  initial ingest skipped — run later: .venv/bin/python3 scripts/ingest_all.py"

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        ✅ Setup complete!            ║"
if [ "$WITH_OLLAMA" = "1" ]; then
  echo "║  Local LLM: $SELECTED_MODEL"
else
  echo "║  Mode: lean (no local LLM — Claude reasons)"
fi
echo "║  Run:   ./start.sh                   ║"
echo "╚══════════════════════════════════════╝"
