---
tags: [concept]
---

# Ollama

**Local LLM runtime memcon talks to.**

OpenAI-compatible HTTP server on `:11434`. Memcon talks to it via
the `openai` Python client with `base_url=http://localhost:11434/v1`.
Models tier from `llama3.2:1b` (1.3 GB RAM) up to `qwen2.5-coder:32b`
(20 GB) — installer picks based on detected RAM. Used by
[[memcon_ask]], [[memcon_digest]], and the four passes of
[[Multi-pass extraction]].

## Related
- [[memory.extractor]]
- [[memcon_ask]]
- [[Local-first]]
- [[Why local LLM not cloud]]
