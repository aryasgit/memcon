---
tags: [component, script]
---

# scripts.ingest_git

**Ingest the most recent commit (called by post-commit hook).**

Reads `git log -1` for SHA/message/author/files, writes a tiny
markdown chunk under `vault/git/`, [[ingestion.ingest|ingests]] it.

## Related
- [[Git auto-ingest]]
- [[ingestion.ingest]]
