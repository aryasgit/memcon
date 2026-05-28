---
tags: [component, memory]
---

# memory.entity_index

**SQLite inverted index of entities → notes.**

`index_note()` to write, `clear_doc()` to wipe a doc's entries,
`lookup(query)` to retrieve. Tokenizer pulls dotted paths, CamelCase,
quoted strings, URLs, error-code shapes from a freeform query.
Stopword filter to avoid generic matches.

## Related
- [[Entity index]]
- [[Hybrid retrieval]]
- [[Why SQLite for entity index]]
