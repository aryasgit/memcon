---
tags: [design-decision]
---

# Why local LLM not cloud

*Decided during: v1.0*

The whole product is "your project's memory never leaves your
machine." If the LLM is cloud — OpenAI, Anthropic, anywhere — then
every query sends your project's context (the retrieved chunks) to a
third party. The local-first promise dies.

[[Ollama]] keeps everything local. Slower than GPT-4, but for
extraction tasks ([[Multi-pass extraction]]) qwen-coder-7b is plenty.
For [[memcon_ask]]'s grounded answers, it's fine — most of the value
is in the retrieved context, not the model's prose.

## Related
- [[Local-first]]
- [[Ollama]]
- [[SaaS-first version]]
