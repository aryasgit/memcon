---
tags: [bug-fix]
---

# openai missing from requirements

**[[api.main]] and [[memcon_mcp.server]] both `from openai import OpenAI`, but `openai` wasn't in requirements.txt.**

Both modules use the `openai` Python client to talk to
[[Ollama]] (which exposes an OpenAI-compatible API). Worked locally
during development because it was installed for unrelated reasons.

When the first external user installed memcon fresh: `ModuleNotFoundError:
No module named 'openai'`.

**Fix:** add `openai==2.38.0` to `requirements.txt`. Pin to a known-good
version because the OpenAI client breaks compat often.

**Lesson:** transitive deps that "happen to be there" on the dev's
machine are landmines. Audit imports against requirements before each
external release.

## Related
- [[api.main]]
- [[memcon_mcp.server]]
- [[Ollama]]
