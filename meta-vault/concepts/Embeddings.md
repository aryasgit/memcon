---
tags: [concept]
---

# Embeddings

**Dense numeric vectors that encode meaning.**

Memcon uses [[Sentence Transformers]]' `all-MiniLM-L6-v2` —
384-dimensional vectors per chunk. Stored in [[Qdrant]] with cosine
distance. Cheap (~ms per chunk on CPU), good enough for the project's
scale. Bespoke embedding models considered + rejected
([[Bespoke embedding model]]).

## Related
- [[Sentence Transformers]]
- [[Qdrant]]
- [[Semantic search]]
