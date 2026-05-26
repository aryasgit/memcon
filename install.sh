#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║     ENGRAM — Installation Setup      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── CHECK DOCKER ─────────────────────────
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. Install from https://docker.com"
  exit 1
fi
echo "✅ Docker found"

# ── CHECK PYTHON ─────────────────────────
if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 not found."
  exit 1
fi
echo "✅ Python 3 found"

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

if [ "$TOTAL_RAM_GB" -ge 16 ]; then
  SELECTED_MODEL="qwen2.5-coder:7b"
  MODEL_REASON="16GB+ RAM → high quality coding model"
elif [ "$TOTAL_RAM_GB" -ge 8 ]; then
  SELECTED_MODEL="qwen2.5-coder:3b"
  MODEL_REASON="8-16GB RAM → balanced coding model"
else
  SELECTED_MODEL="llama3.2:1b"
  MODEL_REASON="<8GB RAM → lightweight model"
fi

echo "   Selected model: $SELECTED_MODEL ($MODEL_REASON)"
echo ""

# ── UPDATE CONFIG WITH SELECTED MODEL ────
if [ -f "engram.config.yaml" ]; then
  if [ "$OS" = "Darwin" ]; then
    sed -i '' "s|model: \".*\"|model: \"$SELECTED_MODEL\"|" engram.config.yaml
  else
    sed -i "s|model: \".*\"|model: \"$SELECTED_MODEL\"|" engram.config.yaml
  fi
  echo "✅ Config updated with model: $SELECTED_MODEL"
fi

# ── CREATE VENV ───────────────────────────
echo "📦 Creating Python environment..."
python3 -m venv .venv
source .venv/bin/activate

# ── INSTALL DEPS ──────────────────────────
echo "📦 Installing Python packages..."
python3 -m pip install -q fastapi uvicorn qdrant-client sentence-transformers \
  watchdog anthropic python-frontmatter python-dotenv \
  gitpython rich openai pyyaml

# ── PULL LLM MODEL ───────────────────────
echo "📦 Pulling LLM: $SELECTED_MODEL (may take a few minutes)..."
ollama pull "$SELECTED_MODEL"

# ── START QDRANT ──────────────────────────
echo "🐳 Starting Qdrant..."
docker compose up -d
sleep 3

# ── VAULT STRUCTURE ───────────────────────
echo "📁 Setting up vault..."
mkdir -p vault/{_templates,hardware,debugging,experiments,firmware,telemetry,decisions,gait}

# ── ENV FILE ─────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  .env created — edit if needed"
fi

# ── INITIAL INGEST ────────────────────────
echo "📥 Ingesting vault..."
python3 scripts/ingest_all.py

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        ✅ Setup complete!            ║"
echo "║  Model: $SELECTED_MODEL"
echo "║  Run:   ./start.sh                   ║"
echo "╚══════════════════════════════════════╝"
