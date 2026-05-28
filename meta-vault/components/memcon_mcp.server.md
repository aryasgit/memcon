---
tags: [component, mcp]
---

# memcon_mcp.server

**The MCP stdio server. 16 tools registered.**

Built on [[FastMCP]]. Each tool is a `@mcp.tool()`-decorated function
with a docstring that becomes the tool's description (which Claude reads
to decide when to call it). The docstrings are heavily tuned — they're
the API surface for an LLM, not for humans.

## Related
- [[MCP Server]]
- [[FastMCP]]
- [[Model Context Protocol (MCP)]]
