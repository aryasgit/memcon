---
tags: [design-decision]
---

# Why Qdrant not pgvector

*Decided during: v1.0*

pgvector would have meant pulling Postgres in as a hard dependency
just to serve as the vector store. The install footprint goes from
"Docker + Python" to "Docker + Postgres + Python + pgvector extension."

[[Qdrant]] is purpose-built: Rust core, fast cold start, low RAM at
memcon's scale, runs alongside [[Ollama]] in a single Docker network.
The qdrant-client Python package is well-maintained.

Chroma was the other obvious candidate — Qdrant won on the persistence
story (Chroma's defaults at the time were less mature) and on the
gRPC option for future scale.

## Related
- [[Qdrant]]
- [[Local-first]]
- [[memory.qdrant_store]]
