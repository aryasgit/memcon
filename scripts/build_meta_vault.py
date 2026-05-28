#!/usr/bin/env python3
"""
scripts/build_meta_vault.py

Generates a complete Obsidian vault that documents the Memcon project itself —
its versions, features, components, concepts, design decisions, UI iterations,
bugs, and milestones. Every note is densely cross-linked with [[wikilinks]] so
that opening the vault in Obsidian and switching to graph view shows the whole
project as a knowledge net.

Usage:
    python3 -m scripts.build_meta_vault [--dest meta-vault] [--clean]

After running, open the folder in Obsidian:
    1. Obsidian → Open vault → pick the meta-vault/ folder
    2. Toggle Graph View (Cmd+G) — you'll see ~90 nodes with hundreds of edges
    3. Click any node to navigate; backlinks panel shows what points at it

This vault is INDEPENDENT of the runtime vault Memcon uses for its own
operation. It exists purely for human exploration of the project.
"""
from __future__ import annotations
import argparse, sys, shutil
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────────────
# Note rendering helpers
# ──────────────────────────────────────────────────────────────────────────────

def fm(tags: list[str], extra: dict | None = None) -> str:
    """Render frontmatter block."""
    lines = ["---", "tags: [" + ", ".join(tags) + "]"]
    for k, v in (extra or {}).items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def related(*links: str) -> str:
    """Render a Related section with wikilinks."""
    if not links:
        return ""
    lines = ["## Related"]
    for l in links:
        lines.append(f"- [[{l}]]")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# THE NOTES
# Each entry: (relative_path, frontmatter_tags, content)
# Content is rendered as: H1 (from filename) + prose + Related
# ──────────────────────────────────────────────────────────────────────────────

NOTES: list[tuple[str, list[str], str]] = []

def N(path: str, tags: list[str], body: str) -> None:
    NOTES.append((path, tags, body.strip() + "\n"))


# ═══════════════════════════════════════════════════════════════════════════════
# HOMEPAGE + MOCs
# ═══════════════════════════════════════════════════════════════════════════════

N("README.md", ["index", "homepage"], """
# Memcon — Project Vault

This vault is **about** the Memcon project — how it grew, how it works,
what it became. It's a separate vault from the runtime memory Memcon uses.

If you opened this in Obsidian, hit **Cmd + G** to see the graph view.
You should see ~90 nodes connected by hundreds of edges. Click any node
to navigate.

## Start here

- [[00-Index]] — full map of contents
- [[v3.1 — Rich notes, hybrid recall]] — where the project is right now
- [[The story]] — the project's arc in 6 paragraphs
- [[MCP Server]] — the single most important component

## Browse by category

- [[MOC — Versions]]
- [[MOC — Features]]
- [[MOC — Components]]
- [[MOC — Concepts]]
- [[MOC — Design Decisions]]
- [[MOC — UI]]
- [[MOC — Bugs and Fixes]]
- [[MOC — Milestones]]
- [[MOC — People and Places]]
- [[MOC — Rejected ideas]]

## Why this vault exists

Memcon is too many decisions and modules to hold in one head. This vault
makes them browseable: each design choice has a note, each module has a
note, each version has a note, each notable bug has a note. The graph
view turns that into a picture.

Built by [[Aryaman (aryasgit)]] for [[BARQ (the robot)]].
""")

N("00-Index.md", ["index"], """
# Index

Complete map of every note in this vault, grouped by category.

## Versions
- [[v1.0 — Plug into Claude]]
- [[v2.0 — Memory absorbs everything]]
- [[v3.0 — Lives in your editor]]
- [[v3.1 — Rich notes, hybrid recall]]
- [[v4.0 — Knows what it knows (planned)]]
- [[v5.0 — Multimodal and shared (planned)]]
- [[v6.0+ — Managed option, niche depth (planned)]]

## Features
- [[MCP Server]]
- [[memcon_capture]] · [[memcon_query]] · [[memcon_ask]]
- [[memcon_write_debug]] · [[memcon_write_decision]] · [[memcon_write_experiment]]
- [[memcon_write_concept]] · [[memcon_write_reference]] · [[memcon_write_meeting]] · [[memcon_write_breakthrough]]
- [[memcon_session_summary]] · [[memcon_update_note]]
- [[memcon_timeline]] · [[memcon_digest]]
- [[memcon_stats]] · [[memcon_subsystems]]
- [[Auto-wikilinks on write]]
- [[Code ingestion]] · [[PDF ingestion]] · [[Git auto-ingest]]
- [[Multi-project switching]]
- [[VS Code extension]] · [[bin-memcon CLI]]
- [[Universal note schema]] · [[Multi-pass extraction]]
- [[Entity index]] · [[Hybrid retrieval]] · [[Auto-enrichment]]

## Components
- [[config.py]]
- [[memory.templates]] · [[memory.writer]] · [[memory.extractor]]
- [[memory.entity_index]] · [[memory.enricher]]
- [[memory.retrieve]] · [[memory.qdrant_store]]
- [[memcon_mcp.server]]
- [[ingestion.ingest]] · [[ingestion.chunker]] · [[ingestion.embedder]] · [[ingestion.watcher]]
- [[api.main]] · [[api.ui.html]]
- [[scripts.register_mcp]] · [[scripts.migrate_to_v3_1]] · [[scripts.ingest_code]] · [[scripts.ingest_git]]
- [[bootstrap.sh]] · [[bootstrap.ps1]] · [[install.sh]]
- [[vscode extension source]]

## Concepts
- [[Model Context Protocol (MCP)]]
- [[Semantic search]] · [[Embeddings]] · [[Hybrid retrieval]]
- [[Qdrant]] · [[Ollama]] · [[FastMCP]] · [[Sentence Transformers]]
- [[Obsidian]] · [[Wikilinks]]
- [[Local-first]] · [[RAG]]
- [[Note kinds]] · [[Subsystems]]

## Design Decisions
- [[Why MCP not REST]] · [[Why Qdrant not pgvector]]
- [[Why local LLM not cloud]] · [[Why Obsidian markdown]]
- [[Why monochrome only]] · [[Why no bordered cards]] · [[Why different interaction per section]]
- [[Why preserve raw context]] · [[Why multi-pass extraction]]
- [[Why SQLite for entity index]] · [[Why background enrichment]]
- [[Why universal schema]] · [[Why MIT licensed]]

## UI
- [[UI v0 — Monochrome serif]]
- [[UI v1 — Claude chat style]]
- [[UI v2 — Audi-Sirnik red]]
- [[UI v3 — Sirnik editorial final]]
- [[DESIGN.md — the design system]]
- [[Five rules of the editorial system]]

## Bugs and Fixes
- [[sed regex hit embedding_model]]
- [[openai missing from requirements]]
- [[cwd is slash on macOS sandbox]]
- [[stdout pollution corrupts JSONRPC]]
- [[Claude Desktop ignores cwd]]
- [[HTTP download lost +x bit]]
- [[Anchor link blue color leak]]

## Milestones
- [[MCP server stood up]]
- [[Engram renamed to Memcon]]
- [[v1.0 tagged]] · [[v2.0 tagged]]
- [[VS Code extension shipped]]
- [[Sirnik landing redesign shipped]]
- [[Design system extracted]]
- [[v3.1 layers landed]]

## People and Places
- [[Aryaman (aryasgit)]] · [[BARQ (the robot)]]
- [[Claude (Anthropic)]] · [[Claude Desktop]] · [[Cursor]] · [[VS Code]]
- [[Sirnik (design reference)]]

## Rejected Ideas
- [[SaaS-first version]]
- [[Telemetry phone-home]]
- [[Ads in dashboard]]
- [[Paid pro tier]]
- [[Bespoke embedding model]]
""")

N("The story.md", ["narrative"], """
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
""")


# ═══════════════════════════════════════════════════════════════════════════════
# MOCs (Maps of Content)
# ═══════════════════════════════════════════════════════════════════════════════

N("MOC — Versions.md", ["moc"], """
# MOC — Versions

Each version corresponds to a *theme*, not a calendar date. Shipped when
the theme felt real.

## Shipped
- [[v1.0 — Plug into Claude]] — MCP server you can ask Claude to use
- [[v2.0 — Memory absorbs everything]] — ingestion, capture, multi-project

## In progress
- [[v3.0 — Lives in your editor]] — VS Code / Cursor extension
- [[v3.1 — Rich notes, hybrid recall]] — schema + extraction + entity index

## Planned
- [[v4.0 — Knows what it knows (planned)]] — self-aware memory
- [[v5.0 — Multimodal and shared (planned)]] — images, voice, teams
- [[v6.0+ — Managed option, niche depth (planned)]] — hosted version, ROS bags

## Related
- [[The story]]
- ROADMAP.md (in the repo root, not in this vault)
""")

N("MOC — Features.md", ["moc"], """
# MOC — Features

## Read (query) tools
- [[memcon_query]] — raw semantic + entity chunks
- [[memcon_ask]] — grounded LLM answer
- [[memcon_timeline]] — time-bounded slice
- [[memcon_digest]] — N-day summary
- [[memcon_stats]] — vault size, entity index size
- [[memcon_subsystems]] — list configured tags

## Write tools
- [[memcon_capture]] — the default: natural-language → structured note
- [[memcon_write_debug]] · [[memcon_write_decision]] · [[memcon_write_experiment]]
- [[memcon_write_concept]] · [[memcon_write_reference]] · [[memcon_write_meeting]] · [[memcon_write_breakthrough]]
- [[memcon_session_summary]] · [[memcon_update_note]]

## Ingestion
- [[Code ingestion]]
- [[PDF ingestion]]
- [[Git auto-ingest]]

## Platform features
- [[Multi-project switching]]
- [[Auto-wikilinks on write]]
- [[VS Code extension]]
- [[bin-memcon CLI]]

## v3.1 architecture features
- [[Universal note schema]]
- [[Multi-pass extraction]]
- [[Entity index]]
- [[Hybrid retrieval]]
- [[Auto-enrichment]]

## Related
- [[MCP Server]]
- [[MOC — Components]]
""")

N("MOC — Components.md", ["moc"], """
# MOC — Components

Every Python module and important file, grouped by layer.

## Configuration
- [[config.py]]
- [[memcon.config.yaml]]

## Memory layer (writes + reads)
- [[memory.templates]] — note templates (v3.1)
- [[memory.writer]] — log_universal + back-compat wrappers
- [[memory.extractor]] — 4-pass LLM extraction (v3.1)
- [[memory.entity_index]] — SQLite inverted index (v3.1)
- [[memory.enricher]] — background git + see-also (v3.1)
- [[memory.retrieve]] — hybrid query (v3.1)
- [[memory.qdrant_store]] — Qdrant client wrapper

## Ingestion pipeline
- [[ingestion.ingest]] — top-level ingest_file
- [[ingestion.chunker]] — markdown / code / pdf chunkers
- [[ingestion.embedder]] — sentence-transformers wrapper
- [[ingestion.watcher]] — vault file-watcher

## MCP surface
- [[memcon_mcp.server]] — 16 MCP tools registered via FastMCP

## HTTP surface
- [[api.main]] — FastAPI app at :8000
- [[api.ui.html]] — chat-style dashboard

## Scripts
- [[scripts.register_mcp]] — patch Claude Desktop config
- [[scripts.migrate_to_v3_1]] — backfill old notes
- [[scripts.ingest_code]] · [[scripts.ingest_git]]
- [[bootstrap.sh]] · [[bootstrap.ps1]] · [[install.sh]]

## Editor + CLI
- [[vscode extension source]]
- [[bin-memcon CLI]]

## Related
- [[MOC — Features]]
- [[MOC — Versions]]
""")

N("MOC — Concepts.md", ["moc"], """
# MOC — Concepts

The vocabulary the project depends on.

## Memcon-coined
- [[Note kinds]]
- [[Subsystems]]
- [[Hybrid retrieval]]
- [[Entity index]]

## Standard memory-system concepts
- [[Embeddings]]
- [[Semantic search]]
- [[RAG]]

## External technologies memcon stands on
- [[Model Context Protocol (MCP)]]
- [[Qdrant]]
- [[Ollama]]
- [[Sentence Transformers]]
- [[FastMCP]]
- [[Obsidian]]
- [[Wikilinks]]

## Stance
- [[Local-first]]

## Related
- [[MOC — Design Decisions]]
""")

N("MOC — Design Decisions.md", ["moc"], """
# MOC — Design Decisions

Non-obvious choices, with rationale. The "why is it this way?" answers.

## Architecture
- [[Why MCP not REST]]
- [[Why Qdrant not pgvector]]
- [[Why local LLM not cloud]]
- [[Why Obsidian markdown]]
- [[Why SQLite for entity index]]
- [[Why background enrichment]]
- [[Why multi-pass extraction]]
- [[Why universal schema]]
- [[Why preserve raw context]]

## Design language
- [[Why monochrome only]]
- [[Why no bordered cards]]
- [[Why different interaction per section]]

## Licensing / values
- [[Why MIT licensed]]

## Related
- [[MOC — Rejected ideas]]
- [[DESIGN.md — the design system]]
""")

N("MOC — UI.md", ["moc"], """
# MOC — UI

Iterations of the visible surfaces.

## Chat UI (api/ui.html)
- [[UI v0 — Monochrome serif]] — initial, "tried to look like Claude but in serif"
- [[UI v1 — Claude chat style]] — bottom textbox, Roboto-like sans

## Landing page (docs/index.html)
- [[UI v2 — Audi-Sirnik red]] — hot red accent, Anton display, editorial density
- [[UI v3 — Sirnik editorial final]] — reverted red, pure mono, varied interactions

## Design vocabulary
- [[DESIGN.md — the design system]]
- [[Five rules of the editorial system]]

## Related
- [[Sirnik (design reference)]]
- [[Why monochrome only]]
""")

