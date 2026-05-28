---
tags: [feature]
---

# Multi-project switching

Three env vars switch memcon between projects without reconfiguring:

- `MEMCON_VAULT` — vault path override
- `MEMCON_COLLECTION` — [[Qdrant]] collection name override
- `MEMCON_MODEL` — [[Ollama]] model tag override

## Where it lives

[[config.py]] — `get_config()` checks each env var and overrides the
default from `memcon.config.yaml`. The override happens at config-load
time, so all downstream modules ([[memory.writer]], [[memory.retrieve]],
[[memcon_mcp.server]]) just see the right paths.

## Shipped

[[v2.0 — Memory absorbs everything]].

## Why env vars and not multiple config files

Atomicity. You can launch memcon for a specific project with one shell
line:
```
MEMCON_VAULT=~/projects/foo MEMCON_COLLECTION=foo_memory memcon serve
```

No reload, no profile switching.

## Related
- [[config.py]]
- [[bin-memcon CLI]]
