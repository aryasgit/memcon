---
tags: [feature]
---

# Git auto-ingest

Installs a `post-commit` hook so every commit message + diff summary
becomes searchable memory automatically.

## Where it lives

- [[scripts.ingest_git]] — runs after each commit
- `scripts/install_git_hook.sh` — the installer

## Shipped

[[v2.0 — Memory absorbs everything]].

## What gets stored

For each commit: SHA, message, author, file list, +/-LOC. Stored as a
small markdown chunk under `vault/git/`. Embeddings on the message let
queries like "when did we add the JWT middleware" surface the relevant
commit.

## Related
- [[Code ingestion]]
- [[v2.0 — Memory absorbs everything]]
