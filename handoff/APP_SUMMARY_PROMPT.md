# App Summary Prompt

> Copy everything below the `---` and paste it as a single message into
> each of the **Memshare**, **Thymeline**, and **Invpart** conversations
> (or any other Claude conversation where one of those apps was built).
>
> The Claude in each of those conversations will produce a structured
> handoff document. Paste each of those three documents (in full) into
> the unified Engram conversation.
>
> The prompt is identical for all three apps — works because each Claude
> already has the app's context loaded.

---

Hey — I need a structured handoff document about this project so I can
hand it off to another Claude conversation cold.

**The receiving conversation** is unifying four of my apps (this one
plus three others) under an umbrella brand called **Engram**. It needs
to understand this app without ever having seen our chat. The goal of
the unified conversation is to build a single bundle landing page that
tells a coherent story across all four apps — it's a marketing /
portfolio narrative effort, NOT a technical-integration effort.

Please produce a markdown document with the **exact sections** below,
in the **exact order** below. Keep the whole thing under ~2000 words.
Self-contained — no references to our prior conversation. Write as if
explaining the project to a senior engineer who's never heard of it.

Output ONLY the markdown document. No preamble, no commentary, no
"Here's the summary you asked for." Start with the H1.

---

# {App Name} — Project Handoff

## 1. One-line pitch

A single sentence elevator pitch. Should work as an H1 sub-headline on
a landing page. Examples of the right register:
- "Memory for Claude that lives on your laptop."
- "Encrypted peer-to-peer comms for engineering teams."
Aim for ≤ 12 words. Concrete. No marketing fluff.

## 2. What it does

Three short paragraphs:
- **The problem** — what gap in existing tools does this fill?
- **The solution** — what does the app actually do?
- **The killer feature** — the one thing that, if removed, kills the
  product. (Not a list of features — the single sharpest one.)

## 3. Tech stack

Markdown table:

| Layer | Tech |
|---|---|
| Language | (Python / Rust / Go / TypeScript / etc.) |
| Framework | (FastAPI / Tauri / Electron / Next.js / etc.) |
| Storage | (SQLite / Qdrant / file-system / IPFS / etc.) |
| Crypto (if any) | (libsodium / WebCrypto / age / etc.) |
| Networking (if any) | (libp2p / WebRTC / stdio / HTTP / etc.) |
| Distribution | (Docker / native binary / brew / vsix / etc.) |
| Deployment | (local-only / Docker-compose / static site / etc.) |

## 4. Architecture

An ASCII or mermaid diagram showing the major components and their
data flow. Keep it small — fits on one screen. Label every box and
every arrow.

If the architecture is genuinely simple (single binary, single
process), say so explicitly instead of forcing a diagram.

## 5. Backend logic

Three subsections:

**Main modules / packages** — bullet list, one line per module
explaining what it owns.

**Key flows** — 2–4 numbered sequences for the most important user
actions ("user sends a file", "user starts a session", etc.).

**Data model** — what gets persisted, in what shape, where. Schema
sketches welcome.

## 6. UI / UX surfaces

Bullet list of every place a user interacts with the app:
- Web dashboard? (URL, port)
- CLI? (binary name, key commands)
- MCP server? (tool list)
- Desktop app? (framework)
- Browser extension?
- Mobile?

For each: a one-line description.

## 7. Design language

- What font(s)?
- What color palette? (hex codes or named system)
- Does it use the shared **DESIGN.md** system from the Memcon repo
  (`/Users/barq/BARQ/engram/DESIGN.md`)? If not, why?
- One sentence on the visual aesthetic.

## 8. Current state

Markdown table:

| Aspect | State |
|---|---|
| Version | (vX.Y) |
| Tagged release | (yes/no + tag) |
| Landing page | (URL or "none") |
| Installer | (one-liner? Docker? `.vsix`?) |
| README | (complete / partial / minimal) |
| Test coverage | (high / medium / low / none) |
| Repo | (URL) |
| Known WIP | (1-2 lines) |
| Known issues | (1-2 lines) |

## 9. Key design decisions

3–6 non-obvious choices and *why* — the things a future Claude would
get wrong by default. Examples of the register:
- "Chose libp2p over WebRTC because direct-mode P2P matters for the
  air-gapped use case."
- "Single-process Tauri instead of Electron because the install
  footprint goal was <50MB."

Format: bold question, paragraph answer.

## 10. Repo structure

Tree showing the top 2 levels of folders + the key files:

```
project/
├── src/
│   ├── ...
│   └── ...
├── frontend/
├── docs/
├── scripts/
└── README.md
```

## 11. The four-word identity

Pick four words that capture the app's stance. Examples for Memcon:
*Local. MIT. Engineer-shaped. Persistent.*

These are going to anchor the bundle landing page — each app gets
four words. Make them count.

## 12. Three things a fresh Claude must know

The three most important pieces of context a new conversation needs
to be productive immediately. The "if I could only tell them three
things" version. Phrase each as a bullet, ≤ 30 words.

## 13. What's on the roadmap

A short bulleted list of what's planned next, in priority order.
3–6 items. Be honest about which are "shipped soon" vs "someday."

---

End of template. The output of this prompt becomes a paste-able block
that goes into the Engram unified conversation alongside the matching
summaries for the other apps. So the more structured + self-contained
your output is, the easier the unified conversation will be.

Thanks.
