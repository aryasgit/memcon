---
tags: [feature]
---

# PDF ingestion

Drop `.pdf` files into `vault/`, they get indexed page-by-page via
`pypdf`. No OCR — text-extraction PDFs only.

## Where it lives

[[ingestion.chunker]] — has a `chunk_file()` dispatcher that routes
`.pdf` to a pypdf-based extractor. [[ingestion.ingest]] handles
the rest the same way it would for markdown.

## Shipped

[[v2.0 — Memory absorbs everything]].

## Why pages, not paragraphs

Pages are the natural breakpoint readers expect. Paragraph chunking
turned out to be inconsistent across the PDFs people actually drop in
(papers, datasheets, manuals). Pages are predictable.

## Related
- [[Code ingestion]]
- [[ingestion.chunker]]
