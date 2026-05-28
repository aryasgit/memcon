---
tags: [concept]
---

# Semantic search

**Retrieval by meaning, not keywords.**

Embed the query, embed the documents, cosine-similarity-match.
What you get: "weird motor error" finds a note about "servo torque
loss" even though no keyword overlaps. What you lose: exact-string
recall (the note that literally mentions `servo.cpp`). That's why v3.1
added [[Hybrid retrieval]] alongside.

## Related
- [[Embeddings]]
- [[Hybrid retrieval]]
- [[Qdrant]]
- [[RAG]]
