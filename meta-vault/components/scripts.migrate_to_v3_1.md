---
tags: [component, script]
---

# scripts.migrate_to_v3_1

**Backfills legacy notes into v3.1 schema.**

Walks the vault, parses old frontmatter + body, infers kind from
folder name + memory_type, lifts old `## Heading` sections into v3.1
field names, runs entity extraction (LLM or regex), re-ingests.
Idempotent, backed-up-by-default, dry-run mode.

## Related
- [[v3.1 — Rich notes, hybrid recall]]
- [[Universal note schema]]
- [[Entity index]]
- [[Multi-pass extraction]]
