---
tags: [milestone, v3.0]
---

# VS Code extension shipped

`memcon-vscode-0.1.0.vsix` — the first VSIX. ~9 KB compiled. Works in
both [[VS Code]] and [[Cursor]] from the same file.

## What it took

- [[vscode extension source]] in TypeScript
- Three commands (`Memcon: Ask`, `Memcon: Save selection`, `Memcon: Search`)
- One sidebar tree view ("Recent")
- HTTP client to talk to [[api.main]] on localhost
- `vsce package --no-dependencies` to build the VSIX

## Distribution

Currently a download from `docs/install/memcon-vscode-0.1.0.vsix`. The
v3.0 roadmap has Marketplace + Open VSX publishing as the next step.

## Why this changes the product

Pre-extension: the reflex was "open browser → memcon UI → query → copy
result back to my code." Three context switches.

Post-extension: `Cmd+Shift+M`, type, answer appears in a markdown tab
in the same window. The friction collapsed to a keystroke.

## Related
- [[v3.0 — Lives in your editor]]
- [[VS Code extension]] · [[vscode extension source]]
- [[VS Code]] · [[Cursor]]
