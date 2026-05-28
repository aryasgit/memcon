---
tags: [component, ingestion]
---

# ingestion.chunker

**Per-filetype chunking strategy.**

`chunk_file(path)` dispatches: `.md` → markdown chunks, `.py`/`.ts`/etc
→ 80-line code windows, `.pdf` → page-by-page via `pypdf`. Each chunk
gets a stable `chunk_id` that downstream IDs hash on.

## Related
- [[Code ingestion]]
- [[PDF ingestion]]
- [[ingestion.ingest]]
