---
tags: [ui, reverted]
---

# UI v2 — Audi-Sirnik red

**A detour.** The landing page got a hot red (`#ED2939`) accent — Audi F1
inspired — with Anton display type, "cluttered but pretty" editorial
density.

## Why it was tried

> "honestly this one particular shade of red along with black and white
> would look very poppy"
> — [[Aryaman (aryasgit)]]

Density of information per viewport, treated like a broadsheet. Red as
the eye-catching accent on the brand wordmark + key CTAs.

## Why it was reverted

It looked striking. But the red kept fighting with the typography for
attention. The "MEMCON." headline read as red-first, word-second. The
typography lost.

## What replaced it

Reverted via `git reset --hard e1c46e8` back to the pre-redesign state,
then a full re-redesign as [[UI v3 — Sirnik editorial final]] — same
density, pure monochrome.

## Related
- [[UI v3 — Sirnik editorial final]]
- [[Why monochrome only]]
- [[Sirnik (design reference)]]
