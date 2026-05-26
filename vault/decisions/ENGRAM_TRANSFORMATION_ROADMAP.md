# ENGRAM — Full Transformation Roadmap
> From bark-hive personal tool → open source engineering memory system
> Author: Aryaman Gupta | Target: Ship today

---

## Vision Statement

**Engram** is a local-first, free, persistent memory system for engineers working on complex long-running projects. It turns your notes, code commits, debugging sessions, and experiments into a searchable, queryable knowledge base — powered entirely by open source tools running on your own machine.

**Tagline:** *Your project never forgets.*

---

## Current State vs Target State

| Dimension | Now (bark-hive) | Target (engram) |
|---|---|---|
| Name | bark-hive | engram |
| Domain | Robotics only | Any engineering project |
| Setup | Manual, 20+ steps | `./install.sh` — one command |
| UI | curl commands | Web dashboard at localhost:3000 |
| Config | Hardcoded paths | `engram.config.yaml` |
| Docs | Internal reference | Full README + docs site |
| Tests | None | Basic smoke tests |
| Distribution | Private GitHub | Public MIT licensed |
| Monetisation | None | SaaS + extension (Phase 3) |

---

## Master Checklist — Ship Today

### PHASE 0 — Rename & Rebrand
- [ ] Rename project folder from `bark-hive` to `engram`
- [ ] Create new GitHub repo: `github.com/aryasgit/engram`
- [ ] Update all internal references from bark-hive → engram
- [ ] Write tagline and one-paragraph description

### PHASE 1 — Generalisation (Core)
- [ ] Remove all hardcoded `/Users/barq/` paths
- [ ] Create `engram.config.yaml` — single config file
- [ ] Update all Python modules to read from config
- [ ] Make subsystems and memory types configurable
- [ ] Make vault path configurable
- [ ] Make LLM model configurable
- [ ] Add domain templates (robotics, game-dev, research, software)

### PHASE 2 — One-Command Install
- [ ] Write `install.sh` (Docker check, venv, pip, ollama pull, vault init)
- [ ] Write `start.sh` (starts Qdrant + API + watcher)
- [ ] Write `stop.sh`
- [ ] Test on clean environment
- [ ] Add Windows/Linux notes to README

### PHASE 3 — Web UI Dashboard
- [ ] Create `ui/index.html` — single file, no build step
- [ ] Search bar → POST /ask
- [ ] Recent ingested notes feed
- [ ] Subsystem/tag filter
- [ ] Ingestion status indicator
- [ ] Memory type breakdown (episodic/semantic/procedural/causal)
- [ ] Serve UI from FastAPI at localhost:8000/ui

### PHASE 4 — API Hardening
- [ ] Add proper error handling to all endpoints
- [ ] Add /stats endpoint (collection size, last ingestion, model info)
- [ ] Add /collections endpoint (list all projects)
- [ ] Add /config endpoint (return current config)
- [ ] Add CORS headers
- [ ] Write basic smoke tests

### PHASE 5 — Documentation
- [ ] README.md (what it is, demo GIF, quickstart, config reference)
- [ ] CONTRIBUTING.md
- [ ] Domain template docs (how to set up for your project type)
- [ ] API reference
- [ ] Architecture diagram

### PHASE 6 — Open Source Launch
- [ ] Final GitHub push with clean commit history
- [ ] Add MIT LICENSE file
- [ ] Post on Reddit r/selfhosted
- [ ] Post on Reddit r/robotics (with BARQ origin story)
- [ ] Post on Hacker News (Show HN)
- [ ] Add to awesome-selfhosted list

### PHASE 7 — Monetisation (Post-Launch)
- [ ] VS Code / Cursor extension (queries /ask inline)
- [ ] Hosted cloud version (managed Qdrant + web UI)
- [ ] Team shared memory (multi-user Qdrant collections)
- [ ] Apply to GitHub Education showcase
- [ ] Landing page at engram.dev

---

## PHASE 0 — Rename & Rebrand

