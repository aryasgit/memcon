---
tags: [component, memory]
---

# memory.qdrant_store

**Qdrant client + helpers.**

`ensure_collection()` creates the collection on first use. `upsert_chunks()`
takes `(chunks, vectors)` and writes them with UUID-5 deterministic IDs.
`search(vec, top_k, subsystem)` returns hits with payload. `get_stats()`
for diagnostics. Uses `MEMCON_QDRANT_HOST` / `_PORT` env overrides.

## Related
- [[Qdrant]]
- [[memory.retrieve]]
- [[ingestion.ingest]]