N("MOC — Bugs and Fixes.md", ["moc"], """
# MOC — Bugs and Fixes

Notable bugs encountered during the build, with their fixes.

- [[sed regex hit embedding_model]]
- [[openai missing from requirements]]
- [[cwd is slash on macOS sandbox]]
- [[stdout pollution corrupts JSONRPC]]
- [[Claude Desktop ignores cwd]]
- [[HTTP download lost +x bit]]
- [[Anchor link blue color leak]]

## Related
- [[MOC — Components]]
- [[install.sh]]
""")

N("MOC — Milestones.md", ["moc"], """
# MOC — Milestones

The moments where the project meaningfully shifted.

- [[MCP server stood up]]
- [[Engram renamed to Memcon]]
- [[v1.0 tagged]]
- [[v2.0 tagged]]
- [[VS Code extension shipped]]
- [[Sirnik landing redesign shipped]]
- [[Design system extracted]]
- [[v3.1 layers landed]]

## Related
- [[The story]]
- [[MOC — Versions]]
""")

N("MOC — People and Places.md", ["moc"], """
# MOC — People and Places

The cast.

## People
- [[Aryaman (aryasgit)]] — builder, sole maintainer

## Projects and orgs
- [[BARQ (the robot)]] — the project memcon was born to serve
- [[Claude (Anthropic)]] — the LLM consumer

## Editors / tools
- [[Claude Desktop]]
- [[Cursor]]
- [[VS Code]]

## Design references
- [[Sirnik (design reference)]]

## Related
- [[The story]]
""")

N("MOC — Rejected ideas.md", ["moc"], """
# MOC — Rejected ideas

Things considered and deliberately not built. They'd change what memcon is.

- [[SaaS-first version]]
- [[Telemetry phone-home]]
- [[Ads in dashboard]]
- [[Paid pro tier]]
- [[Bespoke embedding model]]

## Related
- [[Why local LLM not cloud]]
- [[Why MIT licensed]]
- [[Local-first]]
""")


# ═══════════════════════════════════════════════════════════════════════════════
# VERSIONS (7)
# ═══════════════════════════════════════════════════════════════════════════════

N("versions/v1.0 — Plug into Claude.md", ["version", "shipped"], """
# v1.0 — Plug into Claude

**Theme:** the "MCP server you can ask Claude to use" version.

The defining move of v1.0: instead of building a UI for taking notes,
expose [[Note kinds|note operations]] as tools via [[Model Context Protocol (MCP)]]
so [[Claude (Anthropic)]] can decide when to query and when to write.
The user never opens memcon — they ask Claude, and Claude calls memcon
under the hood.

## Shipped

- [[MCP Server]] — stdio JSON-RPC, 9 tools at this point
- One-liner installer: [[bootstrap.sh]] (mac / Linux / WSL),
  [[bootstrap.ps1]] (Windows)
- RAM-tier model auto-pick from `llama3.2:1b` → `qwen2.5-coder:32b` (see [[Ollama]])
- [[scripts.register_mcp]] — patches [[Claude Desktop]] config
- [[api.main]] dashboard at `localhost:8000/ui` with chat-style UI ([[api.ui.html]])
- [[Auto-wikilinks on write]] — every new note links to top-3 semantic neighbours
- Public landing at `docs/` (which would later become [[UI v3 — Sirnik editorial final]])
- Robust against the [[cwd is slash on macOS sandbox]] problem

## Tools at v1.0 (9)

[[memcon_query]] · [[memcon_ask]] · [[memcon_write_debug]] ·
[[memcon_write_decision]] · [[memcon_write_experiment]] ·
[[memcon_session_summary]] · [[memcon_update_note]] · [[memcon_stats]] ·
[[memcon_subsystems]]

## Related
- [[v2.0 — Memory absorbs everything]]
- [[MCP server stood up]]
- [[v1.0 tagged]]
- [[Why MCP not REST]]
- [[The story]]
""")

N("versions/v2.0 — Memory absorbs everything.md", ["version", "shipped"], """
# v2.0 — Memory absorbs everything

**Theme:** memcon stops being a notes tool and becomes a project-memory
backend that swallows anything you point at it.

## Shipped

- [[Code ingestion]] — walks any project, respects `.gitignore`, chunks
  by 80-line windows (see [[scripts.ingest_code]])
- [[PDF ingestion]] — drop `.pdf` files in `vault/`, indexed page-by-page
- [[Git auto-ingest]] — post-commit hook makes every commit memory
  (see [[scripts.ingest_git]])
- [[memcon_capture]] — single natural-language MCP tool that uses the
  [[Ollama|local LLM]] to extract title/symptom/cause/fix from a paragraph
- [[memcon_timeline]] — time-bounded slice of recent notes
- [[memcon_digest]] — LLM-generated digest of the last N days
- [[bin-memcon CLI]] — `memcon ask / query / stats / recent / save / serve / ui`
- [[Multi-project switching]] via `MEMCON_VAULT`, `MEMCON_COLLECTION`,
  `MEMCON_MODEL` env vars
- GitHub Sponsors button — first step toward sustaining the project

## What it enabled

Once code + PDFs + commits all live in the same [[Qdrant|vector store]],
"why does Claude have such weak project context?" stops being a question.
Claude has *everything*. The retrieval quality is bounded by the
embedder ([[Sentence Transformers]]), not by the corpus.

## Related
- [[v1.0 — Plug into Claude]]
- [[v3.0 — Lives in your editor]]
- [[v2.0 tagged]]
- [[memcon_capture]]
- [[memcon_timeline]]
- [[memcon_digest]]
""")

N("versions/v3.0 — Lives in your editor.md", ["version", "in-progress"], """
# v3.0 — Lives in your editor

**Theme:** the moat feature. Once memcon is inline in [[VS Code]] / [[Cursor]],
the friction of "context-switching to a browser to consult memory" goes
to zero. The reflex becomes Cmd+Shift+M.

## MVP shipped

[[VS Code extension]] (see also [[vscode extension source]]):

- `Memcon: Ask` (`Cmd+Shift+M`) — grounded answer in a markdown tab
- `Memcon: Save selection to memory` (`Cmd+Shift+S`)
- `Memcon: Search` — raw chunks for inspection
- Activity-bar sidebar "Recent" tree with refresh + click-to-peek
- Same `.vsix` works in both [[VS Code]] and [[Cursor]] (Cursor reads
  VS Code extensions natively)
- Distributed as a download from the landing page (`docs/install/`)

## Still to land (0.2.x)

- Code lens on functions/classes: "3 related debug sessions, 2 decisions"
- Hover provider: shows top-1 related note when you hover a symbol
- Status bar widget: "last memcon write: 12 min ago"
- Direct [[memcon_capture]] integration (local-LLM extraction inline)
- Published to VS Code Marketplace + Open VSX
- [[bin-memcon CLI]] linked into `/usr/local/bin` via `MEMCON_LINK_CLI=1`
- Demo video (30-second screencast) on the README + landing hero

## Related
- [[v2.0 — Memory absorbs everything]]
- [[v3.1 — Rich notes, hybrid recall]]
- [[VS Code extension shipped]]
- [[Sirnik landing redesign shipped]]
""")

N("versions/v3.1 — Rich notes, hybrid recall.md", ["version", "in-progress"], """
# v3.1 — Rich notes, hybrid recall

**Theme:** generalize the schema away from quadruped-shaped 4-field notes;
extract more from each capture; add keyword-exact recall alongside semantic.
All still local.

The whole stack landed in two commits.

## Layer 1 — [[Universal note schema]]

[[memory.templates]] defines 8 note kinds with per-kind sections + shared
outer shape. [[memory.writer]] refactored to use [[memory.templates|templates]]
through a single `log_universal()` entry. All old write tools preserved as
back-compat wrappers.

## Layer 2 — [[Multi-pass extraction]]

[[memory.extractor]] runs classify → structure → entities → optional critique.
[[memcon_capture]] rewired through it. Four new MCP write tools added
([[memcon_write_concept]] / [[memcon_write_reference]] /
[[memcon_write_meeting]] / [[memcon_write_breakthrough]]).
**MCP surface now 16 tools** (was 12).

## Layer 3 — [[Entity index]] + [[Hybrid retrieval]]

[[memory.entity_index]] is a SQLite inverted index at `{vault}/.memcon/entities.db`.
[[memory.retrieve|memory.retrieve.query]] is now hybrid: semantic [[Qdrant]] hits +
entity-index hits, merged and reranked. Every read tool picks up
keyword-exact recall for free.

## Layer 4 — [[Auto-enrichment]]

[[memory.enricher]] spawns a background thread after every write: detects
git context, appends a `## See also` block with one-line summaries from
each related note's TL;DR. Non-blocking — write returns instantly.

## Layer 5 — [[scripts.migrate_to_v3_1|Migration]]

[[scripts.migrate_to_v3_1]] backfills legacy notes into the new schema.
Idempotent, safe (auto-backs-up originals), Ollama-optional.

## Related
- [[v3.0 — Lives in your editor]]
- [[v4.0 — Knows what it knows (planned)]]
- [[v3.1 layers landed]]
- [[Why universal schema]]
- [[Why multi-pass extraction]]
- [[Why preserve raw context]]
""")

N("versions/v4.0 — Knows what it knows (planned).md", ["version", "planned"], """
# v4.0 — Knows what it knows *(planned)*

**Theme:** memory that's self-aware. The store stops being passive — it
surfaces patterns, flags contradictions, and downweights stale information.

## Planned

- **Contradiction detection** — when a new note contradicts an existing
  one (same [[Subsystems|subsystem]], opposite outcome), flag the old one
  as `stale=true` and add a `"resolved by NEW_NOTE"` link
- **Confidence / freshness scoring** — old notes get downweighted in
  retrieval unless explicitly re-verified via `memcon_verify(note)`
- **Auto-link by tags** — notes sharing tags get cross-linked in
  [[Auto-wikilinks on write|## Related]] sections, augmenting semantic
  neighbours
- **Knowledge-graph viewer** in the [[api.ui.html|dashboard]] —
  interactive D3 graph of notes + edges (semantic + tag + wikilink),
  filterable by subsystem
- **`memcon_pattern(topic)`** MCP tool — find recurring symptoms /
  decisions / failures across the vault. "What keeps breaking?"
- **`memcon_what_changed(since)`** — semantic diff: what concepts have
  appeared or shifted in the last N days

## Why this is next

[[v3.1 — Rich notes, hybrid recall]] gave the system rich enough notes
and entity-aware retrieval. The next layer is *meta-cognition* — the
system reasoning about its own contents. The [[Entity index]] from v3.1
is the foundation pattern detection runs on.

## Related
- [[v3.1 — Rich notes, hybrid recall]]
- [[v5.0 — Multimodal and shared (planned)]]
- [[Entity index]]
- [[Hybrid retrieval]]
""")

N("versions/v5.0 — Multimodal and shared (planned).md", ["version", "planned"], """
# v5.0 — Multimodal and shared *(planned)*

**Theme:** beyond text. Multiple humans + multiple senses.

## Planned

- **Image ingestion** via CLIP embeddings — circuit photos, sketches,
  whiteboard screenshots, scope traces become semantically queryable
- **Voice memos** — `vault/voice/*.m4a` transcribed via Whisper, indexed
- **Web clipper browser extension** — save Stack Overflow answers, docs
  pages, blog posts to memcon with one click
- **Team vaults** — shared memory across an engineering team with
  privacy boundaries (some notes personal, some shared)
- **Mentions in notes** — `@servo` to tag a [[Subsystems|subsystem]],
  `@aryaman` to tag a person; mentions indexed for cross-references
- **Vault sync** — laptop ↔ robot ↔ workstation share the same vault
  via a chosen transport (Syncthing / iCloud / Dropbox / custom)
- **Mobile read-only app** — query memory from your phone (mostly for
  "wait, what did we decide about X?" moments away from the desk)

## Related
- [[v4.0 — Knows what it knows (planned)]]
- [[v6.0+ — Managed option, niche depth (planned)]]
""")

N("versions/v6.0+ — Managed option, niche depth (planned).md", ["version", "planned"], """
# v6.0+ — Managed option, niche depth *(planned)*

**Theme:** the moonshots. Only land if v1–v5 are deep, not because they
sound cool.

## Planned

- **Memcon Cloud** — managed hosted version for non-technical users or
  teams who don't want to run Docker locally. Real monetisation tier.
  Only if open-source traction makes this an obvious pull. ⚠️ Trades
  [[Local-first]] for accessibility.
- **ROS bag / telemetry ingestion** — robot runtime data becomes
  queryable memory. Niche but deep — the [[BARQ (the robot)]] origin
  keeps calling.
- **Hardware change-log tracking** — wiring diagrams, BOMs, calibration
  params version-tracked + auto-linked to debug sessions that reference
  them. Industrial / robotics audience.
- **Reproducibility queries** — `memcon_what_led_to(commit_sha)` returns
  the full memory chain that produced a specific code state.
- **LLM-agnostic backend** — swap [[Ollama]] for any OpenAI-compatible
  endpoint. Already mostly true via `llm.base_url`; needs UX polish.
- **Plugin SDK** — `memcon-plugin` interface so the community can ship
  domain-specific ingestion / MCP tools without forking core.

## Related
- [[v5.0 — Multimodal and shared (planned)]]
- [[BARQ (the robot)]]
- [[Local-first]]
""")


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURES (~29)
# ═══════════════════════════════════════════════════════════════════════════════

