---
tags: [concept]
---

# Model Context Protocol (MCP)

**An open protocol from Anthropic for LLMs to call tools.**

A JSON-RPC dialect that lets an LLM client (like [[Claude Desktop]],
[[Cursor]], or Claude Code) discover and invoke "tools" exposed by a
server. Servers can be local processes (stdio transport) or remote
(SSE / HTTP). Memcon ships as a stdio server — see [[MCP Server]].

Without MCP, integrating a memory store into Claude meant either a
custom client or copy-paste into the chat. With MCP, you register the
server once and Claude treats memcon's read/write functions as native
tools it can decide to use.

## Related
- [[MCP Server]]
- [[FastMCP]]
- [[Claude Desktop]]
- [[Why MCP not REST]]
