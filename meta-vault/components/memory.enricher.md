---
tags: [component, memory]
---

# memory.enricher

**Background daemon for git context + see-also lines.**

`enrich_async(filepath, kind, title, related)` spawns a thread and returns
immediately. The thread re-reads the file, runs `git rev-parse HEAD` +
friends from the inferred project root, generates a `## See also` block
from each related note's TL;DR, rewrites the file, re-ingests.

## Related
- [[Auto-enrichment]]
- [[Why background enrichment]]
