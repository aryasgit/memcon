---
tags: [component, memory]
---

# memory.extractor

**Multi-pass LLM extraction.**

4 functions: `classify_type` / `extract_structure` / `extract_entities` /
`self_critique`. All use [[Ollama]] JSON mode. Single public entry
`extract(text, hint='auto', run_critique=False) → dict` returns the
extraction ready to feed into [[memory.writer|log_universal]].

## Related
- [[Multi-pass extraction]]
- [[memcon_capture]]
- [[Ollama]]
- [[Why multi-pass extraction]]