### Commands
```bash
# Rename local folder
mv ~/BARQ/hive ~/BARQ/engram
cd ~/BARQ/engram

# Update .env
sed -i '' 's/bark-hive/engram/g' .env

# Update any internal references
grep -r "bark-hive\|barq-hive\|barq_memory" . \
  --include="*.py" --include="*.yaml" --include="*.md" -l
```

### GitHub
- Create new repo: `github.com/aryasgit/engram` (public)
- Archive `bark-hive` private repo
- Update remote:
```bash
git remote set-url origin https://github.com/aryasgit/engram.git
```

---

## PHASE 1 — Generalisation

### engram.config.yaml
```yaml
# engram.config.yaml — edit this for your project
project:
  name: "BARQ"
  description: "Autonomous quadruped robot"
  domain: "robotics"  # robotics | gamedev | research | software | hardware

vault:
  path: "./vault"
  skip_dirs: ["_templates"]
  chunk_size: 400
  min_chunk_length: 30

memory:
  collection: "engram_memory"
  embedding_model: "all-MiniLM-L6-v2"
  vector_dim: 384

llm:
  provider: "ollama"        # ollama | anthropic | openrouter
  model: "qwen2.5-coder:7b"
  base_url: "http://localhost:11434/v1"
  max_tokens: 1024

qdrant:
  host: "localhost"
  port: 6333

api:
  host: "0.0.0.0"
  port: 8000

subsystems:
  - servo
  - imu
  - gait
  - power
  - vision
  - voice
  - slam
  - ik
  - version_control

memory_types:
  - episodic
  - semantic
  - procedural
  - causal
```

### config.py (new file — root of project)
```python
# config.py
import yaml
from pathlib import Path

_config = None

def get_config() -> dict:
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "engram.config.yaml"
        with open(config_path) as f:
            _config = yaml.safe_load(f)
    return _config

def cfg(*keys):
    """Dot-path accessor: cfg('llm', 'model') → 'qwen2.5-coder:7b'"""
    result = get_config()
    for key in keys:
        result = result[key]
    return result
```

### Updated qdrant_store.py (reads from config)
```python
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg

client = QdrantClient(host=cfg('qdrant', 'host'), port=cfg('qdrant', 'port'))
COLLECTION = cfg('memory', 'collection')
DIM = cfg('memory', 'vector_dim')

def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )
        print(f"[qdrant] Created collection: {COLLECTION}")

def upsert_chunks(chunks: list[dict], vectors: list[list[float]]) -> int:
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])),
            vector=v,
            payload=c,
        )
        for c, v in zip(chunks, vectors)
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)

def search(query_vec: list[float], top_k: int = 5, subsystem: str = None) -> list[dict]:
    query_filter = None
    if subsystem:
        query_filter = Filter(must=[
            FieldCondition(key="subsystem", match=MatchValue(value=subsystem))
        ])
    results = client.query_points(
        collection_name=COLLECTION,
        query=query_vec,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    ).points
    return [{"score": round(r.score, 4), **r.payload} for r in results]

def get_stats() -> dict:
    info = client.get_collection(COLLECTION)
    return {
        "total_chunks": info.points_count,
        "collection": COLLECTION,
        "vector_dim": DIM,
    }
```

### Updated embedder.py (reads from config)
```python
from sentence_transformers import SentenceTransformer
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg

_model = None

def get_model():
    global _model
    if _model is None:
        model_name = cfg('memory', 'embedding_model')
        print(f"[embedder] Loading {model_name}...")
        _model = SentenceTransformer(model_name)
        print("[embedder] Model ready.")
    return _model

def embed(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, batch_size=32, show_progress_bar=False).tolist()
```

---

## PHASE 2 — One-Command Install

