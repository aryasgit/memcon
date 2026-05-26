# BARQ HIVE MIND — Complete Reference
> Last updated: 2026-05-25 | Machine: Mac Mini M4 16GB

---

## What Is This?

A **local, free, persistent engineering memory system** for the BARQ quadruped robot project.

It stores every note, debugging session, experiment, and git commit as searchable vector embeddings. You can ask it natural language questions and it returns answers grounded in your own engineering history.

**Nothing calls a paid API. Everything runs on your Mac Mini.**

---

## System Architecture

```
~/BARQ/
├── src/        ← Robot code (github.com/aryasgit/quadruped) — deploys to Jetson
└── hive/       ← Memory system (github.com/aryasgit/bark-hive) — runs on Mac
```

```
Write note in Obsidian (vault/)
        ↓
   Save (Cmd+S)
        ↓
 watcher.py detects change
        ↓
 chunker.py splits into chunks
        ↓
 embedder.py → all-MiniLM-L6-v2 (local, 384-dim)
        ↓
 qdrant_store.py → stored in Qdrant (local Docker)
        ↓
 Instantly queryable via /query or /ask
```

---

## Stack

| Component | Tool | Where it runs |
|---|---|---|
| Vector database | Qdrant (Docker) | localhost:6333 |
| Embedding model | all-MiniLM-L6-v2 (sentence-transformers) | Local, ~90MB |
| LLM for /ask | qwen2.5-coder:7b via Ollama | Local, Mac Mini |
| API backend | FastAPI + uvicorn | localhost:8000 |
| Knowledge vault | Obsidian → ~/BARQ/hive/vault/ | Local |
| File watcher | Python watchdog | Local process |
| Version control | GitHub (bark-hive) | github.com/aryasgit/bark-hive |

---

## File Structure

```
~/BARQ/hive/
├── .env                        ← API keys (never committed)
├── .gitignore
├── docker-compose.yml          ← Qdrant container definition
├── requirements.txt
├── STARTUP.md
│
├── vault/                      ← ALL Obsidian notes live here
│   ├── _templates/
│   │   └── barq_note.md        ← Frontmatter template
│   ├── hardware/
│   ├── gait/
│   ├── debugging/
│   ├── experiments/
│   ├── firmware/
│   ├── telemetry/
│   └── decisions/
│
├── ingestion/
│   ├── chunker.py              ← Splits markdown into chunks
│   ├── embedder.py             ← Embeds text via sentence-transformers
│   ├── ingest.py               ← Orchestrates chunk → embed → store
│   └── watcher.py              ← Watches vault/ and auto-ingests on save
│
├── memory/
│   ├── qdrant_store.py         ← Qdrant client interface
│   └── retrieve.py             ← Semantic search CLI
│
├── api/
│   └── main.py                 ← FastAPI: /query, /ask, /ingest, /health
│
├── scripts/
│   ├── ingest_all.py           ← Bulk ingest entire vault
│   └── ingest_git.py           ← Ingest git commit history from src/
│
└── qdrant_storage/             ← Qdrant persistent data (never committed)
```

---

## Startup — Every Session (Run In This Order)

### 1. Mac Terminal — Start Qdrant
```bash
cd ~/BARQ/hive
docker compose up -d
```

Verify:
```bash
curl http://localhost:6333/health
```

### 2. Cursor Terminal — Tab 1 (API)
```bash
cd ~/BARQ/hive
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

### 3. Cursor Terminal — Tab 2 (Vault Watcher)
```bash
cd ~/BARQ/hive
source .venv/bin/activate
python ingestion/watcher.py vault/
```

### 4. Open Obsidian
- Vault location: `~/BARQ/hive/vault/`
- Write a note → Cmd+S → auto-ingested instantly

---

## Shutdown

```bash
# Cursor terminals
Ctrl+C   ← stops watcher
Ctrl+C   ← stops uvicorn

# Mac terminal
docker stop barq-qdrant-1
```

All data persists in `qdrant_storage/`. Nothing is lost.

---

## API Endpoints

Base URL: `http://localhost:8000`

### GET /health
```bash
curl http://localhost:8000/health
```

### POST /query — Semantic search (raw chunks)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "servo overheating", "top_k": 5}'
```

Optional filter by subsystem:
```bash
  -d '{"query": "servo overheating", "top_k": 5, "subsystem": "servo"}'
