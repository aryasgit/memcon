---
tags: [bug-fix]
---

# cwd is slash on macOS sandbox

**[[Claude Desktop]] launches MCP servers with `cwd=/` (the root). Relative paths exploded.**

Memcon's `memcon.config.yaml` had `vault.path: ./vault` — relative
to the config file's directory.

When [[Claude Desktop]] launched the MCP server on macOS, it set `cwd=/`
because of the app sandbox. `./vault` resolved to `/vault` (read-only,
nonexistent). Every write failed with `[Errno 30] Read-only file system`.

**Fix:** in [[config.py]] `get_config()`, after loading the YAML, if
`vault.path` isn't absolute, resolve it against the config file's
directory:
```python
if vp and not Path(vp).is_absolute():
    project_root = config_path.parent.resolve()
    vault['path'] = str((project_root / vp).resolve())
```

**Lesson:** never trust CWD inside a sandboxed subprocess. Absolutize
everything at config-load time.

## Related
- [[Claude Desktop]]
- [[config.py]]
- [[Claude Desktop ignores cwd]]
