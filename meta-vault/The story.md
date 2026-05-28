---
tags: [narrative]
---

# The story

In ~6 paragraphs.

## 1. The seed

Memcon began as a private project-memory backend for [[BARQ (the robot)]] —
a quadruped that generates more debugging context per session than any
single engineer can hold. [[Aryaman (aryasgit)]] wanted a way for past
debugging conversations to survive into future ones. Local. Searchable.
Not a SaaS.

## 2. Wire it into Claude

The first real version made [[Claude (Anthropic)]] the front-end. Instead
of a separate UI, [[MCP Server]] exposed memcon as a tool Claude could
call — query before answering, write after solving. That meant the user
never had to "go save this" — Claude did it as part of the conversation.
Shipped as [[v1.0 — Plug into Claude]].

## 3. Eat everything

[[v2.0 — Memory absorbs everything]] generalized the ingestion side:
[[Code ingestion]], [[PDF ingestion]], [[Git auto-ingest]],
[[memcon_capture]] (one tool for any natural-language save). The vault
stopped being notes and became a project-memory backend that any kind
of artifact could feed into.

## 4. Move into the editor

[[v3.0 — Lives in your editor]] put memcon inline in [[VS Code]] and
[[Cursor]] via [[VS Code extension]]. Ask, save, browse — all without
leaving the editor. The reflex shortened: from "I'll go look that up"
to a Cmd+Shift+M away.

## 5. Make the notes worth keeping

The fourth wave — [[v3.1 — Rich notes, hybrid recall]] — fixed something
that had been bothering the system since day one: the 4-field schema was
too thin. Notes embedded poorly because there wasn't enough prose.
The fix was [[Universal note schema]] (8 kinds), [[Multi-pass extraction]]
(four LLM passes instead of one), [[Entity index]] (keyword-exact recall),
[[Hybrid retrieval]] (merge both), and [[Auto-enrichment]] (background git
context). Notes became 3–4× as rich. Retrieval quality jumped.

## 6. What's next

[[v4.0 — Knows what it knows (planned)]] turns the passive store into
something self-aware: contradiction detection, freshness scoring, a
knowledge-graph viewer. [[v5.0 — Multimodal and shared (planned)]] goes
beyond text. [[v6.0+ — Managed option, niche depth (planned)]] is the
moonshot — only if traction makes it obvious.

## Related
- [[v1.0 — Plug into Claude]]
- [[v2.0 — Memory absorbs everything]]
- [[v3.0 — Lives in your editor]]
- [[v3.1 — Rich notes, hybrid recall]]
- [[v4.0 — Knows what it knows (planned)]]
- [[BARQ (the robot)]]
- [[Aryaman (aryasgit)]]
