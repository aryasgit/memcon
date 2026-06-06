# Memcon for VS Code & Cursor

Your project's bugs and decisions, in front of Claude — ask grounded questions, save context, and browse your project's notes inline in VS Code or Cursor.

> Requires Memcon running locally. Install with:
> ```bash
> curl -fsSL https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.sh | bash
> ```

## What it does

- **Memcon: Ask** (`Cmd+Shift+M` / `Ctrl+Shift+M`) — pops an input, calls
  the local `/ask` endpoint, and opens a markdown tab with the matching
  notes (plus a composed answer when a local model is configured).
- **Memcon: Save selection to memory** (`Cmd+Shift+S` / `Ctrl+Shift+S`
  when text is selected, or right-click → *Save selection to memory*) —
  captures the selected code along with the file path and an optional
  note, into `vault/decisions/session_<timestamp>.md`. Auto-ingested.
- **Recent sidebar** — activity-bar tree showing the N most recently
  touched notes in your vault. Click to open the full markdown in a
  preview tab.
- **Memcon: Search (raw chunks)** — semantic search returning top-K
  chunks with score, subsystem, memory type, and source.
- **Memcon: Open dashboard** — opens `localhost:8000/ui` in your browser.

Works in both VS Code and Cursor (Cursor reads VS Code extensions
natively).

## Install

### Option A — load from VSIX (recommended while in beta)

```bash
cd vscode
npm install
npm run compile
npx @vscode/vsce package --no-dependencies
# → produces memcon-vscode-0.1.0.vsix
```

Then in VS Code / Cursor:

1. `Cmd+Shift+P` → **Extensions: Install from VSIX…**
2. Pick `vscode/memcon-vscode-0.1.0.vsix`
3. Reload window

### Option B — dev mode (for hacking on the extension)

```bash
cd vscode
npm install
code .       # or: cursor .
```

In the new editor window, press `F5` to launch an Extension Development
Host with Memcon loaded.

### Option C — marketplace

Marketplace publish is planned (see [ROADMAP](../ROADMAP.md)).

## Configuration

| Setting | Default | What |
|---|---|---|
| `memcon.apiUrl` | `http://localhost:8000` | Base URL of the local Memcon API |
| `memcon.topK` | `5` | How many chunks to retrieve per query |
| `memcon.recentLimit` | `15` | Notes shown in the Recent sidebar |

## Troubleshooting

**"Cannot reach Memcon"** — the local API isn't running. Start it:
```bash
cd ~/memcon && ./start.sh
```

**Cmd+Shift+S conflicts with Save As** — change the keybinding in
*Code → Preferences → Keyboard Shortcuts*, search for `memcon`.

**Sidebar shows "api offline"** — check `memcon.apiUrl` matches where
your Memcon is actually running (still `localhost:8000` by default, even
with `docker-compose.full.yml`).

## What's next

See the main [Memcon ROADMAP](../ROADMAP.md) for planned features (code
lens, hover provider, status-bar widget, direct `memcon_capture`).

## License

MIT — same as Memcon proper.
