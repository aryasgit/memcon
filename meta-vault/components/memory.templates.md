---
tags: [component, memory]
---

# memory.templates

**Renders v3.1 note templates.**

Exports `ALL_KINDS` (the 8 valid [[Note kinds]]), `FOLDER_FOR` (kind →
vault folder), `SECTIONS_FOR` (kind → ordered section list), and the
core `render(kind, title, fields, meta)` function. Also `make_frontmatter()`
for building the YAML block.

## Related
- [[Universal note schema]]
- [[Note kinds]]
- [[memory.writer]]
