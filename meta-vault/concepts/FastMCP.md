---
tags: [concept]
---

# FastMCP

**Python framework for building MCP servers.**

The `mcp` package's high-level decorator API. Memcon uses it like:
```python
mcp = FastMCP("memcon")

@mcp.tool()
def memcon_query(query: str, top_k: int = 5) -> dict:
    """docstring becomes the tool description Claude reads"""
    ...
```
The docstring is the *user manual* for the LLM. Memcon's are heavily tuned.

## Related
- [[MCP Server]]
- [[Model Context Protocol (MCP)]]
- [[memcon_mcp.server]]
