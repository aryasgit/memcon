---
tags: [feature, mcp-tool, read]
---

# memcon_timeline

**Time-bounded slice of recent notes.**

Walks the vault, returns notes with `mtime > now − N days`, newest first. Optional subsystem filter. Doesn't touch [[Qdrant]] — file mtime + frontmatter only.

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[v2.0 — Memory absorbs everything]]
- [[memcon_digest]]
- [[Subsystems]]
- [[MCP Server]]
