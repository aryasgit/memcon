---
tags: [concept]
---

# Subsystems

**Soft-constrained tags for grouping notes by area.**

Pre-v3.1 was a strict list from `memcon.config.yaml` (servo / imu /
gait / power / etc. — BARQ-shaped). v3.1 made it optional: if the
config's `subsystems:` list is empty, memcon accepts any free-form
string. The [[Multi-pass extraction|extractor]] still uses the list as
a soft hint to the [[Ollama|LLM]] when present.

## Related
- [[memcon.config.yaml]]
- [[memcon_subsystems]]
- [[BARQ (the robot)]]
