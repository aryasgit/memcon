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
[![GitHub stars](https://img.shields.io/github/stars/aryasgit/memcon?style=flat&color=000&logo=github&logoColor=white)](https://github.com/aryasgit/memcon/stargazers)
[![Sponsor](https://img.shields.io/badge/sponsor-❤-000.svg?logo=github-sponsors&logoColor=white)](https://github.com/sponsors/aryasgit)

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
cost, zero hosting.** The installer wires it into Claude Desktop for you;
restart Claude and suddenly it has reliable long-term memory of your project.

**Low-friction writes:** you don't have to spell out every field. Tell
Claude *"save this as a debugging session"* and `memcon_capture` invokes the
local LLM to extract title / symptom / cause / fix / subsystem / tags from
context, then writes the structured note.

**Self-organising vault:** every new note auto-gets an `## Related` section
with Obsidian `[[wikilinks]]` to the top-3 semantically similar notes — so
the graph view fills itself in as you work.

See [`memcon_mcp/README.md`](memcon_mcp/README.md) for the full tool catalogue
and per-client setup snippets.

---

## Install (the easy way)

### One-liner

#### macOS / Linux / WSL (bash)

```bash
curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh | bash
```

#### Windows (PowerShell)

```powershell
iwr -useb https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.ps1 | iex
```

Either one clones into `~/memcon`, installs deps, picks the right LLM for
your RAM, pulls it via Ollama, starts Qdrant, ingests the starter vault, **and
auto-registers Memcon in your Claude Desktop config** (preserves any
existing MCP servers). Takes 5–10 minutes the first time.

After it finishes, fully quit Claude Desktop and reopen — `memcon` is
already wired in.

Overrides (set as env vars before the one-liner):

| Var | What |
|---|---|
| `MEMCON_DIR` | Custom install path (default `~/memcon`) |
| `MEMCON_MODEL` | Force a specific Ollama model (skips the RAM-auto-pick) |
| `MEMCON_SKIP_MCP=1` | Skip Claude Desktop registration |
| `MEMCON_REF` | Branch / tag (default `main`) |

Example:
```bash
MEMCON_MODEL=qwen2.5-coder:14b curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh | bash
```

```powershell
$env:MEMCON_MODEL="qwen2.5-coder:14b"; iwr -useb https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.ps1 | iex
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

> **If you used the one-liner above, this is already done for you.**
> The installer ran `scripts/register_mcp.py` which wrote the memcon
> entry into your Claude Desktop config (preserving any other MCP servers
> you had). Skip ahead to *Reliable auto-triggering* — just fully quit
> Claude Desktop and reopen.

If you installed manually (or want to wire other clients):

### Claude Desktop

1. Start Memcon: `cd ~/memcon && docker compose up -d`
2. Open the config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`
3. Merge this into the `mcpServers` block:

   ```json
   {
     "mcpServers": {
       "memcon": {
         "command": "/ABSOLUTE/PATH/TO/memcon/.venv/bin/python3",
         "args": ["/ABSOLUTE/PATH/TO/memcon/memcon_mcp/server.py"]
       }
     }
   }
   ```

   On Windows, the command path is
   `C:\path\to\memcon\.venv\Scripts\python.exe` instead.

   > Why `args=["…/server.py"]` instead of `args=["-m","memcon_mcp.server"]`?
   > Claude Desktop on macOS sandboxes the MCP subprocess with `cwd=/` and
   > strips `PYTHONPATH`, so `-m` can't find the `memcon_mcp` package.
   > Running `server.py` by absolute path puts the script's directory on
   > `sys.path` automatically and works under the sandbox.

4. Fully quit Claude Desktop (`Cmd+Q` / right-click tray → Quit), reopen.
5. Ask Claude *"use memcon to check what we know about servo overheating."*

Or just re-run the auto-registrar instead of editing JSON by hand:
```bash
python3 scripts/register_mcp.py
```

### Cursor

Add the same block to `~/.cursor/mcp.json`. Restart Cursor.

### Claude Code

Add the same block to `~/.claude/settings.json` (or a project-level
`.claude/settings.json`).

### Reliable auto-triggering

Claude has to *decide* to call the tools. To make that reflex automatic,
paste this into Claude's project memory / system prompt:

> You have access to the `memcon_*` MCP tools. Before answering any question
> about this project, call `memcon_query` with the user's symptoms/keywords
> and use the returned chunks as authoritative context.
>
> When the user asks to save/log/remember something — phrases like
> "save this", "log this", "save the debugging session", "log my decision",
> "remember this experiment", "session summary" — **always reach for
> `memcon_capture`**. Summarise the recent conversation into the `text`
> argument; the local LLM running inside memcon will extract title /
> symptom / cause / fix (or decision / reasoning, etc.) automatically. Only
> use `memcon_write_debug` / `_decision` / `_experiment` when the user
> explicitly provides pre-structured fields.
>
> At the end of a working session, call `memcon_session_summary` (or
> `memcon_capture` with `hint="session"`). Do not invent project details
> that are not in the returned chunks.

---

## What goes into memory

Memcon can ingest much more than hand-written markdown notes:

| Source | How | Tagged as |
|---|---|---|
| **Markdown in `vault/`** | Auto-ingested on save via the watcher | `subsystem` from frontmatter |
| **PDFs in `vault/`** | Drop a `.pdf` anywhere in `vault/` — auto-extracted page-by-page | `subsystem=docs` |
| **Source code** | `python3 scripts/ingest_code.py [path]` walks a project directory respecting common exclusions (`.git`, `.venv`, `node_modules`, build dirs, binaries) | `subsystem=code`, `memory_type=procedural` |
| **Git commits** | `./scripts/install_git_hook.sh [/path/to/repo]` installs a post-commit hook that ingests each commit automatically | `subsystem=version_control`, `memory_type=episodic` |
| **MCP writes** | `memcon_capture` / `memcon_write_*` from Claude — auto-extracted and structured | per-tool defaults |

## In your editor — VS Code & Cursor

Memcon ships with an extension that works in **both** VS Code and Cursor
(Cursor reads VS Code extensions natively).

| Command | Default shortcut | What |
|---|---|---|
| `Memcon: Ask` | `Cmd+Shift+M` / `Ctrl+Shift+M` | Grounded answer opens in a markdown tab |
| `Memcon: Save selection to memory` | `Cmd+Shift+S` / `Ctrl+Shift+S` | Captures selection + file path + optional note |
| `Memcon: Search` | — | Raw chunks for inspection |
| `Memcon: Open dashboard` | — | Opens `localhost:8000/ui` |
| Sidebar "Recent" tree | — | Activity-bar view of recent notes, click to peek |

Install the pre-built VSIX:

```bash
# From a Memcon clone
cd vscode
npm install && npm run compile
npx @vscode/vsce package --no-dependencies
# → produces memcon-vscode-0.1.0.vsix
```

Then in VS Code / Cursor: `Cmd+Shift+P` → **Extensions: Install from VSIX…** → pick the file → reload window.

A pre-built copy is also available from the landing page at `/install/memcon-vscode-0.1.0.vsix`.

See [vscode/README.md](vscode/README.md) for the full extension docs.

---

## CLI

`bin/memcon` is a one-binary CLI to the local API. Add `~/memcon/bin` to your
`PATH` and you can run from any directory:

```bash
memcon ask    "what caused the servo to overheat?"
memcon query  "imu calibration"
memcon recent
memcon stats
memcon digest 14            # LLM-generated summary of last 14 days
memcon save   "today I…"    # session-summary capture
memcon serve                # start API + watcher (= ./start.sh)
memcon ui                   # open the dashboard in your browser
```

## Multi-project switching

One Memcon install can back N projects via environment variables:

```bash
# In project foo's shell
export MEMCON_VAULT=~/projects/foo/vault
export MEMCON_COLLECTION=foo_memory
./start.sh

# Different terminal, project bar
export MEMCON_VAULT=~/projects/bar/vault
export MEMCON_COLLECTION=bar_memory
./start.sh
```

| Var | Overrides |
|---|---|
| `MEMCON_VAULT` | `vault.path` in yaml |
| `MEMCON_COLLECTION` | Qdrant collection name |
| `MEMCON_MODEL` | Ollama model |
| `MEMCON_QDRANT_HOST` / `_PORT` | Qdrant endpoint |

---

## Cross-OS install matrix

| OS | One-liner | Notes |
|---|---|---|
| **macOS / Linux / WSL** | `curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh \| bash` | Uses bash |
| **Windows native** (PowerShell) | `iwr -useb https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.ps1 \| iex` | Uses PowerShell + `install.bat` |

Behind the scenes:

| Concern | macOS | Linux | Windows |
|---|---|---|---|
| Bootstrap script | `bootstrap.sh` | `bootstrap.sh` | `bootstrap.ps1` |
| Installer | `install.sh` | `install.sh` | `install.bat` |
| RAM detection | `sysctl hw.memsize` | `/proc/meminfo` | `wmic` |
| Claude config path | `~/Library/Application Support/Claude/…` | `~/.config/Claude/…` | `%APPDATA%\Claude\…` |
| Venv interpreter | `.venv/bin/python3` | `.venv/bin/python3` | `.venv\Scripts\python.exe` |
| Skip MCP registration | `MEMCON_SKIP_MCP=1 …` | same | `set MEMCON_SKIP_MCP=1` |

`scripts/register_mcp.py` is cross-platform and handles all three config
paths and venv layouts. Bad / non-JSON existing configs get backed up
automatically (`*.bak-<timestamp>`). Permission failures degrade gracefully
— the rest of the install keeps going and the script prints a one-line
warning.

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

## Troubleshooting

### Claude Desktop says `memcon: Server disconnected`

Click **Open developer settings** → select `memcon` → **View Logs**, or
in Terminal:
```bash
tail -60 ~/Library/Logs/Claude/mcp-server-memcon.log
```

Most common causes:

| Log says | Fix |
|---|---|
| `No module named 'memcon_mcp'` | You're using the old `-m memcon_mcp.server` form. Use the absolute-path form (`args: ["/path/to/memcon/memcon_mcp/server.py"]`) — Claude Desktop sandboxes the spawn with `cwd=/` and `-m` can't find the package. Run `python3 scripts/register_mcp.py` to rewrite it correctly. |
| `No module named 'mcp'` / `'openai'` | venv is missing dependencies. Run `./install.sh` or `.venv/bin/python3 -m pip install -r requirements.txt`. |
| `[Errno 30] Read-only file system: 'vault'` | Old code with relative `vault.path`. `git pull` and restart Claude Desktop — the fix is in `config.py` (absolutises the vault path at config-load). |
| `Connection refused` to localhost:6333 | Qdrant container is stopped. `cd ~/memcon && docker compose up -d` |

### "save this" / "save debug session" — Claude asks for more details instead of saving

By default Claude Desktop doesn't know that `memcon_capture` is the right
tool for loose, short save commands. Add the auto-triggering prompt above
to Claude's project memory. After that, any of these phrases will route
through `memcon_capture` and the local LLM will structure them:
- "save this" / "save it" / "log this"
- "save the debugging session" / "log my decision" / "remember this experiment"
- "session summary" / "save today's session"

If you're invoking from outside Claude (curl, scripts, etc.), call
`memcon_capture(text=...)` directly with a paragraph of context — no need
to fill in title/symptom/cause/fix yourself.

### `install.sh` set `embedding_model` to my LLM model

Old bug from before commit `f1d39bb`. Fix with one line and re-ingest:
```bash
sed -i '' 's|embedding_model: ".*"|embedding_model: "all-MiniLM-L6-v2"|' memcon.config.yaml
source .venv/bin/activate && python3 scripts/ingest_all.py
```

### Venv breaks after I move the project folder

Python venvs hard-code their absolute paths into the wrapper scripts. After
a move:
```bash
rm -rf .venv && ./install.sh
```

### First `memcon_query` is slow (3–5 seconds)

`sentence-transformers` lazy-loads the embedding model on the first call
of each process. Instant after that for the rest of the session. The
~90 MB model is cached locally so it doesn't re-download.

### MCP works in Claude Desktop but not in Claude Code (or vice versa)

Each client has its own config file:
- Claude Desktop → `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- Cursor → `~/.cursor/mcp.json`
- Claude Code CLI → `~/.claude/settings.json`

`scripts/register_mcp.py` only writes Claude Desktop's. Copy the same
`memcon` block into the other config files manually if you want it
everywhere.

---

## Roadmap

Feature-keyed (not date-keyed). See **[ROADMAP.md](ROADMAP.md)** for the full plan:

- **v1.0** *Plug into Claude* — ✅ shipped (MCP server, 9 tools, one-liner install)
- **v2.0** *Memory absorbs everything* — ✅ shipped (code/PDF/git ingestion, CLI, multi-project, 12 tools)
- **v3.0** *Lives in your editor* — 🚧 next (VS Code/Cursor extension with inline memory queries)
- **v4.0** *Knows what it knows* — contradiction detection, knowledge graph viewer, pattern surfacing
- **v5.0** *Multimodal & shared* — image/voice/web ingestion, team vaults
- **v6.0+** *Managed option, niche depth* — hosted tier, ROS bags, plugin SDK

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

## Support

Memcon is built and maintained in spare time. If it saves yours,
consider [sponsoring on GitHub](https://github.com/sponsors/aryasgit) —
every contribution funds direct development time and tells me this
matters. No paywalls, no pro tier, no telemetry.

---

<div align="center">

Built for engineers who build hard things.

**[⭐ Star on GitHub](https://github.com/aryasgit/memcon)** · **[❤ Sponsor](https://github.com/sponsors/aryasgit)**

</div>
