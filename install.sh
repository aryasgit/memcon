#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║     ENGRAM — Installation Setup      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. Install from https://docker.com"
  exit 1
fi
echo "✅ Docker found"

# Check Python3
if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 not found."
  exit 1
fi
echo "✅ Python 3 found"

# Check Ollama
if ! command -v ollama &> /dev/null; then
  echo "📦 Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi
echo "✅ Ollama found"

# Create venv
echo "📦 Creating Python environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "📦 Installing Python packages..."
python3 -m pip install -q fastapi uvicorn qdrant-client sentence-transformers \
  watchdog anthropic python-frontmatter python-dotenv \
  gitpython rich openai pyyaml

# Pull LLM model from config
MODEL=$(python3 -c "import yaml; print(yaml.safe_load(open('engram.config.yaml'))['llm']['model'])")
echo "📦 Pulling LLM: $MODEL (may take a few minutes)..."
ollama pull $MODEL

# Start Qdrant
echo "🐳 Starting Qdrant..."
docker compose up -d
sleep 3

# Create vault structure from config
echo "📁 Setting up vault..."
mkdir -p vault/_templates
python3 -c "
import yaml
c = yaml.safe_load(open('engram.config.yaml'))
import os
for d in c.get('vault',{}).get('skip_dirs',[]):
    os.makedirs(f'vault/{d}', exist_ok=True)
"

# Setup .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  .env created from template — edit if needed"
fi

# Initial ingest
echo "📥 Ingesting vault..."
python3 scripts/ingest_all.py

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        ✅ Setup complete!            ║"
echo "║   Run: ./start.sh to launch          ║"
echo "╚══════════════════════════════════════╝"