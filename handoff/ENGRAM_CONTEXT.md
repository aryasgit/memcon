# Engram — Unified Conversation Context

> Paste this entire file as the first message in a fresh Claude Code
> conversation. The goal of that conversation: take the four apps
> (Memcon, Memshare, Thymeline, Invpart) and unify them under the
> **Engram** umbrella brand. Marketing narrative goal, not technical
> integration.

---

## 1. Who you're talking to

**Aryaman (aryasgit)** — solo engineer. Builds [BARQ](https://github.com/aryasgit/barq),
an autonomous quadruped robot. While building BARQ he hit gaps in
existing engineering project management tools (Notion / Linear / Slack
/ inventory systems all fall short for the specific shape of work
he does). So he built four tools instead of using off-the-shelf:

| App | Role | Repo |
|---|---|---|
| **Memcon** | Local memory layer for Claude (MCP-based) | github.com/aryasgit/memcon |
| **Memshare** | P2P end-to-end encrypted comms for sharing code/files during workflows | (user will provide) |
| **Thymeline** | Documentation app — logs ideas, progress, stores everything timeline-shaped | (user will provide) |
| **Invpart** | Inventory management — tracks/manages/stores parts | (user will provide) |

All four are shipped. All four are at comparable polish to Memcon.

**Voice / working style:** terse, opinionated, fast. He's used to long
working sessions, multiple iterations, and trusts you to ship code
without over-asking. He says things like "HELL YES" when something
works and "remove this part" when something doesn't. Don't over-pad
responses with caveats.

---

## 2. The strategy you're executing

**Goal:** stronger marketing/portfolio narrative — a unified story
that reads better than "four random apps" for hiring, funding,
self-presentation.

**Decision:** ship as **Engram** — a single umbrella brand above the
four existing apps. NOT a technical bundle. Not cross-app integration.
Just a meta-brand that gives the four a shared identity and a
philosophical thesis.

**Why "Engram":** an engram is the neuroscience term for a memory
trace. Memcon was originally going to be named Engram before being
renamed. Now Engram becomes the umbrella, and the four apps become the
four facets of an engineering project's "engram":

- **Memcon** — what was *learned*
- **Memshare** — what was *said*
- **Thymeline** — what was *done*
- **Invpart** — what *exists*

That's the pitch in four lines. It's clean, structural, defensible.

**The shared posture across all four:**
- Local-first (nothing leaves the user's machine by default)
- MIT licensed
- Engineer-shaped (specifically: for engineers who do code + hardware
  + parts + threads together, not generic PM)
- Each works standalone — never required to install more than one
- All built originally to serve [[BARQ]] but generalised

---

## 3. What you're explicitly NOT doing

This matters because the seductive technical project would be wrong.

❌ **Don't build cross-app interop.** No shared `project_id`, no URI
scheme (`mem://`, `share://`, etc.), no shared backbone. That's months
of work that doesn't serve the marketing-narrative goal. It's the
right thing to defer.

❌ **Don't change the individual app landings significantly.** Each
app's existing landing stays. Add at most a small `Part of Engram ↗`
link in the nav. Otherwise leave them alone — they each have their
own sharp wedge that the umbrella should preserve.

❌ **Don't unify the installers.** Each app keeps its own install
path. You don't want "install Engram, get four things." You want
"install Memcon because you have a Claude problem; discover the other
three later."

❌ **Don't build a dashboard that surfaces all four.** That collapses
the bundle into one product and loses the sharpness.

❌ **Don't pick a different brand than Engram unless the user
explicitly reopens that.** The naming decision is settled.

---

## 4. What you ARE building

**One thing: the Engram landing page.** A single page that lives at
the Engram domain and tells the unified story. Six sections:

1. **Hero** — the engram thesis in big type. One sentence headline:
   *"Four tools. One engineering project's full memory."* (or
   whatever variant lands better — workshop it.)
2. **The four facets** — a 4-column row, one paragraph per app, with
   a CTA to that app's existing landing page.
3. **The philosophy** — local-first, MIT, engineer-shaped. This is
   where the principles get dedicated real estate as their own
   value prop (not buried in fine print).
4. **The origin** — BARQ paragraph + "built by one engineer" credibility.
5. **Mix-and-match** — "use one, use all four, never required to
   install more than you need." Removes the bundle objection.
6. **Footer** — credits, the BARQ link, sponsorship.

Plus tiny additions to each individual app's landing:
- Top nav: `Part of Engram ↗` link to the umbrella landing
- That's it. No other changes.

---

## 5. The design system to use

Use `/Users/barq/BARQ/engram/DESIGN.md` — the existing portable
design system extracted from Memcon's redesign + chat UI. It's the
visual language for the entire Engram family.

**The five rules** (from DESIGN.md §1) you must not break:

1. **Monochrome only.** Black bg, white text, gray ladder. No accent
   color anywhere. One green pulse for "live" status max.
2. **No bordered cards.** Sections demarcated by 1px lines and
   negative space only.
3. **Massive display next to tiny micro-labels.** Inter Tight at
   `clamp(2.5rem, 7vw, 6rem)` versus uppercase tracked-`.16em`
   `0.66rem` labels.
4. **Editorial multi-column grids.** Default to 3 columns
   (`1.1fr 1.6fr 1fr`). Even when content "wants" centering.
5. **Different micro-interaction per section.** Variety is the
   life — never reuse the same hover effect twice on the same page.

The Quick-start CSS block lives at `DESIGN.md` §9 — paste it
into a new HTML file as the entire starting point.

Reference implementations of the system:
- `/Users/barq/BARQ/engram/docs/index.html` — Memcon's landing
- `/Users/barq/BARQ/engram/api/ui.html` — Memcon's chat UI

The Engram landing should look like a sibling to those — same palette,
same type, same interaction vocabulary — but with a different
informational architecture (umbrella overview instead of single-product
pitch).

---

## 6. Critical file paths

```
/Users/barq/BARQ/engram/
├── DESIGN.md                 ← THE design system reference
├── ROADMAP.md                ← Memcon's roadmap (v1 → v6+)
├── README.md                 ← Memcon's README
├── docs/index.html           ← Memcon's landing (reference impl)
├── docs/install/             ← Memcon installer downloads
├── api/ui.html               ← Memcon's chat UI (reference impl)
├── memcon_mcp/server.py      ← Memcon MCP server (16 tools, v3.1)
├── memory/                   ← v3.1 architecture
│   ├── templates.py          ← Universal note templates
│   ├── extractor.py          ← Multi-pass LLM extraction
│   ├── entity_index.py       ← SQLite entity inverted index
│   ├── enricher.py           ← Background git + see-also
│   ├── writer.py             ← log_universal entry point
│   └── retrieve.py           ← Hybrid query
├── meta-vault/               ← Obsidian vault documenting Memcon
│   └── (133 notes, browse in Obsidian → graph view)
├── scripts/
│   ├── build_meta_vault.py   ← Regenerates meta-vault/
│   ├── migrate_to_v3_1.py    ← Backfills old notes
│   └── register_mcp.py       ← Patches Claude Desktop config
└── handoff/                  ← YOU ARE HERE
    ├── ENGRAM_CONTEXT.md     ← This file
    └── APP_SUMMARY_PROMPT.md ← Prompt for extracting other-app context
```

**Where Memshare / Thymeline / Invpart live on disk:** the user will
tell you their paths in the conversation, then run the
`APP_SUMMARY_PROMPT.md` prompt in each of those project's conversations
to produce structured handoffs. Wait for those before designing the
unified landing — you need the right one-line pitches and value props
for each.

---

## 7. Memcon — full context (since you may not know it)

You DO have full context on Memcon by reading this repo. Key facts you
should internalize before designing the umbrella:

**Current version:** v3.1 (in progress; v1.0 and v2.0 are tagged
releases, v3.0 + v3.1 are mid-flight).

**The pitch:** "Memory for Claude" — a local memory layer that plugs
into Claude over MCP. Auto-queries past project history before
answering, auto-writes debug sessions after solving.

**Tech stack:** Python 3.10+, FastMCP for the MCP server, Qdrant for
vectors (Docker), Ollama for the local LLM, sentence-transformers
(`all-MiniLM-L6-v2`) for embeddings, FastAPI for the dashboard.

**MCP tools:** 16 of them in v3.1 — `memcon_query`, `memcon_ask`,
`memcon_capture` (the default write), and 13 others. See
`memcon_mcp/server.py` or `meta-vault/MOC — Features.md`.

**v3.1 architecture** (recent — landed in last session):
- Universal note schema (8 kinds: debug / decision / experiment /
  concept / reference / meeting / breakthrough / session)
- Multi-pass extraction (classify → structure → entities → optional
  critique, all Ollama JSON mode)
- Entity index (SQLite inverted index at `{vault}/.memcon/entities.db`)
- Hybrid retrieval (semantic + entity, merged + reranked)
- Auto-enrichment (background thread: git context + see-also lines)
- Migration script for legacy notes

**Distribution:**
- One-liner installer: `curl ... | bash` (macOS/Linux/WSL) or PowerShell
- Repo at github.com/aryasgit/memcon
- VS Code/Cursor extension as `.vsix` (downloadable from landing)
- Sponsorship via GitHub Sponsors (tipjar, not paywall)

**The narrative arc** (from `meta-vault/The story.md`):
1. Born for BARQ
2. Wired into Claude via MCP
3. Generalized to ingest everything (code, PDFs, git)
4. Moved into the editor (VS Code/Cursor)
5. Made notes worth keeping (v3.1 schema overhaul)
6. Next: knows what it knows (v4), multimodal (v5), managed option (v6+)

---

## 8. The four-line bundle pitch — work from this

> An *engram* is a memory trace. An engineering project leaves four:
> what you learned, what you said, what you did, what you have.
>
> **Memcon** — what was learned. Local memory for Claude.
> **Memshare** — what was said. P2P encrypted comms.
> **Thymeline** — what was done. Timeline-shaped docs.
> **Invpart** — what you have. Inventory that doesn't suck.
>
> Local. MIT. Engineer-shaped. Built while making BARQ.

That's the seed. Refine, don't replace.

---

## 9. Recommended first steps in the new conversation

1. **Read** `DESIGN.md`, `README.md`, and `meta-vault/The story.md`
   to load Memcon's context fully.
2. **Ask the user** to run the `APP_SUMMARY_PROMPT.md` against each
   of the other three projects and paste the results back. Don't try
   to design the landing without them — generic placeholder copy for
   Memshare/Thymeline/Invpart will be off-key.
3. **Once you have all four summaries**, draft a one-page Engram
   landing in HTML, using DESIGN.md's quick-start CSS as the base.
   Match the visual style of `docs/index.html` exactly.
4. **Workshop the hero headline** with the user. The four-line pitch
   above is a seed, not the final copy. Try 3–4 variants.
5. **Show the user the landing**. Iterate. Keep it monochrome,
   editorial, dense-but-pretty.
6. **Only after the landing is shipped**: small `Part of Engram ↗`
   nav additions to each of the four apps' existing landings.

---

## 10. Anti-instructions

Things the user has explicitly rejected or that go against the project's
stance — don't propose them:

- ❌ Hosted/SaaS version of Engram or any of its apps as the *default*
- ❌ Telemetry / phone-home of any kind
- ❌ Ads in any dashboard
- ❌ Paid pro tier gating features
- ❌ Bespoke embedding models (sentence-transformers MiniLM is fine)
- ❌ Cross-app integration plumbing in this phase
- ❌ Renaming Memcon (back to Engram or otherwise) — Memcon is a
  shipped product brand and stays. Engram is the *umbrella* above it.

---

## 11. Tone you should bring

- Confident, direct, short responses unless explanation is needed
- Real opinions — the user wants pushback, not yes-and
- Tables and bullet lists for scannable info
- Code in monospace, file paths in monospace
- No emoji unless replying to user using emoji
- "TL;DR" sections welcome at the top of long responses
- Don't ask permission for things in your wheelhouse — just propose
  and iterate

---

## 12. What success looks like

By the end of the conversation:

- [ ] You have one-line pitches + structured summaries for all four apps
- [ ] You've drafted an Engram landing page that visually matches
  Memcon's `docs/index.html`
- [ ] The four apps are linked, each retains its own identity
- [ ] The user has a "this is portfolio-worthy" reaction
- [ ] You've committed the landing to a repo (new one, or under
  `engram/docs/engram/index.html`, or wherever the user prefers)
- [ ] You've left a follow-up note for what's next (small nav links
  on each component app's existing landing)

---

*End of context file. The new conversation should treat everything
above as authoritative project background. If anything contradicts
what's in the actual codebase, the codebase wins.*
