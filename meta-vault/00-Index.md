---
tags: [index]
---

# Index

Complete map of every note in this vault, grouped by category.

## Versions
- [[v1.0 — Plug into Claude]]
- [[v2.0 — Memory absorbs everything]]
- [[v3.0 — Lives in your editor]]
- [[v3.1 — Rich notes, hybrid recall]]
- [[v4.0 — Knows what it knows (planned)]]
- [[v5.0 — Multimodal and shared (planned)]]
- [[v6.0+ — Managed option, niche depth (planned)]]

## Features
- [[MCP Server]]
- [[memcon_capture]] · [[memcon_query]] · [[memcon_ask]]
- [[memcon_write_debug]] · [[memcon_write_decision]] · [[memcon_write_experiment]]
- [[memcon_write_concept]] · [[memcon_write_reference]] · [[memcon_write_meeting]] · [[memcon_write_breakthrough]]
- [[memcon_session_summary]] · [[memcon_update_note]]
- [[memcon_timeline]] · [[memcon_digest]]
- [[memcon_stats]] · [[memcon_subsystems]]
- [[Auto-wikilinks on write]]
- [[Code ingestion]] · [[PDF ingestion]] · [[Git auto-ingest]]
- [[Multi-project switching]]
- [[VS Code extension]] · [[bin-memcon CLI]]
- [[Universal note schema]] · [[Multi-pass extraction]]
- [[Entity index]] · [[Hybrid retrieval]] · [[Auto-enrichment]]

## Components
- [[config.py]]
- [[memory.templates]] · [[memory.writer]] · [[memory.extractor]]
- [[memory.entity_index]] · [[memory.enricher]]
- [[memory.retrieve]] · [[memory.qdrant_store]]
- [[memcon_mcp.server]]
- [[ingestion.ingest]] · [[ingestion.chunker]] · [[ingestion.embedder]] · [[ingestion.watcher]]
- [[api.main]] · [[api.ui.html]]
- [[scripts.register_mcp]] · [[scripts.migrate_to_v3_1]] · [[scripts.ingest_code]] · [[scripts.ingest_git]]
- [[bootstrap.sh]] · [[bootstrap.ps1]] · [[install.sh]]
- [[vscode extension source]]

## Concepts
- [[Model Context Protocol (MCP)]]
- [[Semantic search]] · [[Embeddings]] · [[Hybrid retrieval]]
- [[Qdrant]] · [[Ollama]] · [[FastMCP]] · [[Sentence Transformers]]
- [[Obsidian]] · [[Wikilinks]]
- [[Local-first]] · [[RAG]]
- [[Note kinds]] · [[Subsystems]]

## Design Decisions
- [[Why MCP not REST]] · [[Why Qdrant not pgvector]]
- [[Why local LLM not cloud]] · [[Why Obsidian markdown]]
- [[Why monochrome only]] · [[Why no bordered cards]] · [[Why different interaction per section]]
- [[Why preserve raw context]] · [[Why multi-pass extraction]]
- [[Why SQLite for entity index]] · [[Why background enrichment]]
- [[Why universal schema]] · [[Why MIT licensed]]

## UI
- [[UI v0 — Monochrome serif]]
- [[UI v1 — Claude chat style]]
- [[UI v2 — Audi-Sirnik red]]
- [[UI v3 — Sirnik editorial final]]
- [[DESIGN.md — the design system]]
- [[Five rules of the editorial system]]

## Bugs and Fixes
- [[sed regex hit embedding_model]]
- [[openai missing from requirements]]
- [[cwd is slash on macOS sandbox]]
- [[stdout pollution corrupts JSONRPC]]
- [[Claude Desktop ignores cwd]]
- [[HTTP download lost +x bit]]
- [[Anchor link blue color leak]]

## Milestones
- [[MCP server stood up]]
- [[Engram renamed to Memcon]]
- [[v1.0 tagged]] · [[v2.0 tagged]]
- [[VS Code extension shipped]]
- [[Sirnik landing redesign shipped]]
- [[Design system extracted]]
- [[v3.1 layers landed]]

## People and Places
- [[Aryaman (aryasgit)]] · [[BARQ (the robot)]]
- [[Claude (Anthropic)]] · [[Claude Desktop]] · [[Cursor]] · [[VS Code]]
- [[Sirnik (design reference)]]

## Rejected Ideas
- [[SaaS-first version]]
- [[Telemetry phone-home]]
- [[Ads in dashboard]]
- [[Paid pro tier]]
- [[Bespoke embedding model]]
