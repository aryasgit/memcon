---
tags: [feature, mcp-tool, read]
---

# memcon_query

**Semantic + entity hybrid search across the vault.**

The default read tool. Pass a natural-language question; returns the top-K chunks ranked by [[Hybrid retrieval]] (semantic [[Qdrant]] + [[Entity index]] hits, merged).

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[Hybrid retrieval]]
- [[Entity index]]
- [[memory.retrieve]]
- [[Qdrant]]
- [[Sentence Transformers]]
- [[MCP Server]]
