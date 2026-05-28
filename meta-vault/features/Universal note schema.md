---
tags: [feature, v3.1]
---

# Universal note schema

The v3.1 replacement for the pre-existing 4-field schema (title / symptom /
cause / fix). One outer shape, swappable middle per [[Note kinds|kind]].

## What "universal" means

Every note, regardless of kind, has:

- **Rich frontmatter** — `id`, `type`, `created`, `updated`, `subsystem`
  (now a list), `tags`, `status`, `confidence`, `entities` (six categories),
  `git` (commit / branch / changed_files), `linked` ([[Obsidian]] wikilinks)
- **TL;DR** — one-sentence headline
- **Per-kind middle sections** — the part that differs (Symptom / Cause /
  Fix for debug; Context / Decision / Reasoning for decision; etc.)
- **`## Context`** — verbatim conversation excerpt preserved for the
  embedder (see [[Why preserve raw context]])
- **`## Related`** — auto-generated [[Auto-wikilinks on write|wikilinks]]
- **`## See also`** — added asynchronously by [[Auto-enrichment]]

## Where it lives

[[memory.templates]] is the renderer. [[memory.writer]] is the entry point
(`log_universal(kind, title, fields, …)`).

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 1.

## Related
- [[Multi-pass extraction]] — fills these fields
- [[Note kinds]]
- [[Why universal schema]]
- [[Why preserve raw context]]
