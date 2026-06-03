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

# ── CHECK OLLAMA ──────────────────────────
if ! command -v ollama &> /dev/null; then
  echo "📦 Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi
echo "✅ Ollama found"

# ── DETECT RAM AND PICK MODEL ─────────────
echo ""
echo "🔍 Detecting system RAM..."

OS=$(uname -s)
if [ "$OS" = "Darwin" ]; then
  TOTAL_RAM_BYTES=$(sysctl -n hw.memsize)
  TOTAL_RAM_GB=$(( TOTAL_RAM_BYTES / 1024 / 1024 / 1024 ))
elif [ "$OS" = "Linux" ]; then
  TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
  TOTAL_RAM_GB=$(( TOTAL_RAM_KB / 1024 / 1024 ))
else
  echo "⚠️  Cannot detect RAM on this OS. Defaulting to small model."
  TOTAL_RAM_GB=7
fi

echo "   Detected RAM: ${TOTAL_RAM_GB}GB"

if [ "$TOTAL_RAM_GB" -ge 64 ]; then
  SELECTED_MODEL="qwen2.5-coder:32b"
  MODEL_REASON="64GB+ RAM → flagship 32B coder, best memory tracking"
elif [ "$TOTAL_RAM_GB" -ge 32 ]; then
  SELECTED_MODEL="qwen2.5-coder:14b"
  MODEL_REASON="32-64GB RAM → 14B coder, strong technical reasoning"
elif [ "$TOTAL_RAM_GB" -ge 16 ]; then
  SELECTED_MODEL="qwen2.5-coder:7b"
  MODEL_REASON="16-32GB RAM → 7B coder, solid default"
elif [ "$TOTAL_RAM_GB" -ge 8 ]; then
  SELECTED_MODEL="qwen2.5-coder:3b"
  MODEL_REASON="8-16GB RAM → balanced 3B coder"
else
  SELECTED_MODEL="llama3.2:1b"
  MODEL_REASON="<8GB RAM → lightweight 1B model"
fi

# Allow override via MEMCON_MODEL env var (skips the auto tier entirely)
if [ -n "$MEMCON_MODEL" ]; then
  SELECTED_MODEL="$MEMCON_MODEL"
  MODEL_REASON="overridden via MEMCON_MODEL env var"
fi

echo "   Selected model: $SELECTED_MODEL ($MODEL_REASON)"
echo ""

# ── UPDATE CONFIG WITH SELECTED MODEL ────
# Anchor on "^  model:" so we only touch llm.model and NOT memory.embedding_model
# (the old unanchored pattern matched the substring inside `embedding_model: "..."`).
if [ -f "memcon.config.yaml" ]; then
  if [ "$OS" = "Darwin" ]; then
    sed -i '' "s|^  model: \".*\"|  model: \"$SELECTED_MODEL\"|" memcon.config.yaml
  else
    sed -i "s|^  model: \".*\"|  model: \"$SELECTED_MODEL\"|" memcon.config.yaml
  fi
  echo "✅ Config updated with model: $SELECTED_MODEL"
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

# ── PULL LLM MODEL ───────────────────────
echo "📦 Pulling LLM: $SELECTED_MODEL (may take a few minutes)..."
ollama pull "$SELECTED_MODEL"

# ── START QDRANT ──────────────────────────
echo "🐳 Starting Qdrant..."
docker compose up -d
sleep 3

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

# ── INITIAL INGEST ────────────────────────
echo "📥 Ingesting vault..."
python3 scripts/ingest_all.py

# ── REGISTER MCP IN CLAUDE DESKTOP ────────
# Idempotent — preserves any other MCP servers already configured.
# Set MEMCON_SKIP_MCP=1 to opt out.
if [ -z "$MEMCON_SKIP_MCP" ]; then
  echo ""
  python3 scripts/register_mcp.py || echo "   (MCP registration is optional — Memcon still works standalone)"
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        ✅ Setup complete!            ║"
echo "║  Model: $SELECTED_MODEL"
echo "║  Run:   ./start.sh                   ║"
echo "╚══════════════════════════════════════╝"
