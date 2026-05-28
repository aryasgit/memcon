---
tags: [concept]
---

# Sentence Transformers

**Library for sentence/paragraph embeddings.**

Memcon uses `all-MiniLM-L6-v2` — fast, 384-dim, MIT-licensed, runs
on CPU. Loaded once in [[ingestion.embedder]], reused for every
[[Code ingestion|code]] / [[PDF ingestion|PDF]] / note chunk + every query.
See [[Bespoke embedding model]] for why this is enough.

## Related
- [[Embeddings]]
- [[ingestion.embedder]]
- [[Qdrant]]
- [[Bespoke embedding model]]
