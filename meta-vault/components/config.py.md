---
tags: [component, config]
---

# config.py

**Loads `memcon.config.yaml` and applies env-var overrides.**

`get_config()` is called once and cached. Critical bit: it **absolutizes**
the vault path against the config file's location so it works under the
[[cwd is slash on macOS sandbox]] case. Env vars override `vault.path`,
`memory.collection`, `llm.model` ([[Multi-project switching]]).

## Related
- [[Multi-project switching]]
- [[cwd is slash on macOS sandbox]]
- [[memcon.config.yaml]]
