---
tags: [feature, v3.1]
---

# Auto-enrichment

[[memory.enricher]] spawns a daemon thread after every write to add
two things without blocking the caller:

1. **Git context** — `git rev-parse HEAD` + branch + recently-changed
   files, patched into the note's frontmatter as a `git:` block
2. **`## See also`** — for each linked neighbour, read its TL;DR (or
   first prose line under H1) and append a bullet with the one-liner

## Why background

Write tools should return *instantly* to keep [[Claude (Anthropic)]]'s
loop snappy. Enrichment is opportunistic — if it fails, the note's still
fully valid.

## Where it looks for the project root

In order:
1. `$MEMCON_PROJECT_ROOT`
2. CWD (if not `/` — the [[cwd is slash on macOS sandbox]] case)
3. The vault's parent directory
4. The vault itself

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 4.

## Related
- [[Why background enrichment]]
- [[memory.enricher]]
- [[Auto-wikilinks on write]] — runs synchronously inside the write
