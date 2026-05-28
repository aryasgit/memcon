---
tags: [tool]
---

# Claude Desktop

Anthropic's desktop app for [[Claude (Anthropic)|Claude]]. macOS, Windows,
Linux. The first and primary client memcon targets via [[MCP Server]].

## Quirks that shaped memcon

- [[cwd is slash on macOS sandbox]] — CWD is `/` because of the app sandbox
- [[Claude Desktop ignores cwd]] — even with `cwd` set in config, it
  ignores it, breaking `python3 -m module` imports
- [[stdout pollution corrupts JSONRPC]] — any `print()` in a tool function
  shows up as "Server disconnected" in the UI

[[scripts.register_mcp]] handles the config patching idempotently.

## Where its config lives

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Related
- [[MCP Server]] · [[scripts.register_mcp]]
- [[Claude (Anthropic)]]
- [[cwd is slash on macOS sandbox]] · [[Claude Desktop ignores cwd]]