### install.sh
```bash
#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║     ENGRAM — Installation Setup      ║"
echo "╚══════════════════════════════════════╝"

# Check Docker
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. Install from https://docker.com"
  exit 1
fi
echo "✅ Docker found"

# Check Python
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
pip install -q fastapi uvicorn qdrant-client sentence-transformers \
  watchdog anthropic python-frontmatter python-dotenv \
  gitpython rich openai pyyaml

# Pull LLM model
MODEL=$(python3 -c "import yaml; print(yaml.safe_load(open('engram.config.yaml'))['llm']['model'])")
echo "📦 Pulling LLM model: $MODEL (this may take a few minutes)..."
ollama pull $MODEL

# Start Qdrant
echo "🐳 Starting Qdrant..."
docker compose up -d

# Create vault structure
echo "📁 Creating vault structure..."
mkdir -p vault/{_templates,hardware,gait,debugging,experiments,firmware,telemetry,decisions}

# Copy .env template if not exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  Edit .env with your settings (optional — system works without API keys)"
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     ✅ Installation complete!        ║"
echo "║     Run: ./start.sh                  ║"
echo "╚══════════════════════════════════════╝"
```

### start.sh
```bash
#!/bin/bash
source .venv/bin/activate

# Start Qdrant
docker compose up -d
echo "✅ Qdrant running at localhost:6333"

# Start watcher in background
python ingestion/watcher.py vault/ &
WATCHER_PID=$!
echo "✅ Vault watcher running (PID: $WATCHER_PID)"

# Start API
echo "✅ API starting at localhost:8000"
echo "✅ Dashboard at localhost:8000/ui"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $WATCHER_PID; docker stop \$(docker ps -q --filter name=qdrant); exit" INT
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### stop.sh
```bash
#!/bin/bash
echo "Stopping engram..."
pkill -f "watcher.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
docker stop $(docker ps -q --filter name=qdrant) 2>/dev/null || true
echo "✅ All services stopped."
```

---

## PHASE 3 — Web UI Dashboard

### api/ui.html (served by FastAPI at /ui)
Single file, no build step, no npm. Pure HTML + JS.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Engram — Engineering Memory</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'IBM Plex Mono', monospace;
      background: #0a0a0a;
      color: #e0e0e0;
      min-height: 100vh;
      padding: 2rem;
    }
    h1 { font-size: 1.4rem; color: #00ff88; letter-spacing: 0.1em; }
    .subtitle { color: #555; font-size: 0.8rem; margin-bottom: 2rem; }
    .search-bar {
      display: flex; gap: 0.5rem; margin-bottom: 1.5rem;
    }
    input {
      flex: 1; background: #111; border: 1px solid #333;
      color: #e0e0e0; padding: 0.75rem 1rem; font-family: inherit;
      font-size: 0.9rem; outline: none;
    }
    input:focus { border-color: #00ff88; }
    button {
      background: #00ff88; color: #000; border: none;
      padding: 0.75rem 1.5rem; font-family: inherit;
      font-weight: bold; cursor: pointer; font-size: 0.9rem;
    }
    button:hover { background: #00cc6a; }
    .filters { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
    .chip {
      background: #111; border: 1px solid #333; color: #888;
      padding: 0.3rem 0.75rem; font-size: 0.75rem; cursor: pointer;
      font-family: inherit;
    }
    .chip.active { border-color: #00ff88; color: #00ff88; }
    .answer-box {
      background: #111; border-left: 3px solid #00ff88;
      padding: 1rem; margin-bottom: 1.5rem; display: none;
    }
    .answer-box .label { color: #555; font-size: 0.75rem; margin-bottom: 0.5rem; }
    .answer-box .text { line-height: 1.6; font-size: 0.9rem; }
    .sources { color: #555; font-size: 0.75rem; margin-top: 0.5rem; }
    .results { display: flex; flex-direction: column; gap: 0.75rem; }
    .chunk {
      background: #111; border: 1px solid #222;
      padding: 1rem; transition: border-color 0.2s;
    }
    .chunk:hover { border-color: #333; }
    .chunk-meta {
      display: flex; gap: 1rem; margin-bottom: 0.5rem;
      font-size: 0.7rem; color: #555;
    }
    .chunk-meta .score { color: #00ff88; }
    .chunk-meta .subsystem { color: #888; }
    .chunk-text { font-size: 0.85rem; line-height: 1.5; color: #ccc; }
    .stats { 
      position: fixed; top: 2rem; right: 2rem;
      font-size: 0.75rem; color: #333; text-align: right;
    }
    .stats span { color: #555; }
    .loading { color: #555; font-size: 0.85rem; }
    .mode-toggle { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
    .mode-btn { background: #111; border: 1px solid #333; color: #555;
      padding: 0.4rem 1rem; font-family: inherit; font-size: 0.8rem; cursor: pointer; }
    .mode-btn.active { border-color: #00ff88; color: #00ff88; }
  </style>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap" rel="stylesheet">
</head>
<body>
  <div class="stats">
    <div>engram</div>
    <span id="stats-text">loading...</span>
  </div>

  <h1>// ENGRAM</h1>
  <p class="subtitle">engineering memory system — ask anything about your project</p>

  <div class="mode-toggle">
    <button class="mode-btn active" onclick="setMode('ask')" id="btn-ask">ASK</button>
    <button class="mode-btn" onclick="setMode('search')" id="btn-search">SEARCH</button>
  </div>

  <div class="search-bar">
    <input id="query" type="text" placeholder="What caused the servo to overheat?" 
      onkeydown="if(event.key==='Enter') submit()"/>
    <button onclick="submit()">→</button>
  </div>

  <div class="filters" id="filters"></div>

  <div class="answer-box" id="answer-box">
    <div class="label">// ANSWER</div>
    <div class="text" id="answer-text"></div>
    <div class="sources" id="answer-sources"></div>
  </div>

  <div class="results" id="results"></div>

  <script>
    let mode = 'ask';
    let activeSubsystem = null;

    async function loadStats() {
      try {
        const r = await fetch('/stats');
        const d = await r.json();
        document.getElementById('stats-text').textContent = 
          `${d.total_chunks} chunks · ${d.collection}`;
      } catch { 
        document.getElementById('stats-text').textContent = 'offline'; 
      }
    }

    async function loadFilters() {
      try {
        const r = await fetch('/config');
        const d = await r.json();
        const f = document.getElementById('filters');
        f.innerHTML = '<span style="color:#555;font-size:0.75rem;margin-right:0.5rem">filter:</span>';
        d.subsystems.forEach(s => {
          const c = document.createElement('button');
          c.className = 'chip';
          c.textContent = s;
          c.onclick = () => toggleFilter(s, c);
          f.appendChild(c);
        });
      } catch {}
    }

    function toggleFilter(subsystem, el) {
      if (activeSubsystem === subsystem) {
        activeSubsystem = null;
        el.classList.remove('active');
      } else {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        activeSubsystem = subsystem;
        el.classList.add('active');
      }
    }

    function setMode(m) {
      mode = m;
      document.getElementById('btn-ask').classList.toggle('active', m === 'ask');
      document.getElementById('btn-search').classList.toggle('active', m === 'search');
      document.getElementById('answer-box').style.display = 'none';
      document.getElementById('results').innerHTML = '';
      document.getElementById('query').placeholder = 
        m === 'ask' ? 'What caused the servo to overheat?' : 'servo overheating gait';
    }

    async function submit() {
      const q = document.getElementById('query').value.trim();
      if (!q) return;
      const resultsEl = document.getElementById('results');
      const answerBox = document.getElementById('answer-box');
      resultsEl.innerHTML = '<div class="loading">searching memory...</div>';
      answerBox.style.display = 'none';

      if (mode === 'ask') {
        const r = await fetch('/ask', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({question: q, top_k: 5, subsystem: activeSubsystem})
        });
        const d = await r.json();
        answerBox.style.display = 'block';
        document.getElementById('answer-text').textContent = d.answer;
        document.getElementById('answer-sources').textContent = 
          `sources: ${d.sources.join(', ')} · ${d.chunks_used} chunks used`;
        renderChunks(d.raw_chunks || []);
      } else {
        const r = await fetch('/query', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({query: q, top_k: 10, subsystem: activeSubsystem})
        });
        const d = await r.json();
        renderChunks(d.results);
      }
      loadStats();
    }

    function renderChunks(chunks) {
      const el = document.getElementById('results');
      if (!chunks.length) { el.innerHTML = '<div class="loading">no results found</div>'; return; }
      el.innerHTML = chunks.map(c => `
        <div class="chunk">
          <div class="chunk-meta">
            <span class="score">${c.score}</span>
            <span class="subsystem">${c.subsystem}</span>
            <span>${c.memory_type}</span>
            <span>${c.doc_name}</span>
          </div>
          <div class="chunk-text">${c.text}</div>
        </div>
      `).join('');
    }

    loadStats();
    loadFilters();
  </script>
</body>
</html>
```

