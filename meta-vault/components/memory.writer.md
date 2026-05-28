---
tags: [component, memory]
---

# memory.writer

**Canonical write API.**

`log_universal(kind, title, fields, …)` is the entry. Back-compat
wrappers: `log_debug` / `log_decision` / `log_experiment` /
`log_concept` / `log_reference` / `log_meeting` / `log_breakthrough` /
`summarise_session`. All route through `log_universal` which:
1. resolves [[Auto-wikilinks on write|related neighbours]],
2. renders via [[memory.templates|templates.render]],
3. writes to `{vault}/{folder}/{slug}.md`,
4. ingests into [[Qdrant]] via [[ingestion.ingest]],
5. updates the [[Entity index]],
6. spawns [[memory.enricher|enrich_async]] for background polish.

## Related
- [[Universal note schema]]
- [[memory.templates]]
- [[Auto-enrichment]]
- [[Auto-wikilinks on write]]
- [[Entity index]]
