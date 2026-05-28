---
tags: [design-decision]
---

# Why Obsidian markdown

*Decided during: v1.0*

Three reasons:
1. **Portable.** A vault is a folder of `.md` files. If memcon ever
   disappeared, the user's notes are still readable in any text editor.
2. **Free graph view.** Obsidian's existing graph + backlinks UI
   becomes memcon's frontend for free.
3. **Hackable.** Users can edit notes by hand without going through
   memcon — the [[ingestion.watcher|watcher]] picks up changes and
   re-ingests.

The alternative was a proprietary store (SQLite blobs, MongoDB).
Locked-in storage = the wrong stance for a tool whose value prop is
data ownership.

## Related
- [[Obsidian]]
- [[Wikilinks]]
- [[Local-first]]
- [[ingestion.watcher]]
