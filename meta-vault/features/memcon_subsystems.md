---
tags: [feature, mcp-tool, read]
---

# memcon_subsystems

**List configured subsystems + note kinds.**

Tells Claude which [[Subsystems|subsystem]] buckets exist before writing. Since v3.1, also returns the [[Note kinds|note_kinds]] list so Claude knows what types of notes it can write.

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[Subsystems]]
- [[Note kinds]]
- [[memcon.config.yaml]]
- [[MCP Server]]
