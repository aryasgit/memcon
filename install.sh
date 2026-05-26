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
