---
tags: [feature, mcp-tool, read]
---

# memcon_stats

**Vault diagnostics: chunk count, project info, entity index size.**

Cheap probe. Returns total chunks in [[Qdrant]], the project name, and (since [[v3.1 — Rich notes, hybrid recall|v3.1]]) the [[Entity index]] stats.

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[Entity index]]
- [[Qdrant]]
- [[memory.qdrant_store]]
- [[MCP Server]]
