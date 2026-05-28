---
tags: [design-decision]
---

# Why MCP not REST

*Decided during: v1.0*

If memcon were a REST API, the user would have to know to use it —
they'd open a UI, type a query, copy the answer back. That's friction.

With [[Model Context Protocol (MCP)]], memcon's functions are *tools*
Claude can decide to invoke autonomously. The reflex shortens to "ask
Claude" — Claude does the memory lookup as part of the answer. Memcon
disappears into the background.

The trade-off: MCP is narrower than REST (no browser clients, only
MCP-aware LLM clients). For memcon's design centre — augmenting an
LLM — that's exactly the constraint we want.

## Related
- [[MCP Server]]
- [[Model Context Protocol (MCP)]]
- [[v1.0 — Plug into Claude]]
