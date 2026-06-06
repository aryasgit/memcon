# Memcon — Philosophy

> **Claude already knows what you fixed last time.**
> memcon keeps your project's bugs, decisions, and dead ends on disk — so
> Claude pulls the few that match before it answers. Built for engineers.

---

## Why it exists

Memcon was born from one specific, repeated pain while building **BARQ**, an
autonomous quadruped robot:

You make a fix. You keep building. Weeks pass. Then you hit a wall — and the
assistant you're working with has *zero* memory of what happened. What you
tried at that node. Which road you already walked down and abandoned. Whether
the thing you're about to attempt is the same thing that failed a month ago.

So you re-debug what you already solved. Or you repeat a mistake you already
paid for. The knowledge existed — it was just *gone*, out of the conversation
and out of reach.

Memcon is the fix for that.

---

## What it is

An on-disk record an engineer keeps for their own codebase, so Claude works
from what the project already learned.

You write fixes, debugs, decisions, and dead ends as plain markdown notes.
Before answering, Claude pulls the few notes that match your question — by
meaning *and* by exact filename, symbol, or error string. Recall leans toward
your most recent attempt and flags each note resolved, open, or failed — so a
past failure warns you and a past fix answers you.

It surfaces the handful of notes that matter, then Claude answers from them.

---

## The two readers

The same memory is read by two very different consumers, and it stays honest
to both:

- **You, the human** — it's plain Markdown on disk. Open it in Obsidian, read
  it, edit it, see the graph, walk away with it. Never a locked black box.

- **Claude, the machine** — over MCP. It reads and writes your notes itself,
  as part of the normal conversation, and pulls the matching notes when it's
  wired in (advisory — a model may not always comply).

One record. A human and a machine, both first-class. The combination is the
point: typed engineering notes, a write-back loop, recall by meaning and exact
entity, fully local.

---

## Who it's for

Working engineers — the hobbyist, the new hire, anyone building something for
the first time. You *will* forget what you tried; memcon keeps it on disk so
Claude can hand the relevant slice back when you need it.

---

## Principles

1. **It's a timeline, not a pile.** Time and outcome are first-class — not
   metadata bolted onto a flat bag of notes.
2. **Your data is yours, in the open.** Markdown on disk. No proprietary
   store, no lock-in, nothing to migrate out of.
3. **Seamless by default.** Someone who just wants memory shouldn't have to
   fight a 20-step install. Full local control and maximum privacy are
   available — as an *opt-in*, never the toll at the door.
4. **Transparent to human and machine alike.** If only one of them can read
   it, it's the wrong design.

---

## What it is not

- **Not a notebook.** It's time-aware and outcome-aware, not a flat list.
- **Not a cloud service.** Your engineering history doesn't leave your machine
  unless you decide it should.
- **Not a token-saving trick.** The value is *persistence and recall* — the
  fact that the memory is still there, and that it hands you the right slice of
  the past exactly when you need it.

---

*The road you've walked, handed back to you the moment you need it.*
