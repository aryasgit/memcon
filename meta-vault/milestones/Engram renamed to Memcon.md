---
tags: [milestone, v1.0]
---

# Engram renamed to Memcon

The project was originally called **Engram** (a neuroscience term for a
memory trace). The user renamed it to **Memcon** (short for "Memory
Context") mid-v1 development.

## Why the rename

> "rename the whole of project to Memcon as in Memory Context"
> — [[Aryaman (aryasgit)]]

Engram was poetic but unsearchable (lots of unrelated neuroscience
literature). Memcon was distinctive, said what it does, and tied
naturally to [[Model Context Protocol (MCP)]] — memory + context.

## What it touched

Everything. The project name. The Python package (`memcon_mcp/`). The
Qdrant collection (`memcon_memory`). All env vars (`MEMCON_VAULT`,
`MEMCON_COLLECTION`, `MEMCON_MODEL`). The CLI (`bin/memcon`). The MCP
tool prefix (every tool went from `engram_*` → `memcon_*`).

The git remote also moved: `aryasgit/engram` → `aryasgit/memcon`.
GitHub still serves a redirect.

## Related
- [[v1.0 — Plug into Claude]]
- [[MCP Server]]
- [[Model Context Protocol (MCP)]]
