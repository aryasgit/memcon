---
tags: [design-decision]
---

# Why SQLite for entity index

*Decided during: v3.1*

The [[Entity index]] is small (one row per (entity, kind, doc)),
read-heavy, and per-vault. Three options were on the table:

1. **A second [[Qdrant]] collection** — overkill; vectors are
   irrelevant for exact-match lookup.
2. **A JSON file** — works at small scale, but loading + scanning the
   whole thing per query is O(n).
3. **SQLite** — zero-dependency for Python, gives indexes, transactions,
   WAL, all the basics. File lives at `{vault}/.memcon/entities.db`
   so [[Multi-project switching]] just works.

SQLite won. Schema is two indexes + one PRIMARY KEY.

## Related
- [[Entity index]]
- [[memory.entity_index]]
- [[Multi-project switching]]