### Updated api/main.py (adds /stats, /config, /ui)
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from memory.retrieve import query
from ingestion.ingest import ingest_file
from memory.qdrant_store import ensure_collection, get_stats
from openai import OpenAI
from dotenv import load_dotenv
from config import cfg
load_dotenv()

app = FastAPI(title="Engram API")
llm = OpenAI(
    base_url=cfg('llm', 'base_url'),
    api_key=os.getenv("LLM_API_KEY", "ollama")
)

@app.on_event("startup")
def startup():
    ensure_collection()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    subsystem: str = None

class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    subsystem: str = None

class IngestRequest(BaseModel):
    filepath: str

@app.get("/ui", response_class=HTMLResponse)
def ui():
    ui_path = os.path.join(os.path.dirname(__file__), "ui.html")
    with open(ui_path) as f:
        return f.read()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    return get_stats()

@app.get("/config")
def config():
    return {
        "project": cfg('project', 'name'),
        "domain": cfg('project', 'domain'),
        "subsystems": cfg('subsystems'),
        "memory_types": cfg('memory_types'),
        "llm_model": cfg('llm', 'model'),
    }

@app.post("/query")
def query_memory(req: QueryRequest):
    results = query(req.query, top_k=req.top_k, subsystem=req.subsystem)
    return {"results": results}

