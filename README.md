<div align="center">

```
███╗   ███╗███████╗███╗   ███╗ ██████╗ ██████╗ ███╗   ██╗
████╗ ████║██╔════╝████╗ ████║██╔════╝██╔═══██╗████╗  ██║
██╔████╔██║█████╗  ██╔████╔██║██║     ██║   ██║██╔██╗ ██║
██║╚██╔╝██║██╔══╝  ██║╚██╔╝██║██║     ██║   ██║██║╚██╗██║
██║ ╚═╝ ██║███████╗██║ ╚═╝ ██║╚██████╗╚██████╔╝██║ ╚████║
╚═╝     ╚═╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
```

**Memory Context for Claude.**
**Your project never forgets.**

[![License: MIT](https://img.shields.io/badge/License-MIT-000.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-000.svg)](https://python.org)
[![Local First](https://img.shields.io/badge/runs-100%25%20local-000.svg)]()
[![MCP Ready](https://img.shields.io/badge/MCP-ready-000.svg)]()

</div>

---

## What Memcon does in one paragraph

Memcon (**Mem**ory **Con**text) is a local, persistent memory layer that plugs
straight into Claude. Wire it up once and **Claude auto-queries your project
history before answering and auto-writes new debugging sessions, decisions, and
experiments after solving them** — no copy-paste, no manual note-taking. The
vault grows itself while you work. Nothing leaves your machine.

---

## The MCP loop — this is the whole point

```
┌──────────────────────────────────────────────────────────────┐
│  You: "Why is the RR wrist servo overheating again?"         │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
      Claude calls memcon_query("RR wrist servo overheating")
                              │
                              ▼
   Memcon embeds the query, looks up the top-5 most similar
   chunks from your vault — not the whole memory, only what
   semantically matches the symptoms.
                              │
                              ▼
   Claude answers grounded in YOUR history — not hallucinated.
                              │
                              ▼
      You confirm the fix. Claude calls memcon_write_debug(
         title, symptom, cause, fix, subsystem="servo")
                              │
                              ▼
   A new markdown note lands in vault/debugging/. The Obsidian
   watcher picks it up, embeds it, stores it. Searchable forever.
```

That's it. That's the product.

The MCP server is a thin process Claude Desktop / Cursor / Claude Code spawns
on demand over stdio. **It runs entirely on your machine. Zero cloud, zero API
cost, zero hosting.** You add 6 lines to a config file, restart Claude, and
suddenly Claude has reliable long-term memory of your project.

See [`memcon_mcp/README.md`](memcon_mcp/README.md) for the full tool catalogue
and per-client setup snippets.

---

## Install (the easy way)

### One-liner — macOS / Linux / WSL

```bash
curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh | bash
```

Clones into `~/memcon`, installs deps, picks the right LLM for your RAM,
pulls it via Ollama, starts Qdrant, and ingests the starter vault. Takes 5–10
minutes the first time (model download is the slow part).

Overrides:
```bash
# Custom install path
MEMCON_DIR=/opt/memcon curl -fsSL ... | bash
# Force a specific model
MEMCON_MODEL=qwen2.5-coder:14b curl -fsSL ... | bash
```

### No-Python mode — Docker only

If you'd rather not touch a Python venv:

```bash
git clone https://github.com/aryasgit/memcon.git && cd memcon
docker compose -f docker-compose.full.yml up -d --build
open http://localhost:8000/ui
```

Runs Qdrant + the API + the vault watcher as containers. You still need
Ollama on the host (Memcon reaches it via `host.docker.internal`).

### Manual (macOS)

```bash
git clone https://github.com/aryasgit/memcon.git
cd memcon
./install.sh
./start.sh
open http://localhost:8000/ui
```

### Manual (Windows)

Use WSL (recommended) or Git Bash:

```bash
# inside Ubuntu WSL
git clone https://github.com/aryasgit/memcon.git
cd memcon
./install.sh
```

`install.bat` + `start.bat` also exist if you want to skip WSL entirely.
Docker Desktop must be running either way.

---

## Wire Memcon into Claude

### Claude Desktop

1. Start Memcon: `cd ~/memcon && docker compose up -d`
2. Open `~/Library/Application Support/Claude/claude_desktop_config.json`
   (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows).
3. Merge this into the `mcpServers` block:

   ```json
   {
     "mcpServers": {
       "memcon": {
         "command": "/ABSOLUTE/PATH/TO/memcon/.venv/bin/python3",
         "args": ["-m", "memcon_mcp.server"],
         "cwd": "/ABSOLUTE/PATH/TO/memcon"
       }
     }
   }
   ```

4. Restart Claude Desktop. `memcon` should now appear in the tool menu.
5. Ask Claude *"use memcon to check what we know about servo overheating."*

### Cursor

Add the same block to `~/.cursor/mcp.json`. Restart Cursor.

### Claude Code

Add the same block to `~/.claude/settings.json` (or a project-level
`.claude/settings.json`).

### Reliable auto-triggering

Claude has to *decide* to call the tools. To make that reflex automatic, paste
this into Claude's project memory:

> You have access to the `memcon_*` MCP tools. Before answering any question
> about this project, call `memcon_query` with the user's symptoms/keywords
> and use the returned chunks as authoritative context. After solving a
> problem, call `memcon_write_debug` (or `_decision` / `_experiment`) so the
> resolution persists. At the end of a session, call `memcon_session_summary`.
> Do not invent project details that are not in the returned chunks.

---

## Hardware → model auto-pick

`install.sh` detects RAM and writes the right model into `memcon.config.yaml`:

| RAM | Model | Notes |
|---|---|---|
| 64GB+ | `qwen2.5-coder:32b` | Flagship — best memory tracking |
| 32–64GB | `qwen2.5-coder:14b` | Strong technical reasoning |
| 16–32GB | `qwen2.5-coder:7b` | Solid default |
| 8–16GB | `qwen2.5-coder:3b` | Balanced |
| <8GB | `llama3.2:1b` | Lightweight |

Override at install time with `MEMCON_MODEL=qwen2.5:72b ./install.sh`.

---

## What's inside

```
memcon/
├── memcon.config.yaml         ← master configuration
├── config.py                  ← yaml loader
│
├── memcon_mcp/                ← MCP server (the headline)
│   ├── server.py              ← 9 tools over stdio
│   └── README.md              ← per-client setup
│
├── api/
│   ├── main.py                ← FastAPI: /ask /query /memory/* /ingest /ui
│   └── ui.html                ← Claude-style chat dashboard
│
├── ingestion/
│   ├── chunker.py             ← markdown → semantic chunks
│   ├── embedder.py            ← all-MiniLM-L6-v2 (local, 90MB)
│   ├── ingest.py              ← chunk → embed → upsert
│   └── watcher.py             ← auto-ingest on Obsidian save
│
├── memory/
│   ├── qdrant_store.py        ← Qdrant client
│   ├── retrieve.py            ← semantic search
│   └── writer.py              ← programmatic note creation
│
├── vault/                     ← YOUR notes — open this in Obsidian
│   ├── debugging/
│   ├── decisions/
│   ├── experiments/
│   └── …
│
├── scripts/
│   ├── ingest_all.py          ← bulk ingest the vault
│   └── ingest_git.py          ← ingest git commit history
│
├── bootstrap.sh               ← curl one-liner installer
├── install.sh / install.bat   ← per-OS installers
├── start.sh / stop.sh         ← lifecycle scripts
├── Dockerfile                 ← container image
├── docker-compose.yml         ← Qdrant only
└── docker-compose.full.yml    ← Qdrant + API (no-Python mode)
```

---

## Stack

| Layer | Tool | Why |
|---|---|---|
| Vector DB | Qdrant (Docker) | Best local vector DB, free, persistent |
| Embeddings | all-MiniLM-L6-v2 | 384-dim, ~90MB, no API needed |
| Local LLM | Ollama + Qwen2.5-Coder | Free, runs on Apple Silicon / CUDA / CPU |
| API | FastAPI + uvicorn | Async, auto OpenAPI docs |
| Notes | Obsidian → `vault/` | Best local markdown app |
| Watcher | Python watchdog | Auto-ingest on save |
| MCP | `mcp` Python SDK | Official Anthropic SDK, stdio transport |

---

## Configuration

Everything in one file: `memcon.config.yaml`

```yaml
project:
  name: "BARQ"               # change for your project
  description: "..."
  domain: "robotics"

vault:
  path: "./vault"
  skip_dirs: ["_templates"]
  chunk_size: 400
  min_chunk_length: 30

memory:
  collection: "memcon_memory"
  embedding_model: "all-MiniLM-L6-v2"
  vector_dim: 384

llm:
  provider: "ollama"
  model: "qwen2.5-coder:7b"  # auto-set by install.sh
  base_url: "http://localhost:11434/v1"
  max_tokens: 1024

qdrant:
  host: "localhost"
  port: 6333

subsystems: [servo, imu, gait, power, vision, voice, slam, ik, version_control]
memory_types: [episodic, semantic, procedural, causal]
```

---

## Writing notes by hand

You don't *need* to write notes manually — Claude does that via MCP. But if
you want to:

```markdown
---
memory_type: episodic
subsystem: servo
tags: [overheating, rr_wrist]
date: 2026-05-26
---

# RR Wrist Servo Overheating

## Symptom
Overheats during backward gait, snaps to default angle.

## Cause
Unequal static load distribution.

## Fix
Paper-slip foot contact test + IMU roll/pitch logging.
```

Drop it anywhere in `vault/`. The watcher picks it up, embeds it, stores it.

---

## REST API (if you want to drive Memcon programmatically)

Base: `http://localhost:8000`

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | status check |
| GET | `/stats` | chunk count, collection, project |
| GET | `/config` | active config |
| GET | `/memory/recent?limit=10` | latest notes |
| GET | `/memory/note?path=...` | raw markdown of a note |
| POST | `/query` | semantic search (raw chunks) |
| POST | `/ask` | RAG answer (LLM grounded in memory) |
| POST | `/ingest` | manually ingest a file |
| POST | `/memory/debug` | write a debug note |
| POST | `/memory/decision` | write a decision |
| POST | `/memory/experiment` | write an experiment |
| POST | `/memory/session` | write a session summary |
| POST | `/memory/update` | append to an existing note |
| GET | `/ui` | the web dashboard |

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What caused the servo to overheat?", "top_k": 5}'
```

---

## Reset / rebuild

```bash
# Wipe Qdrant and re-ingest from scratch
curl -X DELETE http://localhost:6333/collections/memcon_memory
python3 scripts/ingest_all.py
```

If the venv breaks (e.g. after moving the folder):

```bash
rm -rf .venv && ./install.sh
```

---

## Origin

Memcon was built as the memory system for **BARQ** — an autonomous 12-DOF
quadruped robot. After spending hours rediscovering old debugging sessions
and forgetting why architectural decisions were made, a persistent
project memory became a necessity.

The system generalised naturally: every long-running engineering project has
the same problem. Memcon is the solution.

---

## License

MIT — do whatever you want with it.

---

<div align="center">

Built for engineers who build hard things.

**[⭐ Star on GitHub](https://github.com/aryasgit/memcon)**

</div>