```

### POST /ask — RAG answer (LLM grounded in memory)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What caused the RR wrist servo to overheat?"}'
```

### POST /ingest — Ingest a specific file
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"filepath": "vault/debugging/my_note.md"}'
```

---

## CLI Query (no API needed)

```bash
cd ~/BARQ/hive
source .venv/bin/activate
python memory/retrieve.py servo overheating backward gait
```

---

## Bulk Operations

### Re-ingest entire vault
```bash
python scripts/ingest_all.py
```

### Ingest git history from src/
```bash
python scripts/ingest_git.py
```
Requires `BARQ_REPO=/Users/barq/BARQ/src` in `.env` and a git repo to exist there.

### Wipe and re-ingest from scratch
```bash
curl -X DELETE http://localhost:6333/collections/barq_memory
python scripts/ingest_all.py
```

---

## Obsidian Note Format

Every note must have this frontmatter for proper tagging:

```yaml
---
memory_type: episodic
subsystem: servo
tags: [rr_wrist, overheating, gait]
date: 2026-05-25
---
```

### memory_type values
| Value | Use for |
|---|---|
| `episodic` | Debugging sessions, experiments, incidents |
| `semantic` | Facts, specs, hardware reference |
| `procedural` | Step-by-step procedures, calibration |
| `causal` | Root cause analysis, failure chains |

### subsystem values
`servo` · `imu` · `gait` · `power` · `vision` · `voice` · `slam` · `ik` · `version_control`

---

## Environment Variables (.env)

```
ANTHROPIC_API_KEY=...     ← Optional, only if swapping Ollama for Claude API
BARQ_REPO=/Users/barq/BARQ/src   ← Path to robot code repo for git ingestion
QDRANT_HOST=localhost
QDRANT_PORT=6333
HF_TOKEN=dummy                   ← Suppresses HuggingFace rate limit warning
```

---

## LLM Configuration

Currently using **Ollama qwen2.5-coder:7b** (local, free, ~5GB).

To change model, edit one line in `api/main.py`:
```python
model="qwen2.5-coder:7b",   # change this
```

Available local models (pull with `ollama pull <name>`):
| Model | Size | Best for |
|---|---|---|
| `llama3.2` | 2GB | Fast, lightweight |
| `qwen2.5-coder:7b` | 5GB | Code + technical (current) |
| `llama3.1:8b` | 5GB | General reasoning |
| `qwen2.5:14b` | 9GB | Best quality on M4 16GB |

---

## Reinstall From Scratch (if venv breaks)

```bash
cd ~/BARQ/hive
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn qdrant-client sentence-transformers watchdog \
  networkx anthropic python-frontmatter tiktoken python-dotenv gitpython rich openai
```

---

## GitHub

- Repo: `github.com/aryasgit/bark-hive` (private)
- Never committed: `.env`, `.venv/`, `qdrant_storage/`

```bash
# Push changes
cd ~/BARQ/hive
git add .
git commit -m "your message"
git push
```

---

## When Robot Code Starts

```bash
# Clone existing quadruped repo into src/
cd ~/BARQ/src
git clone https://github.com/aryasgit/quadruped.git .

# Ingest all commits into hive memory
cd ~/BARQ/hive
python scripts/ingest_git.py
```

Add a git hook to auto-ingest on every commit:
```bash
echo '#!/bin/sh
cd ~/BARQ/hive && source .venv/bin/activate && python scripts/ingest_git.py' \
> ~/BARQ/src/.git/hooks/post-commit
chmod +x ~/BARQ/src/.git/hooks/post-commit
```

---

## Roadmap

| Phase | Feature | Status |
|---|---|---|
| MVP | Qdrant + embeddings + FastAPI | ✅ Done |
| MVP | Obsidian vault + watcher | ✅ Done |
| MVP | /query semantic search | ✅ Done |
| MVP | /ask RAG with local LLM | ✅ Done |
| MVP | GitHub backup | ✅ Done |
| Week 1 | Git commit ingestion | ⬜ Ready (needs src/ repo) |
| Week 1 | Neo4j knowledge graph | ⬜ Pending |
| Week 1 | Telemetry log ingestion | ⬜ Pending |
| Week 1 | Jetson SSH log ingestion | ⬜ Pending |
| Advanced | Multi-agent orchestration | ⬜ Future |
| Advanced | Autonomous debugging loop | ⬜ Future |
