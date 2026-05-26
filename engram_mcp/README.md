# Engram MCP Server

Turn Engram into a **Model Context Protocol** backend for Claude. Once
connected, Claude can:

- **Auto-query** Engram before answering — pulls only the chunks relevant to
  the question (not the whole memory).
- **Auto-write** debug sessions, decisions, and experiments after solving a
  problem — so the next session (yours or someone else's) finds it.

No copy-paste. No manual note-taking. The vault grows itself while you work.

---

## Tools exposed

| Tool | What it does |
|---|---|
| `engram_query(query, top_k=5, subsystem=None)` | Semantic search — returns top-K relevant chunks. The hashmap lookup. |
| `engram_ask(question, top_k=5, subsystem=None)` | Self-contained answer using Engram's local LLM. Prefer `engram_query` if the calling LLM (you) wants raw context. |
| `engram_write_debug(title, symptom, cause, fix, status, subsystem, tags)` | Save a debugging session. |
| `engram_write_decision(title, decision, reasoning, subsystem, tags)` | Save an engineering decision. |
| `engram_write_experiment(title, hypothesis, result, conclusion, subsystem, tags)` | Save an experiment. |
| `engram_session_summary(summary, subsystem)` | End-of-session summary auto-save. |
| `engram_update_note(filepath, content)` | Append findings to an existing note. |
| `engram_stats()` | Chunk count, project, domain. |
| `engram_subsystems()` | List configured subsystems and memory types. |

---

## How the loop works

```
You: "Why is the RR wrist overheating?"
        ↓
Claude calls engram_query("RR wrist overheating servo")
        ↓
Engram returns top-5 chunks from past debug notes
        ↓
Claude answers grounded in YOUR project history (not hallucinated)
        ↓
After you confirm the fix:
Claude calls engram_write_debug(title, symptom, cause, fix, subsystem="servo")
        ↓
New note saved → re-ingested → searchable next session
```

The "hashmap" framing: each `engram_query` call is a key lookup against
semantic-similarity buckets. Only the matching chunks come back — not the
entire vault. Cheap, fast, and keyed by meaning rather than exact string.

---

## Setup — Claude Desktop

1. Make sure Qdrant is running (Engram's vector store):

   ```bash
   cd ~/BARQ/engram
   docker compose up -d
   ```

2. Open Claude Desktop's MCP config file:

   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add the engram server (merge with any existing `mcpServers` block):

   ```json
   {
     "mcpServers": {
       "engram": {
         "command": "/Users/barq/BARQ/engram/.venv/bin/python3",
         "args": ["-m", "engram_mcp.server"],
         "cwd": "/Users/barq/BARQ/engram"
       }
     }
   }
   ```

   Use the absolute path to your venv's `python3` so Claude Desktop picks up
   Engram's dependencies (mcp, qdrant-client, sentence-transformers, etc.).

4. Restart Claude Desktop. You should see "engram" in the MCP tools menu.

5. Test it: ask Claude *"use engram to find anything about servo overheating."*

---

## Setup — Cursor

Cursor reads MCP config from `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "engram": {
      "command": "/Users/barq/BARQ/engram/.venv/bin/python3",
      "args": ["-m", "engram_mcp.server"],
      "cwd": "/Users/barq/BARQ/engram"
    }
  }
}
```

Restart Cursor. Engram tools appear in the agent's tool palette.

---

## Setup — Claude Code (this CLI)

Add to `~/.claude/settings.json` (or your project's `.claude/settings.json`):

```json
{
  "mcpServers": {
    "engram": {
      "command": "/Users/barq/BARQ/engram/.venv/bin/python3",
      "args": ["-m", "engram_mcp.server"],
      "cwd": "/Users/barq/BARQ/engram"
    }
  }
}
```

---

## Try it from the command line

You can also drive the server with the official MCP inspector:

```bash
npx @modelcontextprotocol/inspector \
  /Users/barq/BARQ/engram/.venv/bin/python3 -m engram_mcp.server
```

This opens a local web UI where you can list tools and call them by hand.

---

## Suggested usage prompt for Claude

Paste this into Claude's system prompt or memory once Engram is wired up:

> You have access to the `engram_*` MCP tools, which connect to a local
> project-memory vector store. Before answering any project-specific
> question, call `engram_query` with the user's symptoms/keywords and use
> the returned chunks as authoritative context. After solving a problem,
> call `engram_write_debug` (or `_decision` / `_experiment`) so the
> resolution persists. At the end of a working session, call
> `engram_session_summary`. Do not invent project details that are not in
> the returned chunks.

---

## Troubleshooting

- **"No module named mcp"** — install dependencies into the venv:
  `python3 -m pip install -r requirements.txt`
- **"Connection refused" to Qdrant** — `docker compose up -d` first.
- **Tools missing in Claude Desktop** — confirm the absolute python path,
  restart the app (not just reload).
- **First call is slow** — sentence-transformers downloads the embedding
  model (~90 MB) on first run, then caches it.
