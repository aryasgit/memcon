# Memcon MCP Server

Wire memcon into Claude over the **Model Context Protocol**. Once connected,
Claude can:

- **Pull the matching notes** before answering — only your project's notes
  relevant to the question, not the whole on-disk record.
- **Write a fix back** as a typed note after solving a problem — so the next
  session (yours or someone else's) finds it.

No copy-paste. When you confirm a fix, Claude writes it back as a typed note
(advisory — it ships in the MCP instructions, a model may not always comply).

---

## Tools exposed

| Tool | What it does |
|---|---|
| `memcon_query(query, top_k=5, subsystem=None)` | Semantic search — returns top-K relevant chunks. |
| `memcon_ask(question, top_k=5, subsystem=None)` | Self-contained answer using Memcon's local LLM. |
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
You: "Why are requests failing under burst load?"
        ↓
Claude calls memcon_query("requests failing under burst load")
        ↓
Memcon returns top-5 chunks from past debug notes
        ↓
Claude answers from the matching notes in your project, not from scratch
        ↓
After you confirm the fix:
Claude calls memcon_write_debug(title, symptom, cause, fix, subsystem="cache")
        ↓
New typed note written to your vault (plain markdown you own) → re-ingested → searchable next session
```

Matched by meaning AND by exact filename, symbol, or error string. Only the
matching notes come back — not the entire vault.

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
         "args": ["/ABSOLUTE/PATH/TO/memcon/memcon_mcp/server.py"],
         "cwd": "/ABSOLUTE/PATH/TO/memcon"
       }
     }
   }
   ```

   Use the absolute path to your venv's `python3` so Claude Desktop picks up
   Memcon's dependencies (mcp, qdrant-client, sentence-transformers, etc.).

4. Restart Claude Desktop. "memcon" should appear in the MCP tools menu.

5. Test it: ask Claude *"use memcon to find anything about the Redis pool exhaustion."*

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

## The recall/capture reflex

The recall/capture reflex ships in the server's MCP instructions
(`MEMCON_INSTRUCTIONS` in `server.py`) — no system prompt to paste. It's
advisory; a model may not always comply.

---

## Troubleshooting

- **"No module named mcp"** — install dependencies into the venv:
  `python3 -m pip install -r requirements.txt`
- **"Connection refused" to Qdrant** — `docker compose up -d` first.
- **Tools missing in Claude Desktop** — confirm the absolute python path,
  restart the app (not just reload).
- **First call is slow** — sentence-transformers downloads the embedding
  model (~90 MB) on first run, then caches it.
