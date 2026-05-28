---
tags: [feature, mcp-tool, write]
---

# memcon_write_debug

**Structured debug note (legacy + back-compat surface).**

Title/symptom/cause/fix/status/subsystem/tags. Pre-v3.1 was the dominant write path. Now mostly used when [[memcon_capture]] would be overkill (already-structured input).

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[memcon_capture]]
- [[memory.writer]]
- [[Universal note schema]]
- [[MCP Server]]
