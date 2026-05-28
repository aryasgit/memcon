---
tags: [feature]
---

# Code ingestion

Walks any project, respects `.gitignore`-style exclusions, chunks source
files by 80-line windows, embeds via [[Sentence Transformers]], stores
in [[Qdrant]] keyed by file + line range.

## Where it lives

- [[scripts.ingest_code]] — the CLI entry: `python3 -m scripts.ingest_code`
- [[ingestion.chunker]] — the chunking strategy
- [[ingestion.embedder]] — the embedding wrapper
- [[ingestion.ingest]] — the upsert path

## Shipped

[[v2.0 — Memory absorbs everything]].

## Effect

Once code is ingested, asking Claude "where do we handle JWT expiry?"
returns the right file + the surrounding 80 lines, even if the keyword
"JWT expiry" doesn't literally appear in the code.

## Related
- [[PDF ingestion]]
- [[Git auto-ingest]]
- [[Semantic search]]