N("features/MCP Server.md", ["feature", "core"], """
# MCP Server

The single most important component of memcon. Implements the
[[Model Context Protocol (MCP)]] over stdio so [[Claude (Anthropic)]]
(running in [[Claude Desktop]] / [[Cursor]] / Claude Code) can call
memcon as a set of tools without HTTP, without auth, without a network.

**Module:** [[memcon_mcp.server]]
**Framework:** [[FastMCP]]
**Transport:** stdio JSON-RPC

## The 16 tools (at v3.1)

**Read:**
[[memcon_query]] · [[memcon_ask]] · [[memcon_timeline]] · [[memcon_digest]] ·
[[memcon_stats]] · [[memcon_subsystems]]

**Write:**
[[memcon_capture]] (preferred) · [[memcon_write_debug]] ·
[[memcon_write_decision]] · [[memcon_write_experiment]] ·
[[memcon_write_concept]] · [[memcon_write_reference]] ·
[[memcon_write_meeting]] · [[memcon_write_breakthrough]] ·
[[memcon_session_summary]] · [[memcon_update_note]]

## Why MCP and not a REST API

[[Why MCP not REST]] has the long answer. Short answer: when Claude can
call memcon as a *tool*, it decides when to query without any UI prompting.
That's the whole product — invisible memory.

## Related
- [[v1.0 — Plug into Claude]]
- [[MCP server stood up]]
- [[scripts.register_mcp]]
- [[Why MCP not REST]]
""")

# Generate the 16 tool notes via a loop — same shape, different content
TOOLS = [
    ("memcon_query", "read", "Semantic + entity hybrid search across the vault.",
     "The default read tool. Pass a natural-language question; returns the top-K chunks ranked by [[Hybrid retrieval]] (semantic [[Qdrant]] + [[Entity index]] hits, merged).",
     ["Hybrid retrieval", "Entity index", "memory.retrieve", "Qdrant", "Sentence Transformers"]),
    ("memcon_ask", "read", "Grounded LLM answer with citations.",
     "Runs [[memcon_query]] then asks the [[Ollama|local LLM]] to answer using ONLY the retrieved chunks. Cited. Slower than `query` but self-contained.",
     ["memcon_query", "Ollama", "api.ui.html", "RAG"]),
    ("memcon_timeline", "read", "Time-bounded slice of recent notes.",
     "Walks the vault, returns notes with `mtime > now − N days`, newest first. Optional subsystem filter. Doesn't touch [[Qdrant]] — file mtime + frontmatter only.",
     ["v2.0 — Memory absorbs everything", "memcon_digest", "Subsystems"]),
    ("memcon_digest", "read", "LLM-generated digest of the last N days.",
     "Reads recent notes (cap each to 3000 chars), feeds them to the [[Ollama|local LLM]], produces Themes / Wins / Open items / Worth revisiting. Great for Monday morning.",
     ["memcon_timeline", "Ollama", "v2.0 — Memory absorbs everything"]),
    ("memcon_stats", "read", "Vault diagnostics: chunk count, project info, entity index size.",
     "Cheap probe. Returns total chunks in [[Qdrant]], the project name, and (since [[v3.1 — Rich notes, hybrid recall|v3.1]]) the [[Entity index]] stats.",
     ["Entity index", "Qdrant", "memory.qdrant_store"]),
    ("memcon_subsystems", "read", "List configured subsystems + note kinds.",
     "Tells Claude which [[Subsystems|subsystem]] buckets exist before writing. Since v3.1, also returns the [[Note kinds|note_kinds]] list so Claude knows what types of notes it can write.",
     ["Subsystems", "Note kinds", "memcon.config.yaml"]),
    ("memcon_capture", "write", "DEFAULT write tool — natural-language → structured note.",
     "Routes any 'save this' / 'log it' / 'remember' instruction through the [[Multi-pass extraction]] pipeline. Auto-picks the [[Note kinds|kind]], extracts fields + entities, writes via [[memory.writer|log_universal]]. The tool Claude reaches for unless the user is dictating structured fields explicitly.",
     ["Multi-pass extraction", "memory.extractor", "Note kinds", "Auto-enrichment", "v3.1 — Rich notes, hybrid recall"]),
    ("memcon_write_debug", "write", "Structured debug note (legacy + back-compat surface).",
     "Title/symptom/cause/fix/status/subsystem/tags. Pre-v3.1 was the dominant write path. Now mostly used when [[memcon_capture]] would be overkill (already-structured input).",
     ["memcon_capture", "memory.writer", "Universal note schema"]),
    ("memcon_write_decision", "write", "Structured decision note.",
     "Title/decision/reasoning/subsystem/tags. v3.1 added context/options/consequences as optional kwargs.",
     ["memcon_capture", "memory.writer", "Universal note schema"]),
    ("memcon_write_experiment", "write", "Structured experiment note.",
     "Title/hypothesis/result/conclusion/subsystem/tags. v3.1 added optional setup.",
     ["memcon_capture", "memory.writer", "Universal note schema"]),
    ("memcon_write_concept", "write", "Concept / definition / mental model note.",
     "Added in [[v3.1 — Rich notes, hybrid recall|v3.1]]. Sections: Definition / Why it matters / Example / Pitfalls. Use when the user teaches you a domain term.",
     ["v3.1 — Rich notes, hybrid recall", "Universal note schema", "Note kinds"]),
    ("memcon_write_reference", "write", "External reference (API / spec / docs) captured locally.",
     "Added in v3.1. Sections: Summary / Key points / Notes / Source. Use when grabbing context that should survive even if a URL rots.",
     ["v3.1 — Rich notes, hybrid recall", "Universal note schema", "Note kinds"]),
    ("memcon_write_meeting", "write", "Meeting / sync notes.",
     "Added in v3.1. Sections: Attendees / Notes / Decisions / Action items. Decisions + actions live in their own sections so they're separately searchable.",
     ["v3.1 — Rich notes, hybrid recall", "Universal note schema", "Note kinds"]),
    ("memcon_write_breakthrough", "write", "The 'aha' insight note.",
     "Added in v3.1. Sections: Background / Insight / Implication / Next steps. For when understanding shifts — the kind of thing you want to find six months later.",
     ["v3.1 — Rich notes, hybrid recall", "Universal note schema", "Note kinds"]),
    ("memcon_session_summary", "write", "End-of-session roll-up.",
     "Captures what was worked on, broken, fixed, or decided. Call near the end of a working session. In v3.1 routes through [[memory.writer|log_universal]] with kind=session.",
     ["memory.writer", "Note kinds"]),
    ("memcon_update_note", "write", "Append findings to an existing note.",
     "For when a previously-open debug session gets resolved. Takes the path returned by an earlier write tool, appends a timestamped update block, re-ingests into [[Qdrant]].",
     ["memory.writer", "ingestion.ingest"]),
]

for name, kind_tag, summary, prose, related_list in TOOLS:
    rel_links = "\n".join(f"- [[{r}]]" for r in related_list + ["MCP Server"])
    N(f"features/{name}.md", ["feature", "mcp-tool", kind_tag], f"""
# {name}

**{summary}**

{prose}

## Lives in

[[memcon_mcp.server]] — registered via `@mcp.tool()` decorator on
[[FastMCP]] instance.

## Related
{rel_links}
""")

# Other major features
N("features/Auto-wikilinks on write.md", ["feature"], """
# Auto-wikilinks on write

Every new note gets an auto-generated `## Related` section with Obsidian
[[Wikilinks]] pointing to the top-3 semantically-similar existing notes
in the vault.

## Where it lives

[[memory.writer]] — `_find_related(query_text, exclude_doc)` runs a
semantic search via [[memory.retrieve]] *before* writing the note, then
splices the resulting wikilinks into the body.

## Why before, not after

Because if the note were written first and *then* queried, it would
match itself (high cosine similarity). Pre-write search is cleaner.

## Shipped

[[v1.0 — Plug into Claude]].

## Related
- [[Obsidian]]
- [[Wikilinks]]
- [[memory.writer]]
- [[Auto-enrichment]] — adds a `## See also` section with one-liner
  summaries on top of this
""")

N("features/Code ingestion.md", ["feature"], """
# Code ingestion

Walks any project, respects `.gitignore`-style exclusions, chunks source
files by 80-line windows, embeds via [[Sentence Transformers]], stores
in [[Qdrant]] keyed by file + line range.

## Where it lives

- [[scripts.ingest_code]] — the CLI entry: `python3 -m scripts.ingest_code`
- [[ingestion.chunker]] — the chunking strategy
- [[ingestion.embedder]] — the embedding wrapper
- [[ingestion.ingest]] — the upsert path

## Shipped

[[v2.0 — Memory absorbs everything]].

## Effect

Once code is ingested, asking Claude "where do we handle JWT expiry?"
returns the right file + the surrounding 80 lines, even if the keyword
"JWT expiry" doesn't literally appear in the code.

## Related
- [[PDF ingestion]]
- [[Git auto-ingest]]
- [[Semantic search]]
""")

N("features/PDF ingestion.md", ["feature"], """
# PDF ingestion

Drop `.pdf` files into `vault/`, they get indexed page-by-page via
`pypdf`. No OCR — text-extraction PDFs only.

## Where it lives

[[ingestion.chunker]] — has a `chunk_file()` dispatcher that routes
`.pdf` to a pypdf-based extractor. [[ingestion.ingest]] handles
the rest the same way it would for markdown.

## Shipped

[[v2.0 — Memory absorbs everything]].

## Why pages, not paragraphs

Pages are the natural breakpoint readers expect. Paragraph chunking
turned out to be inconsistent across the PDFs people actually drop in
(papers, datasheets, manuals). Pages are predictable.

## Related
- [[Code ingestion]]
- [[ingestion.chunker]]
""")

N("features/Git auto-ingest.md", ["feature"], """
# Git auto-ingest

Installs a `post-commit` hook so every commit message + diff summary
becomes searchable memory automatically.

## Where it lives

- [[scripts.ingest_git]] — runs after each commit
- `scripts/install_git_hook.sh` — the installer

## Shipped

[[v2.0 — Memory absorbs everything]].

## What gets stored

For each commit: SHA, message, author, file list, +/-LOC. Stored as a
small markdown chunk under `vault/git/`. Embeddings on the message let
queries like "when did we add the JWT middleware" surface the relevant
commit.

## Related
- [[Code ingestion]]
- [[v2.0 — Memory absorbs everything]]
""")

N("features/Multi-project switching.md", ["feature"], """
# Multi-project switching

Three env vars switch memcon between projects without reconfiguring:

- `MEMCON_VAULT` — vault path override
- `MEMCON_COLLECTION` — [[Qdrant]] collection name override
- `MEMCON_MODEL` — [[Ollama]] model tag override

## Where it lives

[[config.py]] — `get_config()` checks each env var and overrides the
default from `memcon.config.yaml`. The override happens at config-load
time, so all downstream modules ([[memory.writer]], [[memory.retrieve]],
[[memcon_mcp.server]]) just see the right paths.

## Shipped

[[v2.0 — Memory absorbs everything]].

## Why env vars and not multiple config files

Atomicity. You can launch memcon for a specific project with one shell
line:
```
MEMCON_VAULT=~/projects/foo MEMCON_COLLECTION=foo_memory memcon serve
```

No reload, no profile switching.

## Related
- [[config.py]]
- [[bin-memcon CLI]]
""")

N("features/VS Code extension.md", ["feature"], """
# VS Code extension

Inline access to memcon from [[VS Code]] and [[Cursor]]. Three commands
+ a sidebar tree:

- `Memcon: Ask` (`Cmd+Shift+M`) — grounded answer in a markdown tab
- `Memcon: Save selection to memory` (`Cmd+Shift+S`) — captures selection
- `Memcon: Search` — raw chunks for inspection
- Activity-bar sidebar "Recent" tree with refresh + click-to-peek

## Where it lives

[[vscode extension source]] — TypeScript, compiled with `tsc`, packaged
with `vsce` as `memcon-vscode-0.1.0.vsix`.

## Distribution

Currently as a download from the landing page (`docs/install/`). Coming:
VS Code Marketplace + Open VSX (see [[v3.0 — Lives in your editor]]).

## Shipped

[[v3.0 — Lives in your editor]] MVP. [[VS Code extension shipped]] for
the moment it landed.

## Related
- [[VS Code]] · [[Cursor]]
- [[bin-memcon CLI]]
""")

N("features/bin-memcon CLI.md", ["feature"], """
# bin/memcon CLI

A bash wrapper at `bin/memcon` that exposes memcon's core operations
from any directory:

```
memcon ask "what was the wrist servo fix?"
memcon query "thermal"
memcon stats
memcon recent
memcon digest
memcon save "..."
memcon serve   # start the HTTP API
memcon ui      # open the dashboard
```

## Where it lives

[[bin-memcon CLI]] file itself + delegation to the Python entry points
in [[api.main]] / [[memory.writer]] / [[memory.retrieve]].

## Shipped

[[v2.0 — Memory absorbs everything]].

## In `PATH`

Currently you run it relative to the repo. Coming in [[v3.0 — Lives in your editor]]:
`install.sh` symlinks `bin/memcon` into `/usr/local/bin` if
`MEMCON_LINK_CLI=1` is set.

## Related
- [[Multi-project switching]]
- [[api.main]]
""")

