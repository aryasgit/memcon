<div align="center">

```
███████╗███╗   ██╗ ██████╗ ██████╗  █████╗ ███╗   ███╗
██╔════╝████╗  ██║██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
█████╗  ██╔██╗ ██║██║  ███╗██████╔╝███████║██╔████╔██║
██╔══╝  ██║╚██╗██║██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║
███████╗██║ ╚████║╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
```

**Your project never forgets.**

A local-first, free, persistent engineering memory system.  
Turns your notes, commits, debugging sessions, and experiments  
into a searchable, queryable knowledge base — powered entirely  
by open source tools running on your own machine.

[![License: MIT](https://img.shields.io/badge/License-MIT-00ff88.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-00ff88.svg)](https://python.org)
[![Local First](https://img.shields.io/badge/runs-100%25%20local-00ff88.svg)]()
[![Zero API Cost](https://img.shields.io/badge/API%20cost-zero-00ff88.svg)]()

</div>

---

## What is Engram?

Engram is a **persistent engineering memory system** built for engineers working on complex, long-running projects — robotics, hardware, game development, research, or any deep technical work.

It solves a problem every engineer faces: *you forget things.* Debugging sessions from 3 months ago. Why a specific architectural decision was made. What that weird IMU error was and how you fixed it. What commit introduced the gait regression.

Engram captures everything — notes, commits, logs, experiments — embeds them as vectors, and makes them queryable in plain English. Ask it a question. Get a grounded answer from your own engineering history.

**Everything runs on your machine. No cloud. No API costs. No data leaves your computer. Ever.**

---

## How It Works

```
You write a note in Obsidian
          │
          ▼
  watcher.py detects save
          │
          ▼
  chunker.py splits content
  into semantic chunks
          │
          ▼
  embedder.py converts chunks
  to 384-dim vectors via
  all-MiniLM-L6-v2 (local)
          │
          ▼
  Qdrant stores vectors +
  metadata (subsystem, memory
  type, tags, source)
          │
          ▼
  Instantly queryable via
  /query (semantic search) or
  /ask (LLM-grounded answer)
```

When you ask a question:

```
Your question
     │
     ▼
Embedded to vector
     │
     ▼
Qdrant finds top-k
most similar chunks
     │
     ▼
Chunks injected into
LLM prompt as context
     │
     ▼
Local LLM (Ollama) answers
grounded in YOUR memory
     │
     ▼
Answer + sources returned
```

---

## What Makes It Special

### 1. 100% Local, 100% Free — Forever
No OpenAI API key. No Pinecone. No cloud sync. No subscriptions.  
Qdrant runs in Docker on your machine. The embedding model (`all-MiniLM-L6-v2`) is downloaded once (~90MB). The LLM runs via Ollama. Everything is on-device. The total recurring cost is exactly $0.

### 2. Engineered Memory Taxonomy
Engram distinguishes between four types of engineering memory:

| Type | What it stores |
|---|---|
| **Episodic** | Debugging sessions, incidents, experiments — *things that happened* |
| **Semantic** | Facts, specs, hardware reference — *things you know* |
| **Procedural** | Calibration steps, wiring procedures, SOPs — *how to do things* |
| **Causal** | Root cause analyses, failure chains — *why things happened* |

This taxonomy makes retrieval dramatically more precise than keyword search.

### 3. Automatic Ingestion Pipeline
Write a note. Save it. Done. The file watcher detects the save, chunks the content, embeds it, and stores it in under a second. Your vault is always current — no manual sync, no batch jobs.

### 4. Semantic Search, Not Keyword Search
You don't need to remember exact words. Ask *"what caused that weird motor error last month"* — Engram finds the relevant debugging note even if your note says *"servo torque loss"* not *"motor error"*. Meaning is matched, not strings.

### 5. Git Commit Memory
Every commit in your project repo becomes a searchable memory. Ask *"when did we change the IK solver?"* and get the exact commit. Engineering history becomes queryable.

### 6. Domain-Configurable
One config file (`engram.config.yaml`) adapts Engram to any project type. Subsystems, memory types, vault structure, and LLM model are all configurable. Built-in templates for robotics, game development, and research.

### 7. Web Dashboard
A clean, local web UI at `localhost:8000/ui`. Search, filter by subsystem, switch between raw semantic search and LLM-grounded answers. No npm, no build step — single HTML file served by FastAPI.

---

## Demo

```
Query: "why did the servo overheat"

// ANSWER
The RR wrist servo overheated due to torque loss and snap to default
angle during backward gait. This was likely caused by vibration-loosened
wiring or a power brownout from servo current spikes.

sources: i2c_oserror, rr_wrist_overheating · 5 chunks used
```

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Docker | Any recent version |
| RAM | 8GB minimum, 16GB recommended |
| Storage | ~3GB (models + DB) |
| OS | macOS, Linux |

> **Recommended hardware:** Apple Silicon Mac (M1/M2/M3/M4) or any machine with 16GB RAM for best local LLM performance.

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/aryasgit/engram.git
cd engram
```

### 2. Install

```bash
./install.sh
```

This single script will:
- Check for Docker, Python 3, and Ollama (installs Ollama if missing)
- Create a Python virtual environment
- Install all Python dependencies
- Pull the local LLM model (`qwen2.5-coder:7b` by default, ~5GB)
- Start Qdrant vector database
- Create your vault folder structure
- Run the initial ingest

> First run takes 5–10 minutes depending on your internet speed (model download). Subsequent starts are instant.

### 3. Start

```bash
./start.sh
```

### 4. Open the dashboard

```
http://localhost:8000/ui
```

### 5. Start writing notes

Point **Obsidian** at the `vault/` folder:  
Obsidian → Open folder as vault → select `engram/vault/`

Every note you save is automatically ingested into memory.

---

## Manual Start (if you prefer)

```bash
# Terminal 1 — Qdrant (run once, keeps data across restarts)
docker compose up -d

# Terminal 2 — API + LLM
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 3 — Vault watcher (auto-ingests on save)
source .venv/bin/activate
python3 ingestion/watcher.py vault/
```

### Stop everything

```bash
./stop.sh
```

---

## Configuration

All configuration lives in one file: `engram.config.yaml`

```yaml
project:
  name: "My Project"
  description: "What you're building"
  domain: "robotics"          # robotics | gamedev | research | software

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
  provider: "ollama"
  model: "qwen2.5-coder:7b"  # change this to any Ollama model
  base_url: "http://localhost:11434/v1"
  max_tokens: 1024

qdrant:
  host: "localhost"
  port: 6333

subsystems:                   # customise for your project
  - servo
  - imu
  - gait

memory_types:
  - episodic
  - semantic
  - procedural
  - causal
```

---

## Writing Notes

Every note should include YAML frontmatter so Engram can tag and filter it correctly:

```markdown
---
memory_type: episodic
subsystem: servo
tags: [overheating, backward-gait, rr-wrist]
date: 2026-05-25
---

# RR Wrist Servo Overheating

## Symptom
Servo overheats during backward gait, causing torque loss and snap to default angle.

## Cause
Unequal static load distribution — RR leg bearing more weight during backward motion.

## Fix
Paper-slip foot contact test. IMU roll/pitch logging to detect lean.
```

### memory_type values

| Value | Use for |
|---|---|
| `episodic` | Debugging sessions, incidents, experiments |
| `semantic` | Facts, specs, reference material |
| `procedural` | Step-by-step procedures, calibration, SOPs |
| `causal` | Root cause analyses, failure chains |

Notes without frontmatter still work — they're tagged as `semantic / unknown` and fully searchable.

---

## API Reference

Base URL: `http://localhost:8000`

### GET /health
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### GET /stats
```bash
curl http://localhost:8000/stats
# {"total_chunks": 103, "collection": "engram_memory", ...}
```

### GET /config
```bash
curl http://localhost:8000/config
# Returns current project config
```

### POST /query — Semantic search (raw chunks)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "servo overheating", "top_k": 5}'
```

Filter by subsystem:
```bash
  -d '{"query": "servo overheating", "top_k": 5, "subsystem": "servo"}'
```

### POST /ask — RAG answer (LLM grounded in your memory)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What caused the RR wrist servo to overheat?"}'
```

Response:
```json
{
  "answer": "The RR wrist servo overheated due to...",
  "sources": ["rr_wrist_overheating", "i2c_oserror"],
  "chunks_used": 5,
  "raw_chunks": [...]
}
```

### POST /ingest — Manually ingest a file
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"filepath": "vault/debugging/my_note.md"}'
```

---

## Bulk Operations

### Re-ingest entire vault
```bash
source .venv/bin/activate
python3 scripts/ingest_all.py
```

### Ingest git history from your project repo
```bash
# Set BARQ_REPO in .env first
python3 scripts/ingest_git.py
```

### CLI query (no API needed)
```bash
source .venv/bin/activate
python3 memory/retrieve.py servo overheating backward gait
```

### Wipe and rebuild from scratch
```bash
curl -X DELETE http://localhost:6333/collections/engram_memory
python3 scripts/ingest_all.py
```

---

## Choosing a Local LLM

Engram uses Ollama for local inference. Change the model in `engram.config.yaml`:

```yaml
llm:
  model: "qwen2.5-coder:7b"   # change this line
```

Then pull the model:
```bash
ollama pull <model-name>
```

### Recommended models by hardware

| RAM | Recommended Model | Quality |
|---|---|---|
| 8GB | `llama3.2` (3B) | Good |
| 16GB | `qwen2.5-coder:7b` | Great — **default** |
| 16GB | `qwen2.5:14b` | Best quality |
| 32GB+ | `llama3.1:70b` | Exceptional |

> `qwen2.5-coder:7b` is the default because it's specifically trained on code and technical content — ideal for engineering projects.

---

## Domain Templates

Engram ships with three domain templates. To use one, copy it over your config:

```bash
cp templates/gamedev.yaml engram.config.yaml    # game development
cp templates/research.yaml engram.config.yaml   # academic research
cp templates/robotics.yaml engram.config.yaml   # robotics (default)
```

Or build your own by editing `engram.config.yaml` directly.

---

## Project Structure

```
engram/
├── engram.config.yaml      ← Master configuration
├── config.py               ← Config loader (reads yaml)
├── install.sh              ← One-command setup
├── start.sh                ← Start all services
├── stop.sh                 ← Stop all services
├── docker-compose.yml      ← Qdrant container
│
├── vault/                  ← Your notes (Obsidian vault)
│   ├── _templates/         ← Note templates
│   ├── debugging/
│   ├── experiments/
│   ├── decisions/
│   ├── hardware/
│   ├── firmware/
│   ├── telemetry/
│   └── gait/
│
├── ingestion/
│   ├── chunker.py          ← Splits markdown into chunks
│   ├── embedder.py         ← Embeds via sentence-transformers
│   ├── ingest.py           ← Orchestrates chunk → embed → store
│   └── watcher.py          ← File system watcher (auto-ingest)
│
├── memory/
│   ├── qdrant_store.py     ← Qdrant client + search interface
│   └── retrieve.py         ← CLI semantic search
│
├── api/
│   ├── main.py             ← FastAPI: /query /ask /ingest /ui
│   └── ui.html             ← Web dashboard (single file)
│
├── scripts/
│   ├── ingest_all.py       ← Bulk ingest entire vault
│   └── ingest_git.py       ← Ingest git commit history
│
└── templates/
    ├── robotics.yaml
    ├── gamedev.yaml
    └── research.yaml
```

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| Vector database | [Qdrant](https://qdrant.tech) | Best local vector DB, Docker-native, free |
| Embeddings | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Fast, 384-dim, excellent quality, ~90MB |
| Local LLM | [Ollama](https://ollama.com) | Best local model runner, Metal/CUDA support |
| API | [FastAPI](https://fastapi.tiangolo.com) | Fast, clean, automatic OpenAPI docs |
| Notes | [Obsidian](https://obsidian.md) | Best local markdown knowledge base |
| Watcher | [watchdog](https://github.com/gorakhargosh/watchdog) | Cross-platform file system events |

---

## Reinstalling / Resetting

### If venv breaks (e.g. after moving folder)
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install fastapi uvicorn qdrant-client sentence-transformers \
  watchdog anthropic python-frontmatter python-dotenv gitpython rich openai pyyaml
```

### Full reset (wipes all memory)
```bash
curl -X DELETE http://localhost:6333/collections/engram_memory
python3 scripts/ingest_all.py
```

---

## Roadmap

- [ ] VS Code / Cursor extension (inline memory queries while coding)
- [ ] Multi-project support (multiple collections, project switcher in UI)
- [ ] ROS bag / telemetry log ingestion
- [ ] PDF ingestion (papers, datasheets)
- [ ] Team shared memory (multi-user Qdrant)
- [ ] Cloud hosted version

---

## Origin

Engram was built as the memory system for **BARQ** — an autonomous 12-DOF quadruped robot. After spending hours rediscovering old debugging sessions and forgetting why certain architectural decisions were made, a persistent engineering memory became a necessity.

The system generalised naturally: every long-running engineering project has the same problem. Engram is the solution.

---

## Contributing

Contributions welcome. Open an issue first for major changes.

```bash
git clone https://github.com/aryasgit/engram.git
cd engram
./install.sh
```

---

## License

MIT — do whatever you want with it.

---

<div align="center">

Built for engineers who build hard things.

**[⭐ Star on GitHub](https://github.com/aryasgit/engram)**

</div>
