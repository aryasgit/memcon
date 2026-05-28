---
tags: [feature, v3.1]
---

# Hybrid retrieval

[[memory.retrieve|memory.retrieve.query]] merges results from two
sources and reranks:

1. **Semantic** — [[Qdrant]] cosine similarity over [[Embeddings]]
2. **Entity** — [[Entity index]] exact / substring matches

Entity hits get a small score boost added to their semantic score. Notes
that surface in *both* searches get the strongest signal.

## Output shape

Same as the v1 semantic-only contract (so old callers keep working), plus:

- `via` — "semantic" | "entity" | "both"
- `entity_hits` — list of `{entity, kind, token}` matches

## Tunables

In [[memory.retrieve]]:
- `ENTITY_BOOST_FACTOR = 0.15` — per matched token
- `MAX_ENTITY_BOOST = 0.45` — cap
- `ENTITY_ONLY_FLOOR = 0.30` — base score for entity-only hits

## What it fixes

Pre-v3.1, asking about `servo.cpp` relied entirely on the cosine match
to that filename embedded inside other text. Often missed. Now: exact
substring of `servo.cpp` in any note's entity list = guaranteed hit.

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 3.

## Related
- [[memcon_query]] · [[memcon_ask]] benefit automatically
- [[Entity index]]
- [[Semantic search]]
- [[Qdrant]]