N("features/Universal note schema.md", ["feature", "v3.1"], """
# Universal note schema

The v3.1 replacement for the pre-existing 4-field schema (title / symptom /
cause / fix). One outer shape, swappable middle per [[Note kinds|kind]].

## What "universal" means

Every note, regardless of kind, has:

- **Rich frontmatter** — `id`, `type`, `created`, `updated`, `subsystem`
  (now a list), `tags`, `status`, `confidence`, `entities` (six categories),
  `git` (commit / branch / changed_files), `linked` ([[Obsidian]] wikilinks)
- **TL;DR** — one-sentence headline
- **Per-kind middle sections** — the part that differs (Symptom / Cause /
  Fix for debug; Context / Decision / Reasoning for decision; etc.)
- **`## Context`** — verbatim conversation excerpt preserved for the
  embedder (see [[Why preserve raw context]])
- **`## Related`** — auto-generated [[Auto-wikilinks on write|wikilinks]]
- **`## See also`** — added asynchronously by [[Auto-enrichment]]

## Where it lives

[[memory.templates]] is the renderer. [[memory.writer]] is the entry point
(`log_universal(kind, title, fields, …)`).

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 1.

## Related
- [[Multi-pass extraction]] — fills these fields
- [[Note kinds]]
- [[Why universal schema]]
- [[Why preserve raw context]]
""")

N("features/Multi-pass extraction.md", ["feature", "v3.1"], """
# Multi-pass extraction

[[memory.extractor]] runs four sequential passes against the [[Ollama|local LLM]]
to turn freeform input into structured note fields. Replaces the
single-prompt approach used in v2.0's [[memcon_capture]].

## The four passes

1. **`classify_type(text)`** → picks one of the 8 [[Note kinds]]
2. **`extract_structure(text, kind)`** → fills per-kind sections + TL;DR
   + `context_raw`, all in Ollama JSON mode for parseability
3. **`extract_entities(text)`** → files / symbols / errors / packages /
   urls / concepts → indexed in [[Entity index]]
4. **`self_critique(text, draft)`** *(optional)* → "what did you miss?"
   pass. Doubles runtime; only useful on long inputs.

## Why multiple passes

A single prompt asks too much of small local models like qwen-coder-7b.
Decomposing into focused sub-tasks (each with its own narrow schema)
boosts accuracy and lets each pass use `response_format={"type":"json_object"}`.

See [[Why multi-pass extraction]].

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 2.

## Related
- [[memcon_capture]] — the public surface
- [[memory.extractor]]
- [[Ollama]]
- [[Universal note schema]]
""")

N("features/Entity index.md", ["feature", "v3.1"], """
# Entity index

A SQLite-backed inverted index that maps named entities (files, symbols,
errors, packages, URLs, concepts) back to the notes that mention them.

Complements [[Qdrant|vector search]]: vectors give fuzzy "this is roughly
about that," entities give exact "the note that mentions servo.cpp."
Together = [[Hybrid retrieval]].

## Schema

```
CREATE TABLE entities (
    entity     TEXT,    -- raw, case-preserved
    entity_lc  TEXT,    -- lowercase for fast lookup
    kind       TEXT,    -- files | symbols | errors | packages | urls | concepts
    doc_name   TEXT,    -- slug matching Qdrant payload doc_name
    path       TEXT,    -- absolute file path
    last_seen  TEXT,    -- ISO timestamp
    PRIMARY KEY (entity_lc, kind, doc_name)
);
```

Index at `{vault}/.memcon/entities.db`.

## Public API

`index_note()` / `clear_doc()` / `lookup()` / `stats()`. All in
[[memory.entity_index]].

## Where the entities come from

[[Multi-pass extraction]] Pass 3 — `extractor.extract_entities()`. Or, on
migration, [[scripts.migrate_to_v3_1]] uses regex fallback if Ollama isn't
available.

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 3.

## Related
- [[Why SQLite for entity index]]
- [[Hybrid retrieval]]
- [[Multi-pass extraction]]
- [[memory.entity_index]]
""")

N("features/Hybrid retrieval.md", ["feature", "v3.1"], """
# Hybrid retrieval

[[memory.retrieve|memory.retrieve.query]] merges results from two
sources and reranks:

1. **Semantic** — [[Qdrant]] cosine similarity over [[Embeddings]]
2. **Entity** — [[Entity index]] exact / substring matches

Entity hits get a small score boost added to their semantic score. Notes
that surface in *both* searches get the strongest signal.

## Output shape

Same as the v1 semantic-only contract (so old callers keep working), plus:

- `via` — "semantic" | "entity" | "both"
- `entity_hits` — list of `{entity, kind, token}` matches

## Tunables

In [[memory.retrieve]]:
- `ENTITY_BOOST_FACTOR = 0.15` — per matched token
- `MAX_ENTITY_BOOST = 0.45` — cap
- `ENTITY_ONLY_FLOOR = 0.30` — base score for entity-only hits

## What it fixes

Pre-v3.1, asking about `servo.cpp` relied entirely on the cosine match
to that filename embedded inside other text. Often missed. Now: exact
substring of `servo.cpp` in any note's entity list = guaranteed hit.

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 3.

## Related
- [[memcon_query]] · [[memcon_ask]] benefit automatically
- [[Entity index]]
- [[Semantic search]]
- [[Qdrant]]
""")

N("features/Auto-enrichment.md", ["feature", "v3.1"], """
# Auto-enrichment

[[memory.enricher]] spawns a daemon thread after every write to add
two things without blocking the caller:

1. **Git context** — `git rev-parse HEAD` + branch + recently-changed
   files, patched into the note's frontmatter as a `git:` block
2. **`## See also`** — for each linked neighbour, read its TL;DR (or
   first prose line under H1) and append a bullet with the one-liner

## Why background

Write tools should return *instantly* to keep [[Claude (Anthropic)]]'s
loop snappy. Enrichment is opportunistic — if it fails, the note's still
fully valid.

## Where it looks for the project root

In order:
1. `$MEMCON_PROJECT_ROOT`
2. CWD (if not `/` — the [[cwd is slash on macOS sandbox]] case)
3. The vault's parent directory
4. The vault itself

## Shipped

[[v3.1 — Rich notes, hybrid recall]] — Layer 4.

## Related
- [[Why background enrichment]]
- [[memory.enricher]]
- [[Auto-wikilinks on write]] — runs synchronously inside the write
""")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENTS (~18)
# ═══════════════════════════════════════════════════════════════════════════════

COMPONENTS = [
    ("config.py", "config", "Loads `memcon.config.yaml` and applies env-var overrides.",
     """`get_config()` is called once and cached. Critical bit: it **absolutizes**
the vault path against the config file's location so it works under the
[[cwd is slash on macOS sandbox]] case. Env vars override `vault.path`,
`memory.collection`, `llm.model` ([[Multi-project switching]]).""",
     ["Multi-project switching", "cwd is slash on macOS sandbox", "memcon.config.yaml"]),
    ("memcon.config.yaml", "config", "The single config file.",
     """Top-level keys: `project`, `vault`, `memory`, `llm`, `qdrant`, `api`,
`subsystems`, `memory_types`. v3.1 added `note_kinds` and
`entity_categories` as informational sections.""",
     ["config.py", "Subsystems", "Note kinds"]),
    ("memory.templates", "memory", "Renders v3.1 note templates.",
     """Exports `ALL_KINDS` (the 8 valid [[Note kinds]]), `FOLDER_FOR` (kind →
vault folder), `SECTIONS_FOR` (kind → ordered section list), and the
core `render(kind, title, fields, meta)` function. Also `make_frontmatter()`
for building the YAML block.""",
     ["Universal note schema", "Note kinds", "memory.writer"]),
    ("memory.writer", "memory", "Canonical write API.",
     """`log_universal(kind, title, fields, …)` is the entry. Back-compat
wrappers: `log_debug` / `log_decision` / `log_experiment` /
`log_concept` / `log_reference` / `log_meeting` / `log_breakthrough` /
`summarise_session`. All route through `log_universal` which:
1. resolves [[Auto-wikilinks on write|related neighbours]],
2. renders via [[memory.templates|templates.render]],
3. writes to `{vault}/{folder}/{slug}.md`,
4. ingests into [[Qdrant]] via [[ingestion.ingest]],
5. updates the [[Entity index]],
6. spawns [[memory.enricher|enrich_async]] for background polish.""",
     ["Universal note schema", "memory.templates", "Auto-enrichment",
      "Auto-wikilinks on write", "Entity index"]),
    ("memory.extractor", "memory", "Multi-pass LLM extraction.",
     """4 functions: `classify_type` / `extract_structure` / `extract_entities` /
`self_critique`. All use [[Ollama]] JSON mode. Single public entry
`extract(text, hint='auto', run_critique=False) → dict` returns the
extraction ready to feed into [[memory.writer|log_universal]].""",
     ["Multi-pass extraction", "memcon_capture", "Ollama", "Why multi-pass extraction"]),
    ("memory.entity_index", "memory", "SQLite inverted index of entities → notes.",
     """`index_note()` to write, `clear_doc()` to wipe a doc's entries,
`lookup(query)` to retrieve. Tokenizer pulls dotted paths, CamelCase,
quoted strings, URLs, error-code shapes from a freeform query.
Stopword filter to avoid generic matches.""",
     ["Entity index", "Hybrid retrieval", "Why SQLite for entity index"]),
    ("memory.enricher", "memory", "Background daemon for git context + see-also lines.",
     """`enrich_async(filepath, kind, title, related)` spawns a thread and returns
immediately. The thread re-reads the file, runs `git rev-parse HEAD` +
friends from the inferred project root, generates a `## See also` block
from each related note's TL;DR, rewrites the file, re-ingests.""",
     ["Auto-enrichment", "Why background enrichment"]),
    ("memory.retrieve", "memory", "Hybrid query layer.",
     """`query(text, top_k, subsystem)` is the public entry — merges
[[memory.qdrant_store|Qdrant]] semantic hits with [[memory.entity_index|entity]] hits
and reranks. Also exposes `query_semantic()` and `query_entities()`
for callers that want one or the other in isolation.""",
     ["Hybrid retrieval", "memory.qdrant_store", "memory.entity_index", "Semantic search"]),
    ("memory.qdrant_store", "memory", "Qdrant client + helpers.",
     """`ensure_collection()` creates the collection on first use. `upsert_chunks()`
takes `(chunks, vectors)` and writes them with UUID-5 deterministic IDs.
`search(vec, top_k, subsystem)` returns hits with payload. `get_stats()`
for diagnostics. Uses `MEMCON_QDRANT_HOST` / `_PORT` env overrides.""",
     ["Qdrant", "memory.retrieve", "ingestion.ingest"]),
    ("memcon_mcp.server", "mcp", "The MCP stdio server. 16 tools registered.",
     """Built on [[FastMCP]]. Each tool is a `@mcp.tool()`-decorated function
with a docstring that becomes the tool's description (which Claude reads
to decide when to call it). The docstrings are heavily tuned — they're
the API surface for an LLM, not for humans.""",
     ["MCP Server", "FastMCP", "Model Context Protocol (MCP)"]),
    ("ingestion.ingest", "ingestion", "Top-level `ingest_file(path)`.",
     """Calls [[ingestion.chunker]] to split, [[ingestion.embedder]] to vectorise,
[[memory.qdrant_store|qdrant_store.upsert_chunks]] to store. Idempotent
thanks to deterministic UUID-5 IDs.""",
     ["ingestion.chunker", "ingestion.embedder", "memory.qdrant_store"]),
    ("ingestion.chunker", "ingestion", "Per-filetype chunking strategy.",
     """`chunk_file(path)` dispatches: `.md` → markdown chunks, `.py`/`.ts`/etc
→ 80-line code windows, `.pdf` → page-by-page via `pypdf`. Each chunk
gets a stable `chunk_id` that downstream IDs hash on.""",
     ["Code ingestion", "PDF ingestion", "ingestion.ingest"]),
    ("ingestion.embedder", "ingestion", "Sentence-transformers wrapper.",
     """One function: `embed(texts) → list[list[float]]`. Loads
`all-MiniLM-L6-v2` once, runs batches. 384-dim output — matches the
[[Qdrant]] collection dim. See [[Bespoke embedding model]] for why we
didn't go custom.""",
     ["Sentence Transformers", "Embeddings", "Qdrant", "Bespoke embedding model"]),
    ("ingestion.watcher", "ingestion", "Auto-ingests vault changes.",
     """Watchdog-based observer on `vault/`. When a `.md` changes,
re-runs [[ingestion.ingest|ingest_file]]. Lets you edit notes in
[[Obsidian]] and have memcon's index update without restarting anything.""",
     ["Obsidian", "ingestion.ingest"]),
    ("api.main", "api", "FastAPI app at :8000.",
     """Routes for `/ui` (the dashboard), `/memory/ask`, `/memory/query`,
`/memory/recent`, `/memory/save`, plus stats. Used by the
[[VS Code extension]] (which talks to it over HTTP from the editor process)
and the browser dashboard.""",
     ["api.ui.html", "VS Code extension"]),
    ("api.ui.html", "api", "The browser dashboard.",
     """Single-file HTML/CSS/JS that the FastAPI server serves at `/ui`.
The chat-style interface — input at the bottom, message list above.
Iterated through [[UI v0 — Monochrome serif]] → [[UI v1 — Claude chat style]].""",
     ["api.main", "UI v1 — Claude chat style"]),
    ("scripts.register_mcp", "script", "Patches Claude Desktop's config.",
     """Idempotent. Reads the user's `claude_desktop_config.json`, adds the
`memcon` MCP server block with an absolute path to the venv's python
+ absolute path to `memcon_mcp/server.py` (NOT the `-m module` form —
that doesn't survive [[Claude Desktop ignores cwd|sandboxing]]).""",
     ["Claude Desktop", "MCP Server", "Claude Desktop ignores cwd"]),
    ("scripts.migrate_to_v3_1", "script", "Backfills legacy notes into v3.1 schema.",
     """Walks the vault, parses old frontmatter + body, infers kind from
folder name + memory_type, lifts old `## Heading` sections into v3.1
field names, runs entity extraction (LLM or regex), re-ingests.
Idempotent, backed-up-by-default, dry-run mode.""",
     ["v3.1 — Rich notes, hybrid recall", "Universal note schema",
      "Entity index", "Multi-pass extraction"]),
    ("scripts.ingest_code", "script", "Ingest a project tree.",
     """`python3 -m scripts.ingest_code <path>`. Walks the tree, respects
`.gitignore`-style exclusions, batches files through [[ingestion.ingest]].""",
     ["Code ingestion", "ingestion.ingest"]),
    ("scripts.ingest_git", "script", "Ingest the most recent commit (called by post-commit hook).",
     """Reads `git log -1` for SHA/message/author/files, writes a tiny
markdown chunk under `vault/git/`, [[ingestion.ingest|ingests]] it.""",
     ["Git auto-ingest", "ingestion.ingest"]),
    ("bootstrap.sh", "script", "macOS / Linux / WSL one-line installer.",
     """The canonical install path: `curl … | bash`. Installs Docker if missing,
brings up [[Qdrant]] + [[Ollama]], picks a model from the RAM tier,
patches the [[Claude Desktop]] config via [[scripts.register_mcp]].""",
     ["install.sh", "scripts.register_mcp", "v1.0 — Plug into Claude"]),
    ("bootstrap.ps1", "script", "Windows PowerShell counterpart of bootstrap.sh.",
     """Same shape, PowerShell-native. `iwr -useb … | iex` is the canonical
install one-liner on Windows. Shipped in [[v1.0 — Plug into Claude]].""",
     ["bootstrap.sh", "install.sh"]),
    ("install.sh", "script", "The body of bootstrap.sh — does the actual work.",
     """Where [[sed regex hit embedding_model|the sed bug]] lived briefly. The
fix anchored the substitution to `^  model:` (line-start + two spaces).
Otherwise it would silently corrupt `embedding_model: "..."` lines too.""",
     ["sed regex hit embedding_model", "bootstrap.sh"]),
    ("vscode extension source", "editor", "The VS Code extension TypeScript.",
     """Lives in `vscode/`. TypeScript compiled with `tsc`, packaged with
`vsce package --no-dependencies`. ~9 KB VSIX. Works in both [[VS Code]]
and [[Cursor]] without changes — Cursor reads VS Code extensions natively.""",
     ["VS Code extension", "VS Code", "Cursor"]),
]

