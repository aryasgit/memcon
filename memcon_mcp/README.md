# Memcon MCP Server

Turn Memcon into a **Model Context Protocol** backend for Claude. Once
connected, Claude can:

- **Auto-query** Memcon before answering — pulls only the chunks relevant to
  the question (not the whole memory).
- **Auto-write** debug sessions, decisions, and experiments after solving a
  problem — so the next session (yours or someone else's) finds it.

No copy-paste. No manual note-taking. The vault grows itself while you work.

---

## Tools exposed

| Tool | What it does |
|---|---|
| `memcon_query(query, top_k=5, subsystem=None)` | Semantic search — returns top-K relevant chunks. The hashmap lookup. |
| `memcon_ask(question, top_k=5, subsystem=None)` | Self-contained answer using Memcon's local LLM. Prefer `memcon_query` if the calling LLM (you) wants raw context. |
| `memcon_write_debug(title, symptom, cause, fix, status, subsystem, tags)` | Save a debugging session. |
| `memcon_write_decision(title, decision, reasoning, subsystem, tags)` | Save an engineering decision. |
| `memcon_write_experiment(title, hypothesis, result, conclusion, subsystem, tags)` | Save an experiment. |
| `memcon_session_summary(summary, subsystem)` | End-of-session summary auto-save. |
| `memcon_update_note(filepath, content)` | Append findings to an existing note. |
| `memcon_stats()` | Chunk count, project, domain. |
| `memcon_subsystems()` | List configured subsystems and memory types. |

---

## How the loop works

```
You: "Why is the RR wrist overheating?"
        ↓
Claude calls memcon_query("RR wrist overheating servo")
        ↓
Memcon returns top-5 chunks from past debug notes
        ↓
Claude answers grounded in YOUR project history (not hallucinated)
        ↓
After you confirm the fix:
Claude calls memcon_write_debug(title, symptom, cause, fix, subsystem="servo")
        ↓
New note saved into the Obsidian vault → re-ingested → searchable next session
```

The "hashmap" framing: each `memcon_query` call is a key lookup against
semantic-similarity buckets. Only the matching chunks come back — not the
entire vault. Cheap, fast, and keyed by meaning rather than exact string.

---

## Setup — Claude Desktop

1. Make sure Qdrant is running (Memcon's vector store):

   ```bash
   cd ~/memcon
   docker compose up -d
   ```

2. Open Claude Desktop's MCP config file:

   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add the memcon server (merge with any existing `mcpServers` block):

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

   Use the absolute path to your venv's `python3` so Claude Desktop picks up
   Memcon's dependencies (mcp, qdrant-client, sentence-transformers, etc.).

4. Restart Claude Desktop. "memcon" should appear in the MCP tools menu.

5. Test it: ask Claude *"use memcon to find anything about servo overheating."*

---

## Setup — Cursor

Cursor reads MCP config from `~/.cursor/mcp.json`:

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

Restart Cursor. Memcon tools appear in the agent's tool palette.

---

## Setup — Claude Code (this CLI)

Add to `~/.claude/settings.json` (or your project's `.claude/settings.json`):

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

---

## Try it from the command line

You can also drive the server with the official MCP inspector:

```bash
npx @modelcontextprotocol/inspector \
  /ABSOLUTE/PATH/TO/memcon/.venv/bin/python3 -m memcon_mcp.server
```

This opens a local web UI where you can list tools and call them by hand.

---

## Suggested usage prompt for Claude

Paste this into Claude's system prompt or memory once Memcon is wired up:

> You have access to the `memcon_*` MCP tools, which connect to a local
> project-memory vector store. Before answering any project-specific
> question, call `memcon_query` with the user's symptoms/keywords and use
> the returned chunks as authoritative context. After solving a problem,
> call `memcon_write_debug` (or `_decision` / `_experiment`) so the
> resolution persists. At the end of a working session, call
> `memcon_session_summary`. Do not invent project details that are not in
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
