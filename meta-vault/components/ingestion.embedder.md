---
tags: [component, ingestion]
---

# ingestion.embedder

**Sentence-transformers wrapper.**

One function: `embed(texts) → list[list[float]]`. Loads
`all-MiniLM-L6-v2` once, runs batches. 384-dim output — matches the
[[Qdrant]] collection dim. See [[Bespoke embedding model]] for why we
didn't go custom.

## Related
- [[Sentence Transformers]]
- [[Embeddings]]
- [[Qdrant]]
- [[Bespoke embedding model]]