for name, kind_tag, summary, prose, related_list in COMPONENTS:
    rel_links = "\n".join(f"- [[{r}]]" for r in related_list)
    N(f"components/{name}.md", ["component", kind_tag], f"""
# {name}

**{summary}**

{prose}

## Related
{rel_links}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# CONCEPTS (~14)
# ═══════════════════════════════════════════════════════════════════════════════

CONCEPTS = [
    ("Model Context Protocol (MCP)", "An open protocol from Anthropic for LLMs to call tools.",
     """A JSON-RPC dialect that lets an LLM client (like [[Claude Desktop]],
[[Cursor]], or Claude Code) discover and invoke "tools" exposed by a
server. Servers can be local processes (stdio transport) or remote
(SSE / HTTP). Memcon ships as a stdio server — see [[MCP Server]].

Without MCP, integrating a memory store into Claude meant either a
custom client or copy-paste into the chat. With MCP, you register the
server once and Claude treats memcon's read/write functions as native
tools it can decide to use.""",
     ["MCP Server", "FastMCP", "Claude Desktop", "Why MCP not REST"]),
    ("Semantic search", "Retrieval by meaning, not keywords.",
     """Embed the query, embed the documents, cosine-similarity-match.
What you get: "weird motor error" finds a note about "servo torque
loss" even though no keyword overlaps. What you lose: exact-string
recall (the note that literally mentions `servo.cpp`). That's why v3.1
added [[Hybrid retrieval]] alongside.""",
     ["Embeddings", "Hybrid retrieval", "Qdrant", "RAG"]),
    ("Embeddings", "Dense numeric vectors that encode meaning.",
     """Memcon uses [[Sentence Transformers]]' `all-MiniLM-L6-v2` —
384-dimensional vectors per chunk. Stored in [[Qdrant]] with cosine
distance. Cheap (~ms per chunk on CPU), good enough for the project's
scale. Bespoke embedding models considered + rejected
([[Bespoke embedding model]]).""",
     ["Sentence Transformers", "Qdrant", "Semantic search"]),
    ("Qdrant", "The vector database memcon uses.",
     """Open-source, Rust-core, runs in Docker on `:6333`. Memcon writes to
collection `memcon_memory` (configurable via `MEMCON_COLLECTION` —
see [[Multi-project switching]]). Picked over alternatives for the
[[Why Qdrant not pgvector|local-first reasons documented separately]].""",
     ["Why Qdrant not pgvector", "memory.qdrant_store", "Embeddings", "Local-first"]),
    ("Ollama", "Local LLM runtime memcon talks to.",
     """OpenAI-compatible HTTP server on `:11434`. Memcon talks to it via
the `openai` Python client with `base_url=http://localhost:11434/v1`.
Models tier from `llama3.2:1b` (1.3 GB RAM) up to `qwen2.5-coder:32b`
(20 GB) — installer picks based on detected RAM. Used by
[[memcon_ask]], [[memcon_digest]], and the four passes of
[[Multi-pass extraction]].""",
     ["memory.extractor", "memcon_ask", "Local-first", "Why local LLM not cloud"]),
    ("FastMCP", "Python framework for building MCP servers.",
     """The `mcp` package's high-level decorator API. Memcon uses it like:
```python
mcp = FastMCP("memcon")

@mcp.tool()
def memcon_query(query: str, top_k: int = 5) -> dict:
    \"\"\"docstring becomes the tool description Claude reads\"\"\"
    ...
```
The docstring is the *user manual* for the LLM. Memcon's are heavily tuned.""",
     ["MCP Server", "Model Context Protocol (MCP)", "memcon_mcp.server"]),
    ("Sentence Transformers", "Library for sentence/paragraph embeddings.",
     """Memcon uses `all-MiniLM-L6-v2` — fast, 384-dim, MIT-licensed, runs
on CPU. Loaded once in [[ingestion.embedder]], reused for every
[[Code ingestion|code]] / [[PDF ingestion|PDF]] / note chunk + every query.
See [[Bespoke embedding model]] for why this is enough.""",
     ["Embeddings", "ingestion.embedder", "Qdrant", "Bespoke embedding model"]),
    ("Obsidian", "Markdown editor with backlinks and a graph view.",
     """Memcon's vault format is just Obsidian-compatible markdown. Notes
get auto-generated [[Wikilinks]] to semantic neighbours
([[Auto-wikilinks on write]]) and to one-liner summaries of those
neighbours ([[Auto-enrichment]]). Open the vault in Obsidian, you see
the graph. THIS very vault is exactly that pattern, applied to the
project itself.""",
     ["Wikilinks", "Auto-wikilinks on write", "Why Obsidian markdown"]),
    ("Wikilinks", "The double-bracket syntax for cross-references.",
     """Obsidian convention. Every double-bracketed note name in a note shows
up as a backlink on the linked note's page and as an edge in the graph view.
Memcon writes them automatically — top-3 semantic neighbours under
`## Related`, then one-liner summaries under `## See also`.""",
     ["Obsidian", "Auto-wikilinks on write", "Auto-enrichment"]),
    ("Local-first", "The fundamental product stance.",
     """Everything memcon needs to function runs on the user's machine:
[[Qdrant]], [[Ollama]], the [[Sentence Transformers|embedder]], the
[[MCP Server]]. No API keys, no SaaS, no telemetry. The user's
engineering history never leaves their disk. This is the value prop —
trading some convenience (you need Docker) for full data ownership.""",
     ["Why local LLM not cloud", "SaaS-first version", "Telemetry phone-home"]),
    ("RAG", "Retrieval-Augmented Generation.",
     """The pattern: pull relevant context from a store, paste it into the
LLM's prompt, generate an answer grounded in that context. [[memcon_ask]]
is RAG. [[memcon_query]] is the *retrieval* half exposed as a tool so
[[Claude (Anthropic)|Claude]] can do its own augmentation. Memcon is
*selective* about being called RAG because the project is more than
that — see [[MCP Server]].""",
     ["memcon_ask", "memcon_query", "Semantic search", "Hybrid retrieval"]),
    ("Hybrid retrieval", "Semantic + entity-exact, merged.",
     """The v3.1 retrieval mode. Vectors give fuzzy meaning-based recall;
the [[Entity index]] gives exact-string recall. Merged and reranked in
[[memory.retrieve|memory.retrieve.query]]. Both [[memcon_query]] and
[[memcon_ask]] benefit automatically.""",
     ["Entity index", "Semantic search", "memory.retrieve"]),
    ("Note kinds", "The 8 types a note can be.",
     """`debug` / `decision` / `experiment` / `concept` / `reference` /
`meeting` / `breakthrough` / `session`. Each has its own middle-section
schema; the outer shape (TL;DR / Context / Related / See also) is
shared. Defined in [[memory.templates|memory.templates.ALL_KINDS]].
[[memcon_capture]]'s classifier picks one per write; explicit
`memcon_write_*` tools force a kind.""",
     ["Universal note schema", "memory.templates", "memcon_capture"]),
    ("Subsystems", "Soft-constrained tags for grouping notes by area.",
     """Pre-v3.1 was a strict list from `memcon.config.yaml` (servo / imu /
gait / power / etc. — BARQ-shaped). v3.1 made it optional: if the
config's `subsystems:` list is empty, memcon accepts any free-form
string. The [[Multi-pass extraction|extractor]] still uses the list as
a soft hint to the [[Ollama|LLM]] when present.""",
     ["memcon.config.yaml", "memcon_subsystems", "BARQ (the robot)"]),
]

