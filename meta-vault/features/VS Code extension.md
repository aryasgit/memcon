---
tags: [feature]
---

# VS Code extension

Inline access to memcon from [[VS Code]] and [[Cursor]]. Three commands
+ a sidebar tree:

- `Memcon: Ask` (`Cmd+Shift+M`) — grounded answer in a markdown tab
- `Memcon: Save selection to memory` (`Cmd+Shift+S`) — captures selection
- `Memcon: Search` — raw chunks for inspection
- Activity-bar sidebar "Recent" tree with refresh + click-to-peek

## Where it lives

[[vscode extension source]] — TypeScript, compiled with `tsc`, packaged
with `vsce` as `memcon-vscode-0.1.0.vsix`.

## Distribution

Currently as a download from the landing page (`docs/install/`). Coming:
VS Code Marketplace + Open VSX (see [[v3.0 — Lives in your editor]]).

## Shipped

[[v3.0 — Lives in your editor]] MVP. [[VS Code extension shipped]] for
the moment it landed.

## Related
- [[VS Code]] · [[Cursor]]
- [[bin-memcon CLI]]
