---
tags: [concept]
---

# RAG

**Retrieval-Augmented Generation.**

The pattern: pull relevant context from a store, paste it into the
LLM's prompt, generate an answer grounded in that context. [[memcon_ask]]
is RAG. [[memcon_query]] is the *retrieval* half exposed as a tool so
[[Claude (Anthropic)|Claude]] can do its own augmentation. Memcon is
*selective* about being called RAG because the project is more than
that — see [[MCP Server]].

## Related
- [[memcon_ask]]
- [[memcon_query]]
- [[Semantic search]]
- [[Hybrid retrieval]]