for name, summary, prose, related_list in CONCEPTS:
    rel_links = "\n".join(f"- [[{r}]]" for r in related_list)
    N(f"concepts/{name}.md", ["concept"], f"""
# {name}

**{summary}**

{prose}

## Related
{rel_links}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN DECISIONS (~13)
# ═══════════════════════════════════════════════════════════════════════════════

DECISIONS = [
    ("Why MCP not REST", "v1.0",
     """If memcon were a REST API, the user would have to know to use it —
they'd open a UI, type a query, copy the answer back. That's friction.

With [[Model Context Protocol (MCP)]], memcon's functions are *tools*
Claude can decide to invoke autonomously. The reflex shortens to "ask
Claude" — Claude does the memory lookup as part of the answer. Memcon
disappears into the background.

The trade-off: MCP is narrower than REST (no browser clients, only
MCP-aware LLM clients). For memcon's design centre — augmenting an
LLM — that's exactly the constraint we want.""",
     ["MCP Server", "Model Context Protocol (MCP)", "v1.0 — Plug into Claude"]),
    ("Why Qdrant not pgvector", "v1.0",
     """pgvector would have meant pulling Postgres in as a hard dependency
just to serve as the vector store. The install footprint goes from
"Docker + Python" to "Docker + Postgres + Python + pgvector extension."

[[Qdrant]] is purpose-built: Rust core, fast cold start, low RAM at
memcon's scale, runs alongside [[Ollama]] in a single Docker network.
The qdrant-client Python package is well-maintained.

Chroma was the other obvious candidate — Qdrant won on the persistence
story (Chroma's defaults at the time were less mature) and on the
gRPC option for future scale.""",
     ["Qdrant", "Local-first", "memory.qdrant_store"]),
    ("Why local LLM not cloud", "v1.0",
     """The whole product is "your project's memory never leaves your
machine." If the LLM is cloud — OpenAI, Anthropic, anywhere — then
every query sends your project's context (the retrieved chunks) to a
third party. The local-first promise dies.

[[Ollama]] keeps everything local. Slower than GPT-4, but for
extraction tasks ([[Multi-pass extraction]]) qwen-coder-7b is plenty.
For [[memcon_ask]]'s grounded answers, it's fine — most of the value
is in the retrieved context, not the model's prose.""",
     ["Local-first", "Ollama", "SaaS-first version"]),
    ("Why Obsidian markdown", "v1.0",
     """Three reasons:
1. **Portable.** A vault is a folder of `.md` files. If memcon ever
   disappeared, the user's notes are still readable in any text editor.
2. **Free graph view.** Obsidian's existing graph + backlinks UI
   becomes memcon's frontend for free.
3. **Hackable.** Users can edit notes by hand without going through
   memcon — the [[ingestion.watcher|watcher]] picks up changes and
   re-ingests.

The alternative was a proprietary store (SQLite blobs, MongoDB).
Locked-in storage = the wrong stance for a tool whose value prop is
data ownership.""",
     ["Obsidian", "Wikilinks", "Local-first", "ingestion.watcher"]),
    ("Why monochrome only", "ui-design",
     """The landing page (and later the chat UI) went through a red phase —
hot red accent borrowed from Audi×Sirnik. Looked dense, but the red
fought with the type. The eye landed on the red instead of the words.

Pure mono — black background, white text, a ladder of grays — lets the
typography do all the talking. Editorial design works because the
*letters* are the visual content. Adding color undoes that.

See [[Five rules of the editorial system]].""",
     ["Five rules of the editorial system", "UI v3 — Sirnik editorial final",
      "UI v2 — Audi-Sirnik red", "DESIGN.md — the design system"]),
    ("Why no bordered cards", "ui-design",
     """The first landing page used "feature cards" — bordered boxes with
bracket-corner decorations. Generic. SaaS-template aesthetic.

The redesign replaced every card with row-lists separated by 1px
dividers and pure typography. Density without chrome. The eye scans
*rows*, not *boxes*.

It also forces tighter writing: a row can't be a 200-word card. It has
to be 1–2 sentences. Constraint as a writing tool.""",
     ["Five rules of the editorial system", "UI v3 — Sirnik editorial final",
      "DESIGN.md — the design system"]),
    ("Why different interaction per section", "ui-design",
     """The previous landing relied on the same "flowing bounding box"
motif across every section. Felt template-y.

The redesign uses a different micro-interaction per section: cursor
crosshair on the hero, live clock in the philosophy row, accordion on
the loop, hover-side-panel on the tool wall, OS-tab switcher on the
install. Variety per section = the page feels alive without needing
animation gimmicks.""",
     ["Five rules of the editorial system", "UI v3 — Sirnik editorial final",
      "DESIGN.md — the design system"]),
    ("Why preserve raw context", "v3.1",
     """The old 4-field schema (title / symptom / cause / fix) discarded the
200-line debugging conversation that produced it. So the [[Embeddings|embedding]]
saw 80 words. Bad embeddings = bad [[Semantic search|recall]].

v3.1 added `## Context` — a verbatim excerpt (~1200 chars) preserved on
every note. The embedder finally has real prose to grip onto. Recall
quality jumps overnight when you migrate.

Trade: notes are longer on disk. Worth it.""",
     ["v3.1 — Rich notes, hybrid recall", "Universal note schema",
      "Multi-pass extraction", "Embeddings"]),
    ("Why multi-pass extraction", "v3.1",
     """Small local models like qwen-coder-7b struggle with prompts that
ask too much. A single "classify + extract + entity-tag" prompt
produced inconsistent JSON.

Decomposing into focused sub-tasks (each with its own narrow schema
+ JSON mode) makes each pass simple enough to be reliable. The price
is runtime: ~30–60s instead of ~15s for a single shot. Acceptable for
a write operation.

Plus: future-proof. The optional `self_critique` pass costs nothing
to add structurally.""",
     ["Multi-pass extraction", "memory.extractor", "Ollama", "v3.1 — Rich notes, hybrid recall"]),
    ("Why SQLite for entity index", "v3.1",
     """The [[Entity index]] is small (one row per (entity, kind, doc)),
read-heavy, and per-vault. Three options were on the table:

1. **A second [[Qdrant]] collection** — overkill; vectors are
   irrelevant for exact-match lookup.
2. **A JSON file** — works at small scale, but loading + scanning the
   whole thing per query is O(n).
3. **SQLite** — zero-dependency for Python, gives indexes, transactions,
   WAL, all the basics. File lives at `{vault}/.memcon/entities.db`
   so [[Multi-project switching]] just works.

SQLite won. Schema is two indexes + one PRIMARY KEY.""",
     ["Entity index", "memory.entity_index", "Multi-project switching"]),
    ("Why background enrichment", "v3.1",
     """Write tools should return immediately to keep [[Claude (Anthropic)|Claude]]'s
loop snappy. But there are nice-to-have additions to a note that need
extra work: a `git rev-parse HEAD` call (slow if the repo is huge), and
reading neighbours to generate `## See also` lines.

Solution: kick a daemon thread after the write returns. The note is
fully valid before the thread runs — if it fails, no harm. The user
sees the polish on their next visit to the note in [[Obsidian]].""",
     ["Auto-enrichment", "memory.enricher"]),
    ("Why universal schema", "v3.1",
     """The pre-v3.1 schema was shaped for hardware debugging — symptom,
cause, fix. That's a great template for a [[BARQ (the robot)|BARQ]]
debug session. It's a *terrible* template for:
- "we decided to use Postgres" (a decision)
- "what is a JWT refresh token?" (a concept)
- "we tried int8 quant on the IK model" (an experiment)

Forcing all of those into symptom/cause/fix loses the structure that
makes each type useful. The universal schema gives each kind its own
middle sections while sharing the outer shape (TL;DR / Context /
Related / See also).""",
     ["Universal note schema", "Note kinds", "BARQ (the robot)"]),
    ("Why MIT licensed", "values",
     """MIT means "do whatever, just preserve the copyright." No copyleft
obligations on derivatives. Companies can adopt memcon without legal
review. Forks can ship without giving anything back.

The alternative — source-available with a non-compete clause — would
have made memcon "free except if you want to host it." That'd be a
SaaS-protection move, but memcon's whole stance is [[Local-first]] —
there's no SaaS to protect.

Sponsorship is a tipjar, not a paywall. See [[Paid pro tier]].""",
     ["Local-first", "Paid pro tier", "SaaS-first version"]),
]

