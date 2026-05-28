---
tags: [ui, principle]
---

# Five rules of the editorial system

From [[DESIGN.md — the design system]] §1. Break any of them and the
look collapses.

## 1. Monochrome only
Black background, white text, a handful of grays. No accent color
anywhere — not even on the CTA. Confidence in typography replaces
color. ([[Why monochrome only]])

## 2. No bordered cards
No rounded corners. No drop shadows. No bracket-corner decorations.
Sections are demarcated by **1px lines** and negative space, never by
boxes. ([[Why no bordered cards]])

## 3. Massive display next to tiny micro-labels
The contrast is between `clamp(2.5rem, 7vw, 6rem)` Inter Tight and
`0.66rem` uppercase tracking-`.16em` labels. Mid-sized headings (h3,
h4) are rare.

## 4. Editorial multi-column grids
Default to **3 columns** (`1.1fr 1.6fr 1fr`) even for things that "want"
to be centered. Forces the eye to scan.

## 5. Different interaction per section
Hover-shift on links, accordion on step-lists, side-panel reveal on
tool walls, OS-tabs on installs, live clock in headers. Never reuse the
same pattern twice on the same page. ([[Why different interaction per section]])

## Related
- [[DESIGN.md — the design system]]
- [[UI v3 — Sirnik editorial final]]
- [[Why monochrome only]] · [[Why no bordered cards]] · [[Why different interaction per section]]
