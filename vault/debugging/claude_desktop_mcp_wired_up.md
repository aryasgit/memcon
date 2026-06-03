---
memory_type: episodic
subsystem: version_control
tags: ['mcp', 'claude-desktop', 'cwd-resolution']
date: 2026-05-27
---

# Claude Desktop MCP wired up

## Symptom
First time wiring Memcon into Claude Desktop, vault writes failed with `[Errno 30] Read-only file system: 'vault'`.

## Cause
Claude Desktop spawns the MCP subprocess with cwd=/, so the yaml's relative `vault.path: ./vault` resolved to `/vault` (root fs, read-only).

## Fix Applied
`config.py` now absolutises `vault.path` against the directory holding `memcon.config.yaml` at config-load time, so every caller gets the real vault path (e.g. `/Users/you/memcon/vault`) regardless of cwd.

## Status
fixed
