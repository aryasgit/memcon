---
tags: [ui, shipped]
---

# UI v3 — Sirnik editorial final

**The landing page as it stands.** Pure monochrome, [[Sirnik (design reference)|Sirnik]]-inspired
editorial. 1100+ lines, ~90 elements, zero bordered cards.

## Design language

- **Type:** Inter Tight (display + body), JetBrains Mono (code + labels)
- **Color:** monochrome only — 9-shade gray ladder, one green pulse on the
  live indicator
- **Grid:** signature 1.1fr / 1.6fr / 1fr 3-column for nav + philosophy row
- **No cards.** Sections are demarcated by 1px lines and typography.
- **Different micro-interaction per section** — cursor crosshair / live
  clock / accordion / hover-side-panel / OS tabs / marquee

## What landed

- 8 sections, each with its own interaction pattern
- Tool wall: hover any of 12 MCP tools → side panel updates with description
- Faux-IDE in the editor section with syntax highlight in grayscale
- Giant `MEMCON` wordmark in the footer with a vault-screenshot cut

## Codified as

[[DESIGN.md — the design system]] — extracted as a portable reference for
future projects.

## Related
- [[Five rules of the editorial system]]
- [[DESIGN.md — the design system]]
- [[Why monochrome only]] · [[Why no bordered cards]] · [[Why different interaction per section]]
- [[Sirnik landing redesign shipped]]
- [[Sirnik (design reference)]]
