---
tags: [feature]
---

# bin/memcon CLI

A bash wrapper at `bin/memcon` that exposes memcon's core operations
from any directory:

```
memcon ask "what was the wrist servo fix?"
memcon query "thermal"
memcon stats
memcon recent
memcon digest
memcon save "..."
memcon serve   # start the HTTP API
memcon ui      # open the dashboard
```

## Where it lives

[[bin-memcon CLI]] file itself + delegation to the Python entry points
in [[api.main]] / [[memory.writer]] / [[memory.retrieve]].

## Shipped

[[v2.0 — Memory absorbs everything]].

## In `PATH`

Currently you run it relative to the repo. Coming in [[v3.0 — Lives in your editor]]:
`install.sh` symlinks `bin/memcon` into `/usr/local/bin` if
`MEMCON_LINK_CLI=1` is set.

## Related
- [[Multi-project switching]]
- [[api.main]]
