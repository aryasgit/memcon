---
tags: [component, ingestion]
---

# ingestion.ingest

**Top-level `ingest_file(path)`.**

Calls [[ingestion.chunker]] to split, [[ingestion.embedder]] to vectorise,
[[memory.qdrant_store|qdrant_store.upsert_chunks]] to store. Idempotent
thanks to deterministic UUID-5 IDs.

## Related
- [[ingestion.chunker]]
- [[ingestion.embedder]]
- [[memory.qdrant_store]]