@app.post("/ask")
def ask(req: AskRequest):
    results = query(req.question, top_k=req.top_k, subsystem=req.subsystem)
    if not results:
        return {"answer": "No relevant memory found.", "sources": [], "chunks_used": 0}

    context = "\n\n---\n\n".join([
        f"[{r['memory_type']} | {r['subsystem']} | score={r['score']}]\n{r['text']}"
        for r in results
    ])
    prompt = f"""You are an engineering memory assistant.
Answer using ONLY the context below. Be concise and technical.
If the context doesn't answer the question, say so explicitly.

CONTEXT:
{context}

QUESTION: {req.question}

ANSWER:"""

    response = llm.chat.completions.create(
        model=cfg('llm', 'model'),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=cfg('llm', 'max_tokens'),
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": list(set(r["doc_name"] for r in results)),
        "chunks_used": len(results),
        "raw_chunks": results,
    }

@app.post("/ingest")
def ingest(req: IngestRequest):
    n = ingest_file(req.filepath)
    return {"chunks_added": n}
```

---

## PHASE 4 — Domain Templates

When someone clones engram, they pick a domain:

### templates/robotics.yaml
```yaml
subsystems: [servo, imu, gait, power, vision, slam, ik, firmware]
memory_types: [episodic, semantic, procedural, causal]
vault_structure: [hardware, gait, debugging, experiments, firmware, telemetry, decisions]
note_template: |
  ---
  memory_type: episodic
  subsystem: unknown
  tags: []
  date: {{date}}
  ---
```

### templates/gamedev.yaml
```yaml
subsystems: [gameplay, rendering, audio, networking, ui, physics, ai]
memory_types: [episodic, semantic, procedural, causal]
vault_structure: [bugs, features, playtests, builds, design, assets]
```

### templates/research.yaml
```yaml
subsystems: [experiment, dataset, model, results, literature, hypothesis]
memory_types: [episodic, semantic, procedural, causal]
vault_structure: [papers, experiments, results, hypotheses, methods, notes]
```

---

## PHASE 5 — README.md (Open Source)

```markdown
# engram — Engineering Memory System

