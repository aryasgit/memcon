---
tags: [tool]
---

# Cursor

VS Code fork with first-class LLM integration. Memcon targets it via
two paths:

1. **MCP** — Cursor supports MCP servers natively. The [[MCP Server]]
   config that works for [[Claude Desktop]] works for Cursor too (with
   path adjustments).
2. **VS Code extension** — Cursor reads VS Code extensions natively, so
   the same `.vsix` from [[VS Code extension]] works without changes.

## Why both paths

MCP gives [[Claude (Anthropic)|Claude]] (running inside Cursor's chat)
access to memcon as tools. The VS Code extension gives the *user* direct
access via Cmd+Shift+M / Cmd+Shift+S without going through chat.

Different ergonomics for different moments.

## Related
- [[VS Code extension]] · [[VS Code]]
- [[MCP Server]] · [[Claude Desktop]]
