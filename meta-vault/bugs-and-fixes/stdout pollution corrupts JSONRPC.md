---
tags: [bug-fix]
---

# stdout pollution corrupts JSONRPC

**Various modules used `print()` for logging. MCP stdio = stdout for JSONRPC. Print → corruption.**

[[ingestion.embedder]], [[ingestion.chunker]], [[ingestion.ingest]],
[[memory.qdrant_store]] all had `print()` calls scattered for diagnostics.

Worked fine via the HTTP API ([[api.main]]). Catastrophic via MCP:
every print interleaved into the JSONRPC stream → Claude Desktop showed
"Server disconnected" within seconds of any operation.

**Fix:** redirect every `print()` to stderr via `file=sys.stderr`. MCP
servers must keep stdout *pristine* for protocol messages only.

**Lesson:** the moment a process is invoked over stdio for an RPC, every
non-protocol byte on stdout is a bug. Even legitimate logs.

## Related
- [[MCP Server]]
- [[Claude Desktop]]
- [[ingestion.ingest]]
