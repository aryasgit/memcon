# How memcon works — and how each claim is tested

memcon makes a few specific claims. This maps each to the code that implements
it and the test that proves it, with honest caveats. Run the proofs yourself
(needs Qdrant on `:6333`):

```bash
.venv/bin/python -m pytest tests/test_differentiators.py -v   # the differentiators
.venv/bin/python -m pytest tests/ -q                          # full suite (30 tests)
```

## 1. The closed write-loop
Claude recalls relevant notes before answering, and after you confirm a fix it
writes a typed note back — instantly searchable.
- **Code:** `memory/writer.py` (`log_debug` / `log_decision` / …), `memory/capture.py`; MCP tools in `memcon_mcp/server.py`. The recall/capture reflex ships in the server's `initialize` instructions (`MEMCON_INSTRUCTIONS`) — **advisory**, not guaranteed (a client/model can ignore it; you can always just say "save this").
- **Tested:** `tests/test_reliability.py` (writes are instant, atomic, searchable), `tests/test_search_and_stress.py` (no loss under concurrency).

## 2. Recall by meaning AND exact entity (hybrid)
Vector search (Qdrant) is fused with a SQLite inverted index over
filenames / symbols / error strings, so a literal `jwt.ts` or `EADDRINUSE`
surfaces its note regardless of cosine distance.
- **Code:** `memory/retrieve.py` (`query()` fuses both paths), `memory/entity_index.py`.
- **Works by default — no LLM required.** Entities are extracted from note
  content on every ingest by an LLM-free precision regex pass
  (`entity_index.extract_entities_from_text`, wired into `ingestion/ingest.py`).
  The optional local LLM (Ollama) adds richer entities on top of that baseline.
- **Tested:** `tests/test_differentiators.py::test_exact_entity_retrieval_surfaces_literal_token`,
  `::test_exact_entity_works_in_lean_mode_from_content_only`,
  `::test_hybrid_fusion_merges_semantic_and_entity_deduplicated`. The flagship
  `memcon_recall` also pulls exact-entity hits (`memory/recall.py`).
- **Caveat:** a note indexes its entities on its *next* ingest — run
  `memcon_reindex` once to backfill a vault that predates this.

## 3. Reciprocal back-links
A new note's `## Related` link is written *back* into each neighbor, so the
connection is symmetric on disk (debug → decision *and* decision → debug) — not
just a one-way list.
- **Code:** `memory/writer.py` `_add_reciprocal_link` (read-modify-write under a
  per-note lock, atomic write).
- **Tested:** `tests/test_differentiators.py::test_reciprocal_backlink_written_into_existing_neighbour`.
- **Caveat:** links are cosine-similarity neighbors (threshold 0.30), **not**
  semantically-typed edges; written on the background worker (eventually
  consistent) and skipped while the embedding model is still cold on a fresh
  process.

## 4. Engineering-typed notes
Eight kinds — `debug` / `decision` / `experiment` / `breakthrough` / `concept` /
`reference` / `meeting` / `session` — each with its own sections.
- **Code:** `memory/templates.py` (`ALL_KINDS`), `memory/writer.py`.

## 5. 100% local
Plain markdown on disk; embeddings via local sentence-transformers; Qdrant +
SQLite on localhost; the optional LLM via local Ollama.
- **Code:** `memcon.config.yaml`, `ingestion/embedder.py`, `memory/qdrant_store.py`.
- **Tested:** `tests/test_reliability.py` (capture keeps the raw note with no LLM).
- **Caveat:** the ~90 MB embedding model is downloaded from HuggingFace on first
  run, then cached. After that, no *project data* ever leaves your machine.

---

Honest bottom line: memcon is **not** a brand-new category — local-markdown
memory MCP servers exist (`basic-memory`), as do hosted memory layers (`mem0`,
`Letta`). The defensible difference is the *combination* above — engineering-typed,
auto-written, recalled by meaning **and** exact entity, fully local — and every
piece has a test you can run.
