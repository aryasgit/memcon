---
tags: [design-decision]
---

# Why preserve raw context

*Decided during: v3.1*

The old 4-field schema (title / symptom / cause / fix) discarded the
200-line debugging conversation that produced it. So the [[Embeddings|embedding]]
saw 80 words. Bad embeddings = bad [[Semantic search|recall]].

v3.1 added `## Context` — a verbatim excerpt (~1200 chars) preserved on
every note. The embedder finally has real prose to grip onto. Recall
quality jumps overnight when you migrate.

Trade: notes are longer on disk. Worth it.

## Related
- [[v3.1 — Rich notes, hybrid recall]]
- [[Universal note schema]]
- [[Multi-pass extraction]]
- [[Embeddings]]
