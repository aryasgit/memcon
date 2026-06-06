# Memcon — Smart Import

A master prompt that turns **one brain-dump into many interlinked, typed notes** — one pass to seed an empty vault from history you already have.

`memcon_capture` takes one blurb → one note. Smart Import is the opposite: paste a
big, messy file (old notes, a chat log, a project README, a brain-dump) and the
model splits it into atomic notes, saves each as the right *kind*, and lets memcon
auto-backlink them. Run it once to seed an empty vault from history you already have.

## How to use

1. Open Claude (Desktop or Code) with the **memcon** MCP server connected.
2. Copy everything in the fenced block below.
3. Replace `<<<PASTE YOUR NOTES HERE>>>` with your backfill markdown.
4. Send it. The model creates the nodes and ends with a receipt.

> No Ollama / Docker needed for the import — the host model does the segmentation;
> only the `memcon_write_*` calls touch memcon.

---

```
You are performing a SMART IMPORT into memcon, a local memory system. Take the
SOURCE TEXT at the bottom and break it into the SMALLEST set of self-contained,
independently-recallable memories, then save each through the right memcon tool.
Quality bar: every node is something a future engineer would be glad to find on
its own, months later, out of context.

STEP 0 — LOAD CONTEXT
Call memcon_subsystems once. Every node's `subsystem` must be chosen from that
list (use "unknown" only if genuinely unclear).

STEP 1 — SEGMENT
Read the WHOLE source first. Split it into atomic memories. One node = ONE
decision, ONE bug, ONE concept, ONE experiment, ONE milestone/insight, ONE
external reference, or ONE meeting. A long session log usually yields SEVERAL
nodes — pull each decision / bug / insight out as its own node. Do not merge
unrelated ideas. Do not split one idea across nodes. Skip filler (greetings,
scaffolding, anything with no recall value).

STEP 2 — CLASSIFY each segment into exactly one kind:
  decision     → a non-obvious choice + why
                 memcon_write_decision(title, decision, reasoning, subsystem, tags)
  debug        → something broke; symptom / cause / fix
                 memcon_write_debug(title, symptom, cause, fix, status, subsystem, tags)
  concept      → a definition / mental model / system invariant
                 memcon_write_concept(title, definition, why, example, pitfalls, subsystem, tags)
  experiment   → tried X, measured Y, concluded Z
                 memcon_write_experiment(title, hypothesis, result, conclusion, subsystem, tags)
  breakthrough → an "aha" that unlocked future work
                 memcon_write_breakthrough(title, insight, background, implication, next_steps, subsystem, tags)
  reference    → an external API / spec / resource worth keeping
                 memcon_write_reference(title, summary, source, key_points, notes, subsystem, tags)
  meeting      → a sync / discussion + decisions / actions
                 memcon_write_meeting(title, notes, attendees, decisions, actions, subsystem, tags)

STEP 3 — EXTRACT LITERALLY
Fill fields ONLY with content that appears in the SOURCE. If a field isn't in the
source, leave it empty — never invent file names, error codes, symbols, or
details. Titles: short and specific ("Redis pool exhausted under load", not "A bug").

STEP 4 — AVOID DUPLICATES
Before writing a node you MAY call memcon_query with its title. If a clearly
equivalent note already exists, call memcon_update_note(filepath, content) to
append to it instead of creating a duplicate.

STEP 5 — WRITE
Call the matching memcon_write_* tool for every segment. memcon auto-creates
backlinks between related notes, so do NOT try to link them by hand. Write
foundational concepts/decisions first, then the debug/experiment nodes that
reference them (denser, more accurate links).

STEP 6 — RECEIPT
When finished, print a short table: each node's kind + title, the total count,
and one line confirming they're auto-backlinked and now searchable via
memcon_recall.

GUARDRAILS: atomic nodes · literal extraction · no fabrication · subsystem from
the list · skip anything without recall value.

SOURCE TEXT:
<<<PASTE YOUR NOTES HERE>>>
```

---

## When *not* to use it

- A single, already-focused note → use `memcon_capture` (one blurb → one note).
- Source you don't want in memory (secrets, throwaway) → don't import it; memcon
  is the source of truth and notes are plain markdown on disk.

## What you get

The import produces real `.md` files in your vault, each templated by kind and
auto-backlinked to related notes (cosine ≥ 0.30, bidirectional) — interlinked
notes you can open in Obsidian and recall against with `memcon_recall`. One pass
from empty to useful.
