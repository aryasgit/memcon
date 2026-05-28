---
tags: [feature, v3.1]
---

# Entity index

A SQLite-backed inverted index that maps named entities (files, symbols,
errors, packages, URLs, concepts) back to the notes that mention them.

Complements [[Qdrant|vector search]]: vectors give fuzzy "this is roughly
about that," entities give exact "the note that mentions servo.cpp."
Together = [[Hybrid retrieval]].

## Schema

```
CREATE TABLE entities (
    entity     TEXT,    -- raw, case-preserved
    entity_lc  TEXT,    -- lowercase for fast lookup
    kind       TEXT,    -- files | symbols | errors | packages | urls | concepts
    doc_name   TEXT,    -- slug matching Qdrant payload doc_name
    path       TEXT,    -- absolute file path
    last_seen  TEXT,    -- ISO timestamp
    PRIMARY KEY (entity_lc, kind, doc_name)
);
```

Index at `{vault}/.memcon/entities.db`.

## Public API

`index_note()` / `clear_doc()` / `lookup()` / `stats()`. All in
[[memory.entity_index]].

## Where the entities come from

[[Multi-pass extraction]] Pass 3 — `extractor.extract_entities()`. Or, on
migration, [[scripts.migrate_to_v3_1]] uses regex fallback if Ollama isn't
available.

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 3.

## Related
- [[Why SQLite for entity index]]
- [[Hybrid retrieval]]
- [[Multi-pass extraction]]
- [[memory.entity_index]]
