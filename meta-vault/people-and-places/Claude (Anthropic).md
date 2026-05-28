---
tags: [person, tool]
---

# Claude (Anthropic)

The LLM memcon is built to augment. Specifically the Claude models
running inside [[Claude Desktop]], [[Cursor]], Claude Code, and the
Claude API.

## Why Claude specifically

Two reasons:
1. [[Model Context Protocol (MCP)]] is Anthropic's protocol. The most
   mature MCP support is in Claude's clients.
2. Claude's instruction-following on tool-call docstrings is good
   enough that memcon's heavily-tuned tool descriptions ([[MCP Server]])
   reliably steer it toward the right tool at the right time.

## Memcon as a Claude extension

The product framing is "Memory for Claude." Could it work with other
LLMs? Yes — the [[Ollama|local LLM]] used internally for extraction is
already model-agnostic. Adding REST/HTTP transports alongside the MCP
stdio one would let other clients in. That's [[v6.0+ — Managed option, niche depth (planned)|v6+]] territory.

## Related
- [[MCP Server]]
- [[Model Context Protocol (MCP)]]
- [[Claude Desktop]] · [[Cursor]]
