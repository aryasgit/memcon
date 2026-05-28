---
tags: [ui]
---

# UI v1 — Claude chat style

**Direct response to [[UI v0 — Monochrome serif]] failing.** Switched to
the [[Claude Desktop|Claude]]-style layout: textbox at the bottom,
messages scroll above, sans-serif body.

## What it kept from v0

Monochromatic palette. The chat UI never got a color accent — it
predicted the eventual [[Why monochrome only|landing-page decision]] by
several iterations.

## What it added

- Inter/Roboto-style sans body
- Bottom-anchored composer with submit-on-enter
- Side controls (clear, settings, etc.)
- Message bubbles styled like Claude's

## Where it lives

[[api.ui.html]], served by [[api.main]] at `/ui`.

## Related
- [[api.ui.html]] · [[api.main]]
- [[UI v0 — Monochrome serif]]
- [[UI v3 — Sirnik editorial final]] — landing page eventually arrived at the same place
