---
tags: [feature, v3.1]
---

# Multi-pass extraction

[[memory.extractor]] runs four sequential passes against the [[Ollama|local LLM]]
to turn freeform input into structured note fields. Replaces the
single-prompt approach used in v2.0's [[memcon_capture]].

## The four passes

1. **`classify_type(text)`** → picks one of the 8 [[Note kinds]]
2. **`extract_structure(text, kind)`** → fills per-kind sections + TL;DR
   + `context_raw`, all in Ollama JSON mode for parseability
3. **`extract_entities(text)`** → files / symbols / errors / packages /
   urls / concepts → indexed in [[Entity index]]
4. **`self_critique(text, draft)`** *(optional)* → "what did you miss?"
   pass. Doubles runtime; only useful on long inputs.

## Why multiple passes

A single prompt asks too much of small local models like qwen-coder-7b.
Decomposing into focused sub-tasks (each with its own narrow schema)
boosts accuracy and lets each pass use `response_format={"type":"json_object"}`.

See [[Why multi-pass extraction]].

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 2.

## Related
- [[memcon_capture]] — the public surface
- [[memory.extractor]]
- [[Ollama]]
- [[Universal note schema]]
