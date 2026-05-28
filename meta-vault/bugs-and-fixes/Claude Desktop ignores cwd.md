---
tags: [bug-fix]
---

# Claude Desktop ignores cwd

**Even when the MCP config specified `cwd` + `env.PYTHONPATH`, Claude Desktop ignored both. `-m module` form broke.**

Initial MCP config used the standard `python3 -m memcon_mcp.server`
form, with `cwd: /Users/barq/BARQ/engram` and
`env.PYTHONPATH: /Users/barq/BARQ/engram` to make the module import work.

[[Claude Desktop]] silently ignored both. Got `ModuleNotFoundError: No
module named 'memcon_mcp'`.

**Fix:** changed the config to pass an absolute *script path* instead:
```json
{
  "command": "/abs/.venv/bin/python3",
  "args": ["/abs/memcon_mcp/server.py"]
}
```
Python auto-adds the script's directory to `sys.path`, so relative
imports in `server.py` work without `cwd` or `PYTHONPATH`.

The script itself has `sys.path.insert(0, '..')` at the top to find
the project root.

**Lesson:** when an MCP client misbehaves, ditch `cwd` and `env` —
absolute paths are the only thing you can trust.

## Related
- [[Claude Desktop]]
- [[scripts.register_mcp]]
- [[MCP Server]]