> Your project never forgets.

Engram is a local-first, free, persistent memory system for engineers.
It turns your notes, commits, debugging sessions, and experiments into
a searchable, queryable knowledge base — powered by open source tools
running entirely on your machine.

## Quick Start

git clone https://github.com/aryasgit/engram
cd engram
./install.sh
./start.sh

Open http://localhost:8000/ui

## What It Does

- Write a note in Obsidian → saved instantly in vector memory
- Ask "what caused that servo bug last week?" → grounded answer
- Every git commit is searchable by meaning, not just keyword
- Works offline, zero API costs, your data never leaves your machine

## Stack

| Component | Tool |
|---|---|
| Vector DB | Qdrant (local Docker) |
| Embeddings | all-MiniLM-L6-v2 (local) |
| LLM | Ollama (local) |
| API | FastAPI |
| Notes | Obsidian |

## Requirements

- macOS / Linux
- Docker
- Python 3.10+
- 8GB RAM minimum (16GB recommended for better models)

## Origin

Built for BARQ — an autonomous quadruped robot. Generalised for any project.
```

---

## PHASE 6 — Monetisation Roadmap

### Tier 1: Open Source (Now)
- MIT licensed
- Local only
- Free forever
- GitHub stars → credibility → job offers

### Tier 2: VS Code / Cursor Extension (~Month 1)
- Extension queries local `/ask` endpoint inline
- Shows memory results in sidebar as you code
- Free extension, drives awareness
- Publish to VS Code marketplace

### Tier 3: Cloud Hosted (~Month 3)
- `app.engram.dev`
- Managed Qdrant + web UI + sync
- No Docker, no setup
- $9/month solo · $29/month team (3 users)
- Tech: Railway or Fly.io for hosting (free tier to start)

### Tier 4: Team Memory (~Month 6)
- Shared Qdrant collections
- Multiple engineers, one memory
- Slack integration (query from Slack)
- $49/month per team
- This is the real B2B play

### Revenue Projections (Conservative)
| Tier | Users | MRR |
|---|---|---|
| 100 solo cloud | 100 | $900 |
| 10 teams | 10 | $490 |
| Total | | ~$1,400/mo |

Not life-changing, but real. And it compounds.

---

## Launch Sequence

### Day of Launch (after build)
1. Push to GitHub (public, MIT)
2. Post on **r/selfhosted**: "I built a local-first engineering memory system — no API costs, runs on your machine"
3. Post on **r/robotics**: "Built this for my quadruped robot, open sourced it"
4. **Hacker News Show HN**: "Show HN: Engram – local engineering memory with semantic search"
5. Tweet thread with demo GIF

### Week 1
- Reply to every comment
- Fix issues that come in
- Add to awesome-selfhosted
- Submit to GitHub Student showcase

---

## Files to Create Today

```
engram/
├── engram.config.yaml      ← NEW: master config
├── config.py               ← NEW: config loader
├── install.sh              ← NEW: one-command setup
├── start.sh                ← NEW: one-command start
├── stop.sh                 ← NEW: one-command stop
├── .env.example            ← NEW: template env file
├── LICENSE                 ← NEW: MIT license
├── README.md               ← NEW: public readme
├── api/
│   ├── main.py             ← UPDATE: add /ui /stats /config
│   └── ui.html             ← NEW: web dashboard
├── memory/
│   └── qdrant_store.py     ← UPDATE: reads from config
├── ingestion/
│   └── embedder.py         ← UPDATE: reads from config
└── templates/
    ├── robotics.yaml        ← NEW
    ├── gamedev.yaml         ← NEW
    └── research.yaml        ← NEW
```

---

## Success Metrics

| Metric | Target |
|---|---|
| GitHub stars (week 1) | 50+ |
| GitHub stars (month 1) | 200+ |
| HN front page | Yes |
| First cloud paying user | Month 3 |
| VS Code extension installs | 500+ |

---

*Built from BARQ. Open sourced for everyone.*
