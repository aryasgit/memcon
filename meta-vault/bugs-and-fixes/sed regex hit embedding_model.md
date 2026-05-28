---
tags: [bug-fix]
---

# sed regex hit embedding_model

**`sed 's|model: ".*"|...|'` in [[install.sh]] matched substring inside `embedding_model: "..."` too.**

The original sed substitution wasn't anchored:
```
sed 's|model: ".*"|model: "qwen2.5-coder:7b"|'
```
Which matches both `model: "..."` AND `embedding_model: "..."` because
the second contains the first as a suffix.

Result: the LLM model installation worked, but `embedding_model` got
silently rewritten too — to a string that wasn't a valid Hugging Face
model name. First user to run it got HFValidationError on first ingest.

**Fix:** anchor to the line start + the exact two-space indent:
```
sed 's|^  model: ".*"|  model: "qwen2.5-coder:7b"|'
```

**Lesson:** `.*` in sed is dangerous — anchor every substitution to
line-start unless you specifically want substring matching.

## Related
- [[install.sh]]
- [[bootstrap.sh]]
