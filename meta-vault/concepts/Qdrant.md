---
tags: [concept]
---

# Qdrant

**The vector database memcon uses.**

Open-source, Rust-core, runs in Docker on `:6333`. Memcon writes to
collection `memcon_memory` (configurable via `MEMCON_COLLECTION` —
see [[Multi-project switching]]). Picked over alternatives for the
[[Why Qdrant not pgvector|local-first reasons documented separately]].

## Related
- [[Why Qdrant not pgvector]]
- [[memory.qdrant_store]]
- [[Embeddings]]
- [[Local-first]]
