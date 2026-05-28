---
tags: [feature, core]
---

# MCP Server

The single most important component of memcon. Implements the
[[Model Context Protocol (MCP)]] over stdio so [[Claude (Anthropic)]]
(running in [[Claude Desktop]] / [[Cursor]] / Claude Code) can call
memcon as a set of tools without HTTP, without auth, without a network.

**Module:** [[memcon_mcp.server]]
**Framework:** [[FastMCP]]
**Transport:** stdio JSON-RPC

## The 16 tools (at v3.1)

**Read:**
[[memcon_query]] · [[memcon_ask]] · [[memcon_timeline]] · [[memcon_digest]] ·
[[memcon_stats]] · [[memcon_subsystems]]

**Write:**
[[memcon_capture]] (preferred) · [[memcon_write_debug]] ·
[[memcon_write_decision]] · [[memcon_write_experiment]] ·
[[memcon_write_concept]] · [[memcon_write_reference]] ·
[[memcon_write_meeting]] · [[memcon_write_breakthrough]] ·
[[memcon_session_summary]] · [[memcon_update_note]]

## Why MCP and not a REST API

[[Why MCP not REST]] has the long answer. Short answer: when Claude can
call memcon as a *tool*, it decides when to query without any UI prompting.
That's the whole product — invisible memory.

## Related
- [[v1.0 — Plug into Claude]]
- [[MCP server stood up]]
- [[scripts.register_mcp]]
- [[Why MCP not REST]]
