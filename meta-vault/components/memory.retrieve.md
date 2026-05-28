---
tags: [component, memory]
---

# memory.retrieve

**Hybrid query layer.**

`query(text, top_k, subsystem)` is the public entry — merges
[[memory.qdrant_store|Qdrant]] semantic hits with [[memory.entity_index|entity]] hits
and reranks. Also exposes `query_semantic()` and `query_entities()`
for callers that want one or the other in isolation.

## Related
- [[Hybrid retrieval]]
- [[memory.qdrant_store]]
- [[memory.entity_index]]
- [[Semantic search]]
