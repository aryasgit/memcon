---
tags: [milestone, v1.0]
---

# MCP server stood up

The moment [[MCP Server]] first answered a tool-call from [[Claude Desktop]].

## What it took

- Implementing 9 tools via [[FastMCP]]'s `@mcp.tool()` decorator
- Solving [[stdout pollution corrupts JSONRPC]]
- Solving [[Claude Desktop ignores cwd]]
- Solving [[cwd is slash on macOS sandbox]]
- Writing [[scripts.register_mcp]] to patch the Claude Desktop config idempotently

## Why it mattered

The MCP server is the *whole product*. Before this, memcon was just a
local memory tool you'd open separately. After this, memcon was Claude's
backend brain. The narrative changed from "another notes app" to
"memory for Claude."

## Related
- [[v1.0 — Plug into Claude]]
- [[MCP Server]] · [[Model Context Protocol (MCP)]]
- [[stdout pollution corrupts JSONRPC]] · [[Claude Desktop ignores cwd]]
