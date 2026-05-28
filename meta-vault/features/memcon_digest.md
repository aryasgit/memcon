---
tags: [feature, mcp-tool, read]
---

# memcon_digest

**LLM-generated digest of the last N days.**

Reads recent notes (cap each to 3000 chars), feeds them to the [[Ollama|local LLM]], produces Themes / Wins / Open items / Worth revisiting. Great for Monday morning.

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[memcon_timeline]]
- [[Ollama]]
- [[v2.0 — Memory absorbs everything]]
- [[MCP Server]]
