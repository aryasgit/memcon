# Memcon — Philosophy

> **Memcon = Memory + Context.**
> A temporal-semantic debugging memory for people building things they've
> never built before.

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

**Memory + Context.** The name is the whole thesis.

- **Memory** — the *timeline*. Every fix, every debug, every decision, every
  dead end and every road taken, stored in order, as it happened.

- **Context** — the part that matters the moment you're stuck. Memcon doesn't
  just hand back "matching notes." When you hit a new problem it serves a
  **fused platter**:
  - a **similar** problem you've faced before — *(semantic)*
  - the **most recent** thing you tried against it — *(temporal)*
  - whether that attempt **worked or failed** — *(outcome)*

That fusion — *similar + recent + outcome, in one answer* — is the soul of the
product. It isn't search. It's **recall**.

---

## The two readers

The same memory is read by two very different consumers, and it stays honest
to both:

- **You, the human** — it's plain Markdown on disk. Open it in Obsidian, read
  it, edit it, see the graph, walk away with it. Never a locked black box.

- **Claude, the machine** — over MCP. It reads and writes your memory itself,
  as part of the normal conversation, and gets the fused recall handed to it
  automatically.

One memory. A human and a machine, both first-class. That duality is the line
the product holds that others don't.

---

## Who it's for

Memcon is a **safety net for builders** — the hobbyist, the new engineer, the
person setting out to build something they've never built, with no map of what
will go right and what won't.

When you're doing something for the first time, you *will* forget what you
tried. Memcon is the net under that: it remembers the path so you don't fall
through the same hole twice.

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

*Memory + Context. The road you've walked, handed back to you the moment you
need it.*
