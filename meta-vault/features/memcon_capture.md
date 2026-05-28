---
tags: [feature, mcp-tool, write]
---

# memcon_capture

**DEFAULT write tool — natural-language → structured note.**

Routes any 'save this' / 'log it' / 'remember' instruction through the [[Multi-pass extraction]] pipeline. Auto-picks the [[Note kinds|kind]], extracts fields + entities, writes via [[memory.writer|log_universal]]. The tool Claude reaches for unless the user is dictating structured fields explicitly.

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
- [[Multi-pass extraction]]
- [[memory.extractor]]
- [[Note kinds]]
- [[Auto-enrichment]]
- [[v3.1 — Rich notes, hybrid recall]]
- [[MCP Server]]
