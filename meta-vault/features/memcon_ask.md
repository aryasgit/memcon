---
tags: [feature, mcp-tool, read]
---

# memcon_ask

**Grounded LLM answer with citations.**

Runs [[memcon_query]] then asks the [[Ollama|local LLM]] to answer using ONLY the retrieved chunks. Cited. Slower than `query` but self-contained.

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[memcon_query]]
- [[Ollama]]
- [[api.ui.html]]
- [[RAG]]
- [[MCP Server]]
