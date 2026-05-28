---
tags: [design-decision]
---

# Why multi-pass extraction

*Decided during: v3.1*

Small local models like qwen-coder-7b struggle with prompts that
ask too much. A single "classify + extract + entity-tag" prompt
produced inconsistent JSON.

Decomposing into focused sub-tasks (each with its own narrow schema
+ JSON mode) makes each pass simple enough to be reliable. The price
is runtime: ~30–60s instead of ~15s for a single shot. Acceptable for
a write operation.

Plus: future-proof. The optional `self_critique` pass costs nothing
to add structurally.

## Related
- [[Multi-pass extraction]]
- [[memory.extractor]]
- [[Ollama]]
- [[v3.1 — Rich notes, hybrid recall]]
