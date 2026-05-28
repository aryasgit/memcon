---
tags: [feature, mcp-tool, write]
---

# memcon_session_summary

**End-of-session roll-up.**

Captures what was worked on, broken, fixed, or decided. Call near the end of a working session. In v3.1 routes through [[memory.writer|log_universal]] with kind=session.

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[memory.writer]]
- [[Note kinds]]
- [[MCP Server]]
