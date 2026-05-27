# Memcon Roadmap

A feature-keyed view of where Memcon is going. **No dates.** Versions ship when
the theme is real, not when a calendar says so.

---

## v1.0 — *Plug into Claude* ✅ shipped

The "MCP server you can ask Claude to use" version. Everything below is in
`main` and tagged at [`v1.0.0`](https://github.com/aryasgit/memcon/releases/tag/v1.0.0).

- [x] MCP server over stdio with **9 tools** (`memcon_query`, `memcon_ask`,
      `memcon_write_debug` / `_decision` / `_experiment`, `memcon_session_summary`,
      `memcon_update_note`, `memcon_stats`, `memcon_subsystems`)
- [x] One-liner installer for macOS / Linux / WSL (`bootstrap.sh`) and
      Windows (`bootstrap.ps1`)
- [x] RAM-tier model auto-pick from `llama3.2:1b` → `qwen2.5-coder:32b`
- [x] Auto-register Memcon in Claude Desktop config (`scripts/register_mcp.py`)
- [x] FastAPI dashboard at `localhost:8000/ui` with chat-style UI
- [x] Auto Obsidian `[[wikilinks]]` to top-3 semantic neighbours on every new note
- [x] Public landing page at `docs/` with `.zip` and curl install paths
- [x] Robust against macOS sandboxing (absolute paths, `vault.path` absolutised
      at config-load, stderr-only logging)

---

## v2.0 — *Memory absorbs everything* ✅ shipped

Memcon stops being a notes tool and becomes a project-memory backend. Tagged
at [`v2.0.0`](https://github.com/aryasgit/memcon/releases/tag/v2.0.0).

- [x] **Code ingestion** — `scripts/ingest_code.py` walks any project, respects
      `.gitignore`-style exclusions, chunks source by 80-line windows
- [x] **PDF ingestion** — drop `.pdf` files in `vault/`, indexed page-by-page
      via `pypdf`
- [x] **Git auto-ingest** — `scripts/install_git_hook.sh` installs a
      post-commit hook so every commit becomes searchable memory
- [x] **`memcon_capture`** — single natural-language MCP tool that uses the
      local LLM to extract title/symptom/cause/fix from a freeform paragraph
- [x] **`memcon_timeline`** — time-bounded slice of recent notes
- [x] **`memcon_digest`** — LLM-generated digest of the last N days
      (Themes / Wins / Open items / Worth revisiting)
- [x] **`bin/memcon` CLI** — `memcon ask / query / stats / recent / digest /
      save / serve / ui` from any directory
- [x] **Multi-project switching** via `MEMCON_VAULT`, `MEMCON_COLLECTION`,
      `MEMCON_MODEL` env vars
- [x] GitHub Sponsors button via `.github/FUNDING.yml`

---

## v3.1 — *Rich notes, hybrid recall* 🚧 **in progress**

The schema generalises. The local LLM now extracts in **four passes** instead
of one — what gets stored is richer, what gets retrieved is more accurate.
All still local.

**Layer 1 — Universal note schema** *(✅ shipped)*
- [x] `memory/templates.py` — 8 note kinds (debug / decision / experiment /
      concept / reference / meeting / breakthrough / session) with per-kind
      sections, shared outer shape (TL;DR + Context + Related + See also)
- [x] Rich frontmatter: `id`, `type`, `created`, `updated`, `subsystem` (now
      a list), `tags`, `status`, `confidence`, `entities` (six categories),
      `git` ({commit, branch, changed_files}), `linked` (Obsidian wikilinks)
- [x] `memory/writer.py` refactor: `log_universal(kind, title, fields, …)` as
      the canonical entry; back-compat wrappers `log_debug/_decision/…`
      preserved; new `log_concept / log_reference / log_meeting / log_breakthrough`
- [x] Verbatim `## Context` preserved on every note — the embedder finally has
      real prose to grip onto, not a 4-line skeleton

**Layer 2 — Multi-pass extraction** *(✅ shipped)*
- [x] `memory/extractor.py`: `classify_type` → `extract_structure` →
      `extract_entities` → optional `self_critique`, all in Ollama JSON mode
- [x] `memcon_capture` rewired through the pipeline; returns the kind picked,
      confidence, and the entity dict so Claude can quote it
- [x] Four new MCP tools: `memcon_write_concept / _reference / _meeting /
      _breakthrough`. Total MCP surface now **16 tools**.

**Layer 3 — Entity-indexed hybrid retrieval** *(✅ shipped)*
- [x] `memory/entity_index.py` — SQLite inverted index at
      `{vault}/.memcon/entities.db` keyed by (entity_lc, kind, doc_name);
      `index_note()` / `clear_doc()` / `lookup()` / `stats()`
- [x] `memory/retrieve.query()` is now **hybrid**: semantic Qdrant hits +
      entity-index hits merged and reranked. Output adds `via` (semantic /
      entity / both) and `entity_hits` fields. `memcon_query` benefits
      automatically — every read tool picks up keyword-exact recall for free.

**Layer 4 — Auto-enrichment** *(✅ shipped)*
- [x] `memory/enricher.py` — background thread spawned after every write:
      detects git context (`commit`, `branch`, `changed_files`) from the
      project root, generates a `## See also` block with one-line summaries
      pulled from each related note's TL;DR. Non-blocking — write returns
      instantly.

**Layer 5 — Backfill migration** *(✅ shipped)*
- [x] `scripts/migrate_to_v3_1.py` — walks the vault, parses legacy
      frontmatter + body, infers the kind from folder + memory_type, lifts
      `## Symptom` / `## Cause` / `## Fix Applied` / etc. into the v3.1 field
      names, runs entity extraction (LLM if Ollama is up, regex fallback
      otherwise), preserves verbatim original under `## Context`, and
      re-ingests into Qdrant
- [x] Idempotent — second run detects `type:` in frontmatter and skips
- [x] Safe — backs originals up to `{vault}/_backup_v3.1_<timestamp>/`
      unless `--no-backup` is passed
- [x] CLI: `python3 -m scripts.migrate_to_v3_1 [--dry-run] [--no-llm]
      [--limit N] [--no-backup] [--reingest] [--verbose]`

**Still to land before tagging v3.1.0:**
- [ ] `memcon_pattern(topic)` — first crack at v4 contradiction/pattern
      detection, built on the entity index + semantic graph
- [ ] End-to-end test with Ollama running: classify → structure → entities
      → write → query (verify hybrid recall on real notes)

---

## v3.0 — *Lives in your editor* 🚧 **in progress**

The moat feature. Once Memcon is inline in VS Code / Cursor, engineers don't
context-switch to a browser to consult memory — they hover and it's there.

**MVP (`vscode/` folder, `memcon-vscode-0.1.0.vsix`) — ✅ shipped:**
- [x] `Memcon: Ask` command (`Cmd+Shift+M`) — grounded answer in a markdown tab
- [x] `Memcon: Save selection to memory` (`Cmd+Shift+S`) — captures selection
      + file path + optional note
- [x] `Memcon: Search` — raw chunks for inspection
- [x] Sidebar "Recent" tree in the activity bar, with refresh + click-to-peek
- [x] First-launch welcome + dashboard shortcut
- [x] Same VSIX works in both VS Code and Cursor
- [x] Distributed as a download from the landing page (`docs/install/`)

**Still to land (`vscode/` 0.2.x):**
- [ ] Code lens on functions/classes: "3 related debug sessions, 2 decisions"
- [ ] Hover provider: shows top-1 related note when you hover a symbol
- [ ] Status bar widget: "last memcon write: 12 min ago"
- [ ] Direct `memcon_capture` integration (local-LLM extraction, not just session)
- [ ] Published to VS Code Marketplace + Open VSX
- [ ] **CLI in your `PATH`** — install.sh symlinks `bin/memcon` into
      `/usr/local/bin` (opt-in via `MEMCON_LINK_CLI=1`)
- [ ] **Demo video** (30-second screencast of the inline editor loop) embedded
      at the top of the README and landing-page hero

---

## v4.0 — *Knows what it knows*

Memory that's self-aware. Stops being a passive store and starts surfacing
patterns + flagging contradictions.

- [ ] **Contradiction detection** — when a new note contradicts an existing one
      (same subsystem, opposite outcome), flag the old one as `stale=true` and
      surface a "resolved by [[new_note]]" link
- [ ] **Confidence / freshness scoring** — old notes get downweighted in
      retrieval unless explicitly re-verified via `memcon_verify(note)`
- [ ] **Auto-link by tags** — notes sharing tags get cross-linked in their
      `## Related` sections in addition to semantic neighbours
- [ ] **Knowledge-graph viewer** in the dashboard — interactive D3-style graph
      of notes + edges (semantic + tag + wikilink), filterable by subsystem
- [ ] **`memcon_pattern(topic)`** MCP tool — find recurring symptoms /
      decisions / failures across the vault. "What keeps breaking?"
- [ ] **`memcon_what_changed(since)`** — semantic diff: what concepts have
      appeared or shifted in the last N days

---

## v5.0 — *Multimodal & shared*

Beyond text. Multiple humans + multiple senses.

- [ ] **Image ingestion** via CLIP embeddings — circuit photos, sketches,
      whiteboard screenshots, scope traces become semantically queryable
- [ ] **Voice memos** — `vault/voice/*.m4a` transcribed via Whisper, indexed
- [ ] **Web clipper browser extension** — save Stack Overflow answers, docs
      pages, blog posts to memcon with one click
- [ ] **Team vaults** — shared memory across an engineering team with
      privacy boundaries (some notes personal, some shared)
- [ ] **Mentions in notes** — `@servo` to tag a subsystem, `@aryaman` to
      tag a person; mentions index for cross-references
- [ ] **Vault sync** — laptop ↔ robot ↔ workstation share the same vault
      via a chosen transport (Syncthing / iCloud / Dropbox / custom)
- [ ] **Mobile read-only app** — query memory from your phone (mostly for
      "wait, what did we decide about X?" moments away from the desk)

---

## v6.0+ — *Managed option, niche depth*

The moonshots. Only land if v1–v5 are deep, not just because they sound cool.

- [ ] **Memcon Cloud** — managed hosted version for non-technical users or
      teams who don't want to run Docker locally. Real monetisation tier. Only
      if open-source traction makes this an obvious pull.
- [ ] **ROS bag / telemetry ingestion** — robot runtime data becomes
      queryable memory. Niche but deep — the BARQ origin keeps calling.
- [ ] **Hardware change-log tracking** — wiring diagrams, BOMs, calibration
      params version-tracked + auto-linked to debug sessions that reference
      them. Industrial / robotics audience.
- [ ] **Reproducibility queries** — `memcon_what_led_to(commit_sha)` returns
      the full memory chain that produced a specific code state.
- [ ] **LLM-agnostic backend** — swap Ollama for any OpenAI-compatible
      endpoint. Already mostly true via `llm.base_url`; needs UX polish and
      docs.
- [ ] **Plugin SDK** — `memcon-plugin` interface so the community can ship
      domain-specific ingestion / MCP tools without forking core.

---

## What's *not* on the roadmap (deliberately)

These have been considered and rejected — they'd change what Memcon is:

- ❌ **A SaaS-first version**. The local-first promise is the value prop.
- ❌ **Telemetry / phone-home**. Anything reporting back to a server breaks
      the "nothing leaves your machine" guarantee.
- ❌ **Ads or sponsored content** in the dashboard. Hard no.
- ❌ **A paid "pro" tier gating existing features**. Memcon's MIT and stays
      that way. Sponsorship is a tipjar, not a paywall.
- ❌ **A bespoke embedding model**. Sentence-transformers' `all-MiniLM-L6-v2`
      is excellent for the cost. Swapping in a custom model would be a
      research project disguised as a feature.

---

## Contributing to the roadmap

If you've built on Memcon and there's a feature that would make it
genuinely indispensable for you, open an issue with `roadmap:` in the title.
Concrete user stories beat vague wishes.

If you want to help ship one of the items above, pick something marked
`[ ]`, comment on the relevant issue (or open one), and let's coordinate.
Memcon's small enough that a single thoughtful PR can change the trajectory.
