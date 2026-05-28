---
tags: [feature]
---

# Auto-wikilinks on write

Every new note gets an auto-generated `## Related` section with Obsidian
[[Wikilinks]] pointing to the top-3 semantically-similar existing notes
in the vault.

## Where it lives

[[memory.writer]] — `_find_related(query_text, exclude_doc)` runs a
semantic search via [[memory.retrieve]] *before* writing the note, then
splices the resulting wikilinks into the body.

## Why before, not after

Because if the note were written first and *then* queried, it would
match itself (high cosine similarity). Pre-write search is cleaner.

## Shipped

[[v1.0 — Plug into Claude]].

## Related
- [[Obsidian]]
- [[Wikilinks]]
- [[memory.writer]]
- [[Auto-enrichment]] — adds a `## See also` section with one-liner
  summaries on top of this