for name, version_tag, prose, related_list in DECISIONS:
    rel_links = "\n".join(f"- [[{r}]]" for r in related_list)
    N(f"design-decisions/{name}.md", ["design-decision"], f"""
# {name}

*Decided during: {version_tag}*

{prose}

## Related
{rel_links}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# UI REDESIGNS (~6)
# ═══════════════════════════════════════════════════════════════════════════════

N("ui-design/UI v0 — Monochrome serif.md", ["ui"], """
# UI v0 — Monochrome serif

**First pass.** The chat UI in [[api.ui.html]] tried to look like Claude's
chat interface but in serif. Times New Roman or similar. Heavy italics
for emphasis.

## Why it failed

> "It's too italicised, plus just like claude interface has a textbox below,
> with various options on the side"
> — [[Aryaman (aryasgit)]]

Two problems:
1. Serif at body size felt heavy and old-fashioned, not literary.
2. The composition didn't match what [[Claude (Anthropic)|Claude]] users expected:
   they want a bottom textbox with messages above, not a serif essay layout.

## What replaced it

[[UI v1 — Claude chat style]] — Inter sans, bottom composer, message list above.

## Related
- [[api.ui.html]]
- [[UI v1 — Claude chat style]]
""")

N("ui-design/UI v1 — Claude chat style.md", ["ui"], """
# UI v1 — Claude chat style

**Direct response to [[UI v0 — Monochrome serif]] failing.** Switched to
the [[Claude Desktop|Claude]]-style layout: textbox at the bottom,
messages scroll above, sans-serif body.

## What it kept from v0

Monochromatic palette. The chat UI never got a color accent — it
predicted the eventual [[Why monochrome only|landing-page decision]] by
several iterations.

## What it added

- Inter/Roboto-style sans body
- Bottom-anchored composer with submit-on-enter
- Side controls (clear, settings, etc.)
- Message bubbles styled like Claude's

## Where it lives

[[api.ui.html]], served by [[api.main]] at `/ui`.

## Related
- [[api.ui.html]] · [[api.main]]
- [[UI v0 — Monochrome serif]]
- [[UI v3 — Sirnik editorial final]] — landing page eventually arrived at the same place
""")

N("ui-design/UI v2 — Audi-Sirnik red.md", ["ui", "reverted"], """
# UI v2 — Audi-Sirnik red

**A detour.** The landing page got a hot red (`#ED2939`) accent — Audi F1
inspired — with Anton display type, "cluttered but pretty" editorial
density.

## Why it was tried

> "honestly this one particular shade of red along with black and white
> would look very poppy"
> — [[Aryaman (aryasgit)]]

Density of information per viewport, treated like a broadsheet. Red as
the eye-catching accent on the brand wordmark + key CTAs.

## Why it was reverted

It looked striking. But the red kept fighting with the typography for
attention. The "MEMCON." headline read as red-first, word-second. The
typography lost.

## What replaced it

Reverted via `git reset --hard e1c46e8` back to the pre-redesign state,
then a full re-redesign as [[UI v3 — Sirnik editorial final]] — same
density, pure monochrome.

## Related
- [[UI v3 — Sirnik editorial final]]
- [[Why monochrome only]]
- [[Sirnik (design reference)]]
""")

N("ui-design/UI v3 — Sirnik editorial final.md", ["ui", "shipped"], """
# UI v3 — Sirnik editorial final

**The landing page as it stands.** Pure monochrome, [[Sirnik (design reference)|Sirnik]]-inspired
editorial. 1100+ lines, ~90 elements, zero bordered cards.

## Design language

- **Type:** Inter Tight (display + body), JetBrains Mono (code + labels)
- **Color:** monochrome only — 9-shade gray ladder, one green pulse on the
  live indicator
- **Grid:** signature 1.1fr / 1.6fr / 1fr 3-column for nav + philosophy row
- **No cards.** Sections are demarcated by 1px lines and typography.
- **Different micro-interaction per section** — cursor crosshair / live
  clock / accordion / hover-side-panel / OS tabs / marquee

## What landed

- 8 sections, each with its own interaction pattern
- Tool wall: hover any of 12 MCP tools → side panel updates with description
- Faux-IDE in the editor section with syntax highlight in grayscale
- Giant `MEMCON` wordmark in the footer with a vault-screenshot cut

## Codified as

[[DESIGN.md — the design system]] — extracted as a portable reference for
future projects.

## Related
- [[Five rules of the editorial system]]
- [[DESIGN.md — the design system]]
- [[Why monochrome only]] · [[Why no bordered cards]] · [[Why different interaction per section]]
- [[Sirnik landing redesign shipped]]
- [[Sirnik (design reference)]]
""")

N("ui-design/DESIGN.md — the design system.md", ["ui", "doc"], """
# DESIGN.md — the design system

A portable reference doc capturing the design language from
[[UI v3 — Sirnik editorial final]] + the chat UI. 723 lines, 10 sections.
Lives at the repo root: `/Users/barq/BARQ/engram/DESIGN.md`.

## Sections

1. Philosophy (the 5 rules — see [[Five rules of the editorial system]])
2. Typography — three families, full type scale, letter-spacing table
3. Color palette — dark + light themes, 14 vars, the "contrast ladder"
4. Layout & spacing — container, signature 1.1/1.6/1 grid
5. Components — 10 copy-paste blocks
6. Interactions — 10 patterns to pick from (the "different per section" menu)
7. Anti-patterns — 12 things that break the system
8. Adapting to a new app — 5-step recipe with section-archetype mapping
9. Quick-start CSS — paste-block to bootstrap a new HTML file
10. One-line summary — the tweet-length version

## Why this exists

After two ground-up redesigns in two days, the project deserved a
codified language — so the third application doesn't have to reverse-
engineer the first two. Future projects can adopt the system cold.

## Related
- [[UI v3 — Sirnik editorial final]]
- [[Five rules of the editorial system]]
- [[Design system extracted]]
- [[Why monochrome only]] · [[Why no bordered cards]] · [[Why different interaction per section]]
""")

N("ui-design/Five rules of the editorial system.md", ["ui", "principle"], """
# Five rules of the editorial system

From [[DESIGN.md — the design system]] §1. Break any of them and the
look collapses.

## 1. Monochrome only
Black background, white text, a handful of grays. No accent color
anywhere — not even on the CTA. Confidence in typography replaces
color. ([[Why monochrome only]])

## 2. No bordered cards
No rounded corners. No drop shadows. No bracket-corner decorations.
Sections are demarcated by **1px lines** and negative space, never by
boxes. ([[Why no bordered cards]])

## 3. Massive display next to tiny micro-labels
The contrast is between `clamp(2.5rem, 7vw, 6rem)` Inter Tight and
`0.66rem` uppercase tracking-`.16em` labels. Mid-sized headings (h3,
h4) are rare.

## 4. Editorial multi-column grids
Default to **3 columns** (`1.1fr 1.6fr 1fr`) even for things that "want"
to be centered. Forces the eye to scan.

## 5. Different interaction per section
Hover-shift on links, accordion on step-lists, side-panel reveal on
tool walls, OS-tabs on installs, live clock in headers. Never reuse the
same pattern twice on the same page. ([[Why different interaction per section]])

## Related
- [[DESIGN.md — the design system]]
- [[UI v3 — Sirnik editorial final]]
- [[Why monochrome only]] · [[Why no bordered cards]] · [[Why different interaction per section]]
""")


# ═══════════════════════════════════════════════════════════════════════════════
# BUGS AND FIXES (~7)
# ═══════════════════════════════════════════════════════════════════════════════

BUGS = [
    ("sed regex hit embedding_model",
     "`sed 's|model: \".*\"|...|'` in [[install.sh]] matched substring inside `embedding_model: \"...\"` too.",
     """The original sed substitution wasn't anchored:
```
sed 's|model: ".*"|model: "qwen2.5-coder:7b"|'
```
Which matches both `model: "..."` AND `embedding_model: "..."` because
the second contains the first as a suffix.

Result: the LLM model installation worked, but `embedding_model` got
silently rewritten too — to a string that wasn't a valid Hugging Face
model name. First user to run it got HFValidationError on first ingest.

**Fix:** anchor to the line start + the exact two-space indent:
```
sed 's|^  model: ".*"|  model: "qwen2.5-coder:7b"|'
```

**Lesson:** `.*` in sed is dangerous — anchor every substitution to
line-start unless you specifically want substring matching.""",
     ["install.sh", "bootstrap.sh"]),
    ("openai missing from requirements",
     "[[api.main]] and [[memcon_mcp.server]] both `from openai import OpenAI`, but `openai` wasn't in requirements.txt.",
     """Both modules use the `openai` Python client to talk to
[[Ollama]] (which exposes an OpenAI-compatible API). Worked locally
during development because it was installed for unrelated reasons.

When the first external user installed memcon fresh: `ModuleNotFoundError:
No module named 'openai'`.

**Fix:** add `openai==2.38.0` to `requirements.txt`. Pin to a known-good
version because the OpenAI client breaks compat often.

**Lesson:** transitive deps that "happen to be there" on the dev's
machine are landmines. Audit imports against requirements before each
external release.""",
     ["api.main", "memcon_mcp.server", "Ollama"]),
    ("cwd is slash on macOS sandbox",
     "[[Claude Desktop]] launches MCP servers with `cwd=/` (the root). Relative paths exploded.",
     """Memcon's `memcon.config.yaml` had `vault.path: ./vault` — relative
to the config file's directory.

When [[Claude Desktop]] launched the MCP server on macOS, it set `cwd=/`
because of the app sandbox. `./vault` resolved to `/vault` (read-only,
nonexistent). Every write failed with `[Errno 30] Read-only file system`.

**Fix:** in [[config.py]] `get_config()`, after loading the YAML, if
`vault.path` isn't absolute, resolve it against the config file's
directory:
```python
if vp and not Path(vp).is_absolute():
    project_root = config_path.parent.resolve()
    vault['path'] = str((project_root / vp).resolve())
```

**Lesson:** never trust CWD inside a sandboxed subprocess. Absolutize
everything at config-load time.""",
     ["Claude Desktop", "config.py", "Claude Desktop ignores cwd"]),
    ("stdout pollution corrupts JSONRPC",
     "Various modules used `print()` for logging. MCP stdio = stdout for JSONRPC. Print → corruption.",
     """[[ingestion.embedder]], [[ingestion.chunker]], [[ingestion.ingest]],
[[memory.qdrant_store]] all had `print()` calls scattered for diagnostics.

Worked fine via the HTTP API ([[api.main]]). Catastrophic via MCP:
every print interleaved into the JSONRPC stream → Claude Desktop showed
"Server disconnected" within seconds of any operation.

**Fix:** redirect every `print()` to stderr via `file=sys.stderr`. MCP
servers must keep stdout *pristine* for protocol messages only.

**Lesson:** the moment a process is invoked over stdio for an RPC, every
non-protocol byte on stdout is a bug. Even legitimate logs.""",
     ["MCP Server", "Claude Desktop", "ingestion.ingest"]),
    ("Claude Desktop ignores cwd",
     "Even when the MCP config specified `cwd` + `env.PYTHONPATH`, Claude Desktop ignored both. `-m module` form broke.",
     """Initial MCP config used the standard `python3 -m memcon_mcp.server`
form, with `cwd: /Users/barq/BARQ/engram` and
`env.PYTHONPATH: /Users/barq/BARQ/engram` to make the module import work.

[[Claude Desktop]] silently ignored both. Got `ModuleNotFoundError: No
module named 'memcon_mcp'`.

**Fix:** changed the config to pass an absolute *script path* instead:
```json
{
  "command": "/abs/.venv/bin/python3",
  "args": ["/abs/memcon_mcp/server.py"]
}
```
Python auto-adds the script's directory to `sys.path`, so relative
imports in `server.py` work without `cwd` or `PYTHONPATH`.

The script itself has `sys.path.insert(0, '..')` at the top to find
the project root.

**Lesson:** when an MCP client misbehaves, ditch `cwd` and `env` —
absolute paths are the only thing you can trust.""",
     ["Claude Desktop", "scripts.register_mcp", "MCP Server"]),
    ("HTTP download lost +x bit",
     "Downloading `memcon-install.command` over HTTP stripped the executable bit. Double-click did nothing.",
     """The macOS installer was a single `.command` file (which is just a
shell script with an extension Finder treats as runnable). Worked great
when copied locally with `cp`. Distributed via the landing page download
button: the browser saved it without the `+x` bit. Double-click silently
no-op'd.

**Fix:** ship a `.zip` instead. `cp -p` (or `zip -9` and `unzip`)
preserves the executable bit. Users now download `memcon-install-mac.zip`,
unzip it, then right-click → Open the `.command` file.

The actual canonical install path is the `curl | bash` one-liner; the
zip is the fallback for users who refuse to pipe-into-shell (fair).

**Lesson:** HTTP transit doesn't preserve POSIX permissions. Use a
container format that does, or do the chmod client-side as part of an
installer.""",
     ["bootstrap.sh", "install.sh"]),
    ("Anchor link blue color leak",
     "`.logo` was an `<a>` tag inheriting the browser default blue. Style cascade missed it.",
     """The brand logo at the top-left of the landing page is an `<a>` tag
(it links to `#`). Original CSS only set `color: var(--text)` on `.logo`
without specifying the `:link / :visited / :hover / :active` pseudo-
classes.

Browsers apply default `<a>` colors (blue, then purple after visit)
*via these pseudo-classes*, which beat the bare element selector.
Result: the logo turned blue after the user clicked it once. Looked
broken.

**Fix:** explicit cover of all states:
```css
.logo:link, .logo:visited, .logo:hover, .logo:active {
  color: var(--text);
  text-decoration: none;
}
```

**Lesson:** if you're styling `<a>` and color matters, set every
pseudo-class explicitly.""",
     ["UI v3 — Sirnik editorial final"]),
]

for name, summary, prose, related_list in BUGS:
    rel_links = "\n".join(f"- [[{r}]]" for r in related_list)
    N(f"bugs-and-fixes/{name}.md", ["bug-fix"], f"""
# {name}

**{summary}**

{prose}

## Related
{rel_links}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# MILESTONES (~8)
# ═══════════════════════════════════════════════════════════════════════════════

N("milestones/MCP server stood up.md", ["milestone", "v1.0"], """
# MCP server stood up

The moment [[MCP Server]] first answered a tool-call from [[Claude Desktop]].

## What it took

- Implementing 9 tools via [[FastMCP]]'s `@mcp.tool()` decorator
- Solving [[stdout pollution corrupts JSONRPC]]
- Solving [[Claude Desktop ignores cwd]]
- Solving [[cwd is slash on macOS sandbox]]
- Writing [[scripts.register_mcp]] to patch the Claude Desktop config idempotently

## Why it mattered

The MCP server is the *whole product*. Before this, memcon was just a
local memory tool you'd open separately. After this, memcon was Claude's
backend brain. The narrative changed from "another notes app" to
"memory for Claude."

## Related
- [[v1.0 — Plug into Claude]]
- [[MCP Server]] · [[Model Context Protocol (MCP)]]
- [[stdout pollution corrupts JSONRPC]] · [[Claude Desktop ignores cwd]]
""")

N("milestones/Engram renamed to Memcon.md", ["milestone", "v1.0"], """
# Engram renamed to Memcon

The project was originally called **Engram** (a neuroscience term for a
memory trace). The user renamed it to **Memcon** (short for "Memory
Context") mid-v1 development.

## Why the rename

> "rename the whole of project to Memcon as in Memory Context"
> — [[Aryaman (aryasgit)]]

Engram was poetic but unsearchable (lots of unrelated neuroscience
literature). Memcon was distinctive, said what it does, and tied
naturally to [[Model Context Protocol (MCP)]] — memory + context.

## What it touched

Everything. The project name. The Python package (`memcon_mcp/`). The
Qdrant collection (`memcon_memory`). All env vars (`MEMCON_VAULT`,
`MEMCON_COLLECTION`, `MEMCON_MODEL`). The CLI (`bin/memcon`). The MCP
tool prefix (every tool went from `engram_*` → `memcon_*`).

The git remote also moved: `aryasgit/engram` → `aryasgit/memcon`.
GitHub still serves a redirect.

## Related
- [[v1.0 — Plug into Claude]]
- [[MCP Server]]
- [[Model Context Protocol (MCP)]]
""")

N("milestones/v1.0 tagged.md", ["milestone", "v1.0"], """
# v1.0 tagged

[`v1.0.0`](https://github.com/aryasgit/memcon/releases/tag/v1.0.0)
landed once these were all true:

- [[MCP Server]] worked end-to-end with [[Claude Desktop]]
- [[bootstrap.sh]] / [[bootstrap.ps1]] installed cleanly on a fresh machine
- [[scripts.register_mcp]] patched the Claude Desktop config idempotently
- All known [[MOC — Bugs and Fixes|bugs]] fixed
- Landing page live with install instructions

## Why now

> "let's mark the current version as a V1"
> — [[Aryaman (aryasgit)]]

The first version had a real, complete story: install, register, ask,
save. Tagging it was about committing to that surface as the baseline —
v2 could build on it, but anyone who came in on v1.0 would get a
working system from the install one-liner.

## Related
- [[v1.0 — Plug into Claude]]
- [[v2.0 tagged]]
- [[bootstrap.sh]]
""")

N("milestones/v2.0 tagged.md", ["milestone", "v2.0"], """
# v2.0 tagged

[`v2.0.0`](https://github.com/aryasgit/memcon/releases/tag/v2.0.0)
shipped once memcon stopped being "a notes tool with MCP" and became a
project-memory backend that swallowed everything pointed at it.

## What was new

- [[Code ingestion]] — any project tree
- [[PDF ingestion]] — drop and forget
- [[Git auto-ingest]] — post-commit hook
- [[memcon_capture]] — the natural-language write
- [[memcon_timeline]] · [[memcon_digest]] — temporal slicing
- [[bin-memcon CLI]] — usable from any directory
- [[Multi-project switching]] — three env vars

## Why this version is the foundation

Without [[Code ingestion]], memcon couldn't answer "where do we handle X"
about the user's actual codebase. Once code was in, [[Claude (Anthropic)|Claude]]
had enough context to reason about *real* problems, not just notes.

Everything since v2 has built on this: [[v3.0 — Lives in your editor|v3.0]]
puts memcon in the editor where the code lives; [[v3.1 — Rich notes, hybrid recall|v3.1]]
makes the recall over that code dramatically sharper.

## Related
- [[v2.0 — Memory absorbs everything]]
- [[v3.0 — Lives in your editor]]
""")

N("milestones/VS Code extension shipped.md", ["milestone", "v3.0"], """
# VS Code extension shipped

`memcon-vscode-0.1.0.vsix` — the first VSIX. ~9 KB compiled. Works in
both [[VS Code]] and [[Cursor]] from the same file.

## What it took

- [[vscode extension source]] in TypeScript
- Three commands (`Memcon: Ask`, `Memcon: Save selection`, `Memcon: Search`)
- One sidebar tree view ("Recent")
- HTTP client to talk to [[api.main]] on localhost
- `vsce package --no-dependencies` to build the VSIX

## Distribution

Currently a download from `docs/install/memcon-vscode-0.1.0.vsix`. The
v3.0 roadmap has Marketplace + Open VSX publishing as the next step.

## Why this changes the product

Pre-extension: the reflex was "open browser → memcon UI → query → copy
result back to my code." Three context switches.

Post-extension: `Cmd+Shift+M`, type, answer appears in a markdown tab
in the same window. The friction collapsed to a keystroke.

## Related
- [[v3.0 — Lives in your editor]]
- [[VS Code extension]] · [[vscode extension source]]
- [[VS Code]] · [[Cursor]]
""")

N("milestones/Sirnik landing redesign shipped.md", ["milestone", "v3.0"], """
# Sirnik landing redesign shipped

The landing page at `docs/index.html` went through three full redesigns
in two days, landing on [[UI v3 — Sirnik editorial final]].

## The arc

1. Original: cards, corners, a generic SaaS feel
2. [[UI v2 — Audi-Sirnik red]]: tried hot red accent, looked striking
   but the red fought the type
3. Reverted with `git reset --hard e1c46e8`
4. [[UI v3 — Sirnik editorial final]]: pure monochrome, [[Sirnik (design reference)|Sirnik]]-inspired
   editorial, different micro-interaction per section

## What it codified

[[DESIGN.md — the design system]] — a 723-line portable reference that
captures the language so the next project can pick it up cold.

## Related
- [[UI v3 — Sirnik editorial final]]
- [[Design system extracted]]
- [[Sirnik (design reference)]]
""")

N("milestones/Design system extracted.md", ["milestone", "ui"], """
# Design system extracted

After [[Sirnik landing redesign shipped]] (and the parallel work on the
chat UI), the user asked:

> "create a holistic MD file that stores the design philosophy, font color
> palette of the above two redesigns, so in case I want to make another
> app, this becomes my base design principle and I can use the MD as a
> reference to recreate it for a different purpose"
> — [[Aryaman (aryasgit)]]

The result: [[DESIGN.md — the design system]]. 723 lines. 10 sections.
Includes the [[Five rules of the editorial system|five rules]], the
type scale, the color palette, the component library, the interaction
menu, the anti-patterns, and a quick-start CSS paste block.

## Why this matters

After two redesigns the project deserved a codified language. Without
it, a third application of the system would have to reverse-engineer
the first two. With it, anyone (the user, a future collaborator, even
Claude) can apply the system to a new app from cold.

## Related
- [[DESIGN.md — the design system]]
- [[Five rules of the editorial system]]
- [[UI v3 — Sirnik editorial final]]
""")

N("milestones/v3.1 layers landed.md", ["milestone", "v3.1"], """
# v3.1 layers landed

All five layers of v3.1 landed in two commits:

- `f5dd14f` — Layers 1–4 (templates / extractor / entity_index /
  enricher) + the writer refactor + retrieve rewrite + 4 new MCP tools
- `329d572` — Layer 5 ([[scripts.migrate_to_v3_1|the migration script]])

## What changed

- New modules: [[memory.templates]], [[memory.extractor]],
  [[memory.entity_index]], [[memory.enricher]]
- Rewritten: [[memory.writer]], [[memory.retrieve]]
- Updated: [[memcon_mcp.server]] (now 16 tools), [[memcon.config.yaml]],
  ROADMAP.md
- New script: [[scripts.migrate_to_v3_1]]

## What it took

The full vision was 4 layers + a migration script. Each layer touched
the next: the schema is what extraction fills, extraction populates
the entity index, the entity index feeds hybrid retrieval, retrieval
+ writes feed enrichment.

Total: ~2800 lines of Python net new, 257 lines of pre-existing code
refactored. Smoke-tested end-to-end with a synthetic vault.

## Related
- [[v3.1 — Rich notes, hybrid recall]]
- [[Universal note schema]] · [[Multi-pass extraction]] · [[Entity index]] · [[Hybrid retrieval]] · [[Auto-enrichment]]
- [[scripts.migrate_to_v3_1]]
""")


# ═══════════════════════════════════════════════════════════════════════════════
# PEOPLE AND PLACES (~7)
# ═══════════════════════════════════════════════════════════════════════════════

N("people-and-places/Aryaman (aryasgit).md", ["person"], """
# Aryaman (aryasgit)

The builder. Solo maintainer of memcon. GitHub handle `aryasgit`.

## Context

Engineering [[BARQ (the robot)|BARQ]] — an autonomous quadruped robot —
generated more debugging context per session than any single engineer
could hold. Memcon started as the project-memory backend for BARQ,
then generalized.

## Voice in this vault

Multiple direct quotes appear in the [[MOC — UI|UI iteration notes]] and
[[MOC — Milestones|milestone notes]] — these are real instructions/
reactions from the build sessions. They capture the texture of how the
project actually evolved (terse, opinionated, fast).

## Sponsorship

GitHub Sponsors button live since [[v2.0 — Memory absorbs everything|v2.0]].
"Sponsorship is a tipjar, not a paywall" — see [[Why MIT licensed]].

## Related
- [[BARQ (the robot)]]
- [[The story]]
""")

N("people-and-places/BARQ (the robot).md", ["place", "project"], """
# BARQ (the robot)

Autonomous quadruped robot project. The reason memcon exists.

## Why memcon was built for BARQ

A quadruped is a debugging machine. Every gait test surfaces something
weird: a servo overheating, an IMU drift, a power brownout, a planner
edge case. Each finding is small, but they accumulate. The pre-memcon
flow was: figure it out, file it in your head, forget it three weeks
later, re-debug from scratch.

Memcon's job is to make those findings *survive* into future sessions —
specifically into [[Claude (Anthropic)|Claude]] sessions, which is
where most of the debugging actually happens.

## How BARQ shaped memcon

- The original [[Subsystems]] list was BARQ-shaped (servo, imu, gait,
  power, vision, voice, slam, ik). [[v3.1 — Rich notes, hybrid recall|v3.1]]
  made the list optional.
- The 4-field schema (symptom / cause / fix) was perfect for BARQ debugs.
  But terrible for everything else — see [[Why universal schema]].
- The [[Note kinds|new note kinds]] (concept, reference, meeting,
  breakthrough) generalize beyond the debug-session shape.

## Related
- [[Subsystems]]
- [[Aryaman (aryasgit)]]
- [[The story]]
""")

N("people-and-places/Claude (Anthropic).md", ["person", "tool"], """
# Claude (Anthropic)

The LLM memcon is built to augment. Specifically the Claude models
running inside [[Claude Desktop]], [[Cursor]], Claude Code, and the
Claude API.

## Why Claude specifically

Two reasons:
1. [[Model Context Protocol (MCP)]] is Anthropic's protocol. The most
   mature MCP support is in Claude's clients.
2. Claude's instruction-following on tool-call docstrings is good
   enough that memcon's heavily-tuned tool descriptions ([[MCP Server]])
   reliably steer it toward the right tool at the right time.

## Memcon as a Claude extension

The product framing is "Memory for Claude." Could it work with other
LLMs? Yes — the [[Ollama|local LLM]] used internally for extraction is
already model-agnostic. Adding REST/HTTP transports alongside the MCP
stdio one would let other clients in. That's [[v6.0+ — Managed option, niche depth (planned)|v6+]] territory.

## Related
- [[MCP Server]]
- [[Model Context Protocol (MCP)]]
- [[Claude Desktop]] · [[Cursor]]
""")

N("people-and-places/Claude Desktop.md", ["tool"], """
# Claude Desktop

Anthropic's desktop app for [[Claude (Anthropic)|Claude]]. macOS, Windows,
Linux. The first and primary client memcon targets via [[MCP Server]].

## Quirks that shaped memcon

- [[cwd is slash on macOS sandbox]] — CWD is `/` because of the app sandbox
- [[Claude Desktop ignores cwd]] — even with `cwd` set in config, it
  ignores it, breaking `python3 -m module` imports
- [[stdout pollution corrupts JSONRPC]] — any `print()` in a tool function
  shows up as "Server disconnected" in the UI

[[scripts.register_mcp]] handles the config patching idempotently.

## Where its config lives

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\\Claude\\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Related
- [[MCP Server]] · [[scripts.register_mcp]]
- [[Claude (Anthropic)]]
- [[cwd is slash on macOS sandbox]] · [[Claude Desktop ignores cwd]]
""")

N("people-and-places/Cursor.md", ["tool"], """
# Cursor

VS Code fork with first-class LLM integration. Memcon targets it via
two paths:

1. **MCP** — Cursor supports MCP servers natively. The [[MCP Server]]
   config that works for [[Claude Desktop]] works for Cursor too (with
   path adjustments).
2. **VS Code extension** — Cursor reads VS Code extensions natively, so
   the same `.vsix` from [[VS Code extension]] works without changes.

## Why both paths

MCP gives [[Claude (Anthropic)|Claude]] (running inside Cursor's chat)
access to memcon as tools. The VS Code extension gives the *user* direct
access via Cmd+Shift+M / Cmd+Shift+S without going through chat.

Different ergonomics for different moments.

## Related
- [[VS Code extension]] · [[VS Code]]
- [[MCP Server]] · [[Claude Desktop]]
""")

N("people-and-places/VS Code.md", ["tool"], """
# VS Code

Microsoft's editor. The primary surface for the [[VS Code extension]]
shipped in [[v3.0 — Lives in your editor]].

## What memcon adds to it

Three commands + a sidebar tree:
- `Cmd+Shift+M` — Ask memcon, grounded answer in a markdown tab
- `Cmd+Shift+S` — Save selection to memory
- `Memcon: Search` — raw chunks
- Activity-bar "Recent" tree

## Why VS Code first

It's the most-used editor on the planet. The extension ecosystem (and
the VSIX format) is well-documented. The same VSIX works in [[Cursor]]
without modification, doubling the reach for one build.

## Related
- [[VS Code extension]] · [[vscode extension source]]
- [[Cursor]]
""")

N("people-and-places/Sirnik (design reference).md", ["design"], """
# Sirnik (design reference)

A design studio at [sirnik.co](https://sirnik.co). Their landing page
was the visual anchor for [[UI v3 — Sirnik editorial final]].

## What was borrowed

- **Pure monochrome** — black background, white text, no accent color
- **Editorial multi-column grid** — 3-col asymmetric splits at the top
- **Massive display typography** — Sirnik uses what looks like a tight
  custom sans for their headline; memcon approximated with Inter Tight
- **Tiny micro-labels** — uppercase, wide tracking, used as section
  markers
- **Giant footer wordmark** with an image card cutting into it — the
  single biggest visual move on the page
- **Live time + location** in the philosophy row

## What wasn't borrowed

- Sirnik's custom typeface (we used [[Sentence Transformers|free Google Fonts]])
- Their specific hero composition (memcon's hero serves different content)
- Their photography aesthetic (memcon shows code, not portraits)

## Why it worked as a reference

Sirnik's design embodies the [[Five rules of the editorial system|five rules]]
we ended up codifying. Studying it gave us a working example to point
at when the previous attempts ([[UI v0 — Monochrome serif]],
[[UI v1 — Claude chat style]], [[UI v2 — Audi-Sirnik red]]) were
drifting.

## Related
- [[UI v3 — Sirnik editorial final]]
- [[DESIGN.md — the design system]]
- [[Five rules of the editorial system]]
""")


# ═══════════════════════════════════════════════════════════════════════════════
# REJECTED IDEAS (~5)
# ═══════════════════════════════════════════════════════════════════════════════

N("rejected/SaaS-first version.md", ["rejected"], """
# SaaS-first version *(rejected)*

> A hosted memcon. Sign up at memcon.io, get a vault in the cloud, no
> install needed.

## Why no

It would invert the entire value prop. Memcon's promise is "your
engineering history never leaves your machine." A hosted version means
the user's code, debug sessions, decisions, all sit on someone else's
server.

Even with end-to-end encryption, the user would have to trust the
operator (us) not to peek, get hacked, or pivot.

## The honest version

A managed hosted version *is* on the [[v6.0+ — Managed option, niche depth (planned)|v6+]]
roadmap — but only "if open-source traction makes this an obvious pull,"
and explicitly as an *option* alongside the local-first default. Never
the default. Never the only path.

## Related
- [[Local-first]]
- [[Why local LLM not cloud]]
- [[Why MIT licensed]]
- [[Telemetry phone-home]]
""")

N("rejected/Telemetry phone-home.md", ["rejected"], """
# Telemetry phone-home *(rejected)*

> Memcon could report anonymized usage stats. How many writes per
> session, which tool is most popular, install successes vs failures.
> Useful for prioritizing what to build.

## Why no

It would break the "nothing leaves your machine" guarantee. Even with
opt-in consent, even with anonymous data, the moment the binary is
*capable* of phoning home, the trust is gone — savvy users will run
network monitors to verify, and the promise becomes "trust us about
the toggle."

Useful product analytics without phone-home: log to a local file the
user can inspect. Show it themselves if they want to share. Never
emit network traffic the user didn't initiate.

## Related
- [[Local-first]]
- [[SaaS-first version]]
- [[Why local LLM not cloud]]
""")

N("rejected/Ads in dashboard.md", ["rejected"], """
# Ads in dashboard *(rejected)*

> The [[api.ui.html|dashboard]] gets eyeballs from engineers. Could be
> a monetizable surface.

## Why no

Hard no. The dashboard is a *tool*. The moment it has ads it stops
being a tool and starts being a media product, and the incentives
diverge. Memcon's incentive should always be "make the user's project
memory better" — not "increase engagement to sell impressions."

Same logic as the rejection of the [[Paid pro tier]]. Memcon should
make money via sponsorship + (optionally) a [[v6.0+ — Managed option, niche depth (planned)|hosted
tier for those who want it]], not via the open-source product's UI.

## Related
- [[Paid pro tier]]
- [[Why MIT licensed]]
""")

N("rejected/Paid pro tier.md", ["rejected"], """
# Paid pro tier *(rejected)*

> Some features could be gated behind a paid plan — say, the
> [[VS Code extension]], or [[memcon_digest]], or future
> [[v4.0 — Knows what it knows (planned)|contradiction detection]].

## Why no

Memcon's stance: the whole product is MIT, and stays that way.
Sponsorship is a tipjar, not a paywall.

The moment a feature is "free if you have ≤10 notes, paid otherwise,"
you've fragmented your users into two classes and given the paid ones
leverage you have to maintain. Worse: the value of the open-source
project drops, because new users default-perceive it as "missing the
good parts."

A paid hosted tier ([[v6.0+ — Managed option, niche depth (planned)|v6+]])
is different — that's selling *infrastructure*, not gating features.
Anyone who runs memcon locally gets the full product.

## Related
- [[Why MIT licensed]]
- [[SaaS-first version]]
- [[Ads in dashboard]]
""")

N("rejected/Bespoke embedding model.md", ["rejected"], """
# Bespoke embedding model *(rejected)*

> Could train a custom embedder fine-tuned for debugging conversations.
> Or use a much bigger model (BGE-large, e5-large) for better recall.

## Why no

Two reasons:
1. **`all-MiniLM-L6-v2` is excellent for the cost.** 384-dim, ~25MB,
   CPU-fast, well-understood. The retrieval quality bottleneck in
   memcon is *not* the embedder — it's note quality (which v3.1 fixed
   with [[Why preserve raw context|raw context preservation]]).
2. **Custom embedders are a research project disguised as a feature.**
   Fine-tuning needs labeled data, eval pipelines, drift detection.
   That's months of work to maybe get 5% better recall. Meanwhile the
   feature backlog has [[v4.0 — Knows what it knows (planned)|contradiction detection]],
   the [[VS Code extension|VS Code marketplace publish]], etc. —
   higher-leverage uses of the same time.

If someone wants to swap the embedder, the architecture allows it
([[ingestion.embedder]] is one file). But it's not on memcon's
critical path.

## Related
- [[Sentence Transformers]]
- [[Embeddings]]
- [[Why preserve raw context]]
""")


# ═══════════════════════════════════════════════════════════════════════════════
# Main — write everything
# ═══════════════════════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Memcon meta-vault for Obsidian.")
    ap.add_argument("--dest", default="meta-vault",
                    help="Destination folder (default: meta-vault/)")
    ap.add_argument("--clean", action="store_true",
                    help="Delete the destination before writing (default: preserve unrelated files)")
    args = ap.parse_args(argv)

    dest = Path(args.dest).resolve()
    if args.clean and dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    written = 0
    for path, tags, body in NOTES:
        out = dest / path
        out.parent.mkdir(parents=True, exist_ok=True)
        # H1 inferred from filename stem (already in body usually; we use body verbatim)
        content = fm(tags) + "\n\n" + body
        out.write_text(content)
        written += 1

    # Print a tiny manifest for clarity
    print(f"✓ Wrote {written} notes to {dest}")
    print()
    print("Open in Obsidian:")
    print(f"   1. Obsidian → Open vault → pick: {dest}")
    print(f"   2. Cmd+G to toggle Graph View")
    print(f"   3. Click any node to navigate; backlinks panel is at the side")
    return 0


if __name__ == "__main__":
    sys.exit(main())
