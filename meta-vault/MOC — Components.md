---
tags: [moc]
---

# MOC — Components

Every Python module and important file, grouped by layer.

## Configuration
- [[config.py]]
- [[memcon.config.yaml]]

## Memory layer (writes + reads)
- [[memory.templates]] — note templates (v3.1)
- [[memory.writer]] — log_universal + back-compat wrappers
- [[memory.extractor]] — 4-pass LLM extraction (v3.1)
- [[memory.entity_index]] — SQLite inverted index (v3.1)
- [[memory.enricher]] — background git + see-also (v3.1)
- [[memory.retrieve]] — hybrid query (v3.1)
- [[memory.qdrant_store]] — Qdrant client wrapper

## Ingestion pipeline
- [[ingestion.ingest]] — top-level ingest_file
- [[ingestion.chunker]] — markdown / code / pdf chunkers
- [[ingestion.embedder]] — sentence-transformers wrapper
- [[ingestion.watcher]] — vault file-watcher

## MCP surface
- [[memcon_mcp.server]] — 16 MCP tools registered via FastMCP

## HTTP surface
- [[api.main]] — FastAPI app at :8000
- [[api.ui.html]] — chat-style dashboard

## Scripts
- [[scripts.register_mcp]] — patch Claude Desktop config
- [[scripts.migrate_to_v3_1]] — backfill old notes
- [[scripts.ingest_code]] · [[scripts.ingest_git]]
- [[bootstrap.sh]] · [[bootstrap.ps1]] · [[install.sh]]

## Editor + CLI
- [[vscode extension source]]
- [[bin-memcon CLI]]

## Related
- [[MOC — Features]]
- [[MOC — Versions]]
