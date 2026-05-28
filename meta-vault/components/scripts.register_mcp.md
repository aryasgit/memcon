---
tags: [component, script]
---

# scripts.register_mcp

**Patches Claude Desktop's config.**

Idempotent. Reads the user's `claude_desktop_config.json`, adds the
`memcon` MCP server block with an absolute path to the venv's python
+ absolute path to `memcon_mcp/server.py` (NOT the `-m module` form —
that doesn't survive [[Claude Desktop ignores cwd|sandboxing]]).

## Related
- [[Claude Desktop]]
- [[MCP Server]]
- [[Claude Desktop ignores cwd]]
