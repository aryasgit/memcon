---
tags: [component, script]
---

# install.sh

**The body of bootstrap.sh — does the actual work.**

Where [[sed regex hit embedding_model|the sed bug]] lived briefly. The
fix anchored the substitution to `^  model:` (line-start + two spaces).
Otherwise it would silently corrupt `embedding_model: "..."` lines too.

## Related
- [[sed regex hit embedding_model]]
- [[bootstrap.sh]]
