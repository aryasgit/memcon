---
tags: [design-decision]
---

# Why background enrichment

*Decided during: v3.1*

Write tools should return immediately to keep [[Claude (Anthropic)|Claude]]'s
loop snappy. But there are nice-to-have additions to a note that need
extra work: a `git rev-parse HEAD` call (slow if the repo is huge), and
reading neighbours to generate `## See also` lines.

Solution: kick a daemon thread after the write returns. The note is
fully valid before the thread runs — if it fails, no harm. The user
sees the polish on their next visit to the note in [[Obsidian]].

## Related
- [[Auto-enrichment]]
- [[memory.enricher]]
