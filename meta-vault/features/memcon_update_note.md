---
tags: [feature, mcp-tool, write]
---

# memcon_update_note

**Append findings to an existing note.**

For when a previously-open debug session gets resolved. Takes the path returned by an earlier write tool, appends a timestamped update block, re-ingests into [[Qdrant]].

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[memory.writer]]
- [[ingestion.ingest]]
- [[MCP Server]]
