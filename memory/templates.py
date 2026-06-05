"""
memory/templates.py
Universal note templates with per-type sections.

The schema philosophy (see DESIGN.md and ROADMAP v4 notes):
  - One outer shape, swappable middle.
  - Rich frontmatter: id, type, created, updated, subsystem, tags, status,
    confidence, entities (files/symbols/errors/packages/urls/concepts), git, linked.
  - "Investigation" / "Context" sections preserve the raw conversation so the
    embedder has real prose to work with, not a 4-line skeleton.

Public entry points
-------------------
    render(kind, fields)            → full markdown string (frontmatter + body)
    render_frontmatter(meta)        → just the --- block (used by enricher to update)
    SECTIONS_FOR[kind]              → ordered list of section names for that kind
    ALL_KINDS                       → tuple of valid kind strings
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Iterable

# ──────────────────────────────────────────────────────────────────────────────
# Kinds — every note belongs to one. The middle sections differ; the outer
# shape (TL;DR + Context + Related) is shared.
# ──────────────────────────────────────────────────────────────────────────────

ALL_KINDS: tuple[str, ...] = (
    "debug",          # something broke; investigation + fix
    "decision",       # we chose A over B; rationale survives
    "experiment",     # we tried X; here's what happened
    "concept",        # a definition / mental model
    "reference",      # an API / spec / external source captured locally
    "meeting",        # sync / discussion notes
    "breakthrough",   # the "aha" moment that unlocked something
    "session",        # end-of-session roll-up
)

# Folder names under vault/ for each kind. Old folders preserved (debugging,
# decisions, experiments) so legacy notes coexist.
FOLDER_FOR: dict[str, str] = {
    "debug":        "debugging",
    "decision":     "decisions",
    "experiment":   "experiments",
    "concept":      "concepts",
    "reference":    "references",
    "meeting":      "meetings",
    "breakthrough": "breakthroughs",
    "session":      "sessions",
}

# Mapping kind → ordered (section_title, field_name, fallback_text) tuples.
# `field_name` is the key inside the `fields` dict passed to render(); fallback
# is what gets emitted if that key is empty/missing.
SECTIONS_FOR: dict[str, list[tuple[str, str, str]]] = {
    "debug": [
        ("TL;DR",          "tldr",          ""),
        ("Symptom",        "symptom",       ""),
        ("Investigation",  "investigation", ""),  # the long-form raw context
        ("Cause",          "cause",         "Under investigation."),
        ("Fix",            "fix",           "None yet."),
        ("Verification",   "verification",  ""),
    ],
    "decision": [
        ("TL;DR",          "tldr",          ""),
        ("Context",        "context",       ""),
        ("Options considered", "options",   ""),
        ("Decision",       "decision",      ""),
        ("Reasoning",      "reasoning",     ""),
        ("Consequences",   "consequences",  ""),
    ],
    "experiment": [
        ("TL;DR",          "tldr",          ""),
        ("Hypothesis",     "hypothesis",    ""),
        ("Setup",          "setup",         ""),
        ("Result",         "result",        ""),
        ("Conclusion",     "conclusion",    ""),
    ],
    "concept": [
        ("TL;DR",          "tldr",          ""),
        ("Definition",     "definition",    ""),
        ("Why it matters", "why",           ""),
        ("Example",        "example",       ""),
        ("Pitfalls",       "pitfalls",      ""),
    ],
    "reference": [
        ("TL;DR",          "tldr",          ""),
        ("What this is",   "summary",       ""),
        ("Key points",     "key_points",    ""),
        ("Notes",          "notes",         ""),
        ("Source",         "source",        ""),
    ],
    "meeting": [
        ("TL;DR",          "tldr",          ""),
        ("Attendees",      "attendees",     ""),
        ("Notes",          "notes",         ""),
        ("Decisions",      "decisions",     ""),
        ("Action items",   "actions",       ""),
    ],
    "breakthrough": [
        ("TL;DR",          "tldr",          ""),
        ("Background",     "background",    ""),
        ("Insight",        "insight",       ""),
        ("Implication",    "implication",   ""),
        ("Next steps",     "next_steps",    ""),
    ],
    "session": [
        ("TL;DR",          "tldr",          ""),
        ("Worked on",      "worked_on",     ""),
        ("Solved",         "solved",        ""),
        ("Decided",        "decided",       ""),
        ("Open items",     "open_items",    ""),
    ],
}

# Sections that appear at the bottom of every kind, after the type-specific
# middle sections. Order matters: raw context first (so the embedder sees it),
# then auto-linked Related, then enrichment.
TAIL_SECTIONS: list[tuple[str, str]] = [
    # (title, field_name) — emitted only if field is non-empty
    ("Context",  "context_raw"),
    ("Related",  "related_md"),   # rendered by writer.py from wikilinks
    ("See also", "see_also"),     # filled in by enricher.py asynchronously
]


# ──────────────────────────────────────────────────────────────────────────────
# Frontmatter rendering
# ──────────────────────────────────────────────────────────────────────────────

def _yaml_value(v: Any) -> str:
    """Render a single value as YAML-safe text. Keeps the file human-editable."""
    if v is None:
        return '""'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        # Quote if it contains YAML-special chars or starts ambiguously
        if any(c in v for c in ":#[]{},&*!|>'\"%@`") or v.startswith(("- ", "? ")):
            return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return v if v else '""'
    if isinstance(v, list):
        if not v:
            return "[]"
        return "[" + ", ".join(_yaml_value(x) for x in v) + "]"
    if isinstance(v, dict):
        # Inline dict — only used for `git: {commit, branch}` style nesting
        return "{" + ", ".join(f"{k}: {_yaml_value(val)}" for k, val in v.items()) + "}"
    return _yaml_value(str(v))


def render_frontmatter(meta: dict) -> str:
    """Render a frontmatter dict to a YAML --- block.

    Keys preserved in insertion order. Nested dicts become inline {k: v} form
    so the result remains valid YAML and obsidian-readable.
    """
    lines = ["---"]
    for k, v in meta.items():
        if v is None or v == "" or v == [] or v == {}:
            continue
        if isinstance(v, dict):
            # Multi-line dict if any sub-value is itself a list (nicer to read)
            if any(isinstance(sv, list) for sv in v.values()):
                lines.append(f"{k}:")
                for sk, sv in v.items():
                    if sv is None or sv == "" or sv == []:
                        continue
                    lines.append(f"  {sk}: {_yaml_value(sv)}")
            else:
                lines.append(f"{k}: {_yaml_value(v)}")
        else:
            lines.append(f"{k}: {_yaml_value(v)}")
    lines.append("---")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Body rendering
# ──────────────────────────────────────────────────────────────────────────────

def _section(title: str, body: str) -> str:
    """Emit `## Title\n\nbody\n` — skipped entirely if body is empty."""
    body = (body or "").strip()
    if not body:
        return ""
    return f"## {title}\n\n{body}\n"


def render_body(kind: str, title: str, fields: dict, sections: list | None = None) -> str:
    """Render the H1 + middle sections + tail sections.

    `sections` overrides the frozen per-kind skeleton with an explicit list of
    (title, field_name, fallback) tuples — this is how adaptive templates inject
    problem-specific sections inherited from related notes. When None, falls back
    to the static SECTIONS_FOR[kind].
    """
    out: list[str] = [f"# {title}\n"]

    specs = sections if sections is not None else SECTIONS_FOR.get(kind, SECTIONS_FOR["debug"])
    for section_title, field_name, fallback in specs:
        value = fields.get(field_name) or fallback
        chunk = _section(section_title, value)
        if chunk:
            out.append(chunk)

    for section_title, field_name in TAIL_SECTIONS:
        chunk = _section(section_title, fields.get(field_name, ""))
        if chunk:
            out.append(chunk)

    return "\n".join(out).rstrip() + "\n"


# ──────────────────────────────────────────────────────────────────────────────
# Adaptive templates — sections that LEARN per problem-domain
#
# A new note starts from its kind's frozen skeleton, then INHERITS the
# problem-specific sections that recur across its most-related past notes. So the
# 3rd+ latency-incident note auto-adopts "## Latency timeline" once earlier ones
# share it — and similar problems end up structurally aligned, which is exactly
# what makes memcon_recall able to line them up apples-to-apples.
# ──────────────────────────────────────────────────────────────────────────────

import re as _re_mod

# How many related notes must share an extra section before it's inherited.
# 2 = genuine recurrence (kills one-off noise from a single related note).
RECUR_MIN = 2


def parse_section_titles(markdown: str) -> list[str]:
    """Every `## Heading` in a markdown note, in order."""
    return [m.group(1).strip() for m in _re_mod.finditer(r"^##\s+(.+?)\s*$", markdown, _re_mod.MULTILINE)]


def _standard_titles(kind: str) -> set[str]:
    """Section titles that are part of the frozen skeleton or the shared tail —
    i.e. NOT problem-specific. Used to isolate the 'extra' sections in a note."""
    std = {t for t, _f, _fb in SECTIONS_FOR.get(kind, [])}
    tail = {t for t, _f in TAIL_SECTIONS}
    return std | tail


def adaptive_sections(
    kind: str,
    related_texts: list[str],
    *,
    recur_min: int = RECUR_MIN,
) -> list[tuple[str, str, str]]:
    """Build the section spec for a new note of `kind`, given the markdown of its
    most-related past notes.

    = the frozen skeleton  +  problem-specific sections that appear in
    >= recur_min of the related notes (slotted just before the skeleton's final
    resolution sections). Extra fields are keyed `x_<slug>` so the extractor
    fills them and render reads them back.

    Returns a list of (section_title, field_name, fallback) — drop-in for
    render_body(sections=...).
    """
    base = list(SECTIONS_FOR.get(kind, SECTIONS_FOR["debug"]))
    std = _standard_titles(kind)

    from collections import Counter
    counts: Counter = Counter()
    for txt in related_texts or []:
        for title in dict.fromkeys(parse_section_titles(txt)):   # dedupe within a note
            if title not in std:
                counts[title] += 1

    extras = [t for t, c in counts.items() if c >= recur_min]
    extra_specs = [(t, "x_" + _slug(t), "") for t in extras]
    if not extra_specs:
        return base

    # Slot problem-specific sections before the final two skeleton sections
    # (the resolution pair, e.g. Fix/Verification), so evidence precedes outcome.
    if len(base) >= 2:
        return base[:-2] + extra_specs + base[-2:]
    return base + extra_specs


# ──────────────────────────────────────────────────────────────────────────────
# Public render() — frontmatter + body
# ──────────────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    """UTC ISO-8601 with second precision — what frontmatter uses for created/updated."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_frontmatter(
    *,
    kind: str,
    title: str,
    note_id: str,
    subsystem: str | list[str] = "unknown",
    tags: Iterable[str] | None = None,
    status: str = "",
    confidence: str = "",          # high | medium | low
    entities: dict | None = None,  # {files: [...], symbols: [...], errors: [...], packages: [...], urls: [...], concepts: [...]}
    git: dict | None = None,       # {commit, branch, changed_files}
    linked: Iterable[str] | None = None,
    project: str = "",
    extras: dict | None = None,
) -> dict:
    """Build a frontmatter dict with consistent key ordering.

    Use this then pass the result through render_frontmatter() — or pass it
    inside `meta=` to render().
    """
    meta: dict[str, Any] = {
        "id":         note_id,
        "type":       kind,
        # Back-compat: keep the old `memory_type` field so legacy code paths
        # (e.g. memcon_query payload filters, watcher.py) still work.
        "memory_type": _MEMORY_TYPE_FOR.get(kind, "episodic"),
        "created":    _now_iso(),
        "updated":    _now_iso(),
        "project":    project or "",
        "subsystem":  subsystem if isinstance(subsystem, list) else (subsystem or "unknown"),
        "tags":       list(tags or []),
        "status":     status,
        "confidence": confidence,
        "entities":   entities or {},
        "git":        git or {},
        "linked":     list(linked or []),
    }
    if extras:
        meta.update(extras)
    return meta


# Map new kinds → legacy `memory_type` payload field used elsewhere.
_MEMORY_TYPE_FOR: dict[str, str] = {
    "debug":        "episodic",
    "experiment":   "episodic",
    "session":      "episodic",
    "meeting":      "episodic",
    "breakthrough": "episodic",
    "decision":     "causal",
    "concept":      "semantic",
    "reference":    "semantic",
}


def render(
    *,
    kind: str,
    title: str,
    fields: dict,
    meta: dict | None = None,
    sections: list | None = None,   # explicit section spec (adaptive templates)
    # Convenience args — if `meta` not supplied, these build it
    note_id: str = "",
    subsystem: str | list[str] = "unknown",
    tags: Iterable[str] | None = None,
    status: str = "",
    confidence: str = "",
    entities: dict | None = None,
    git: dict | None = None,
    linked: Iterable[str] | None = None,
    project: str = "",
) -> str:
    """Render a complete note (frontmatter + body) as a markdown string.

    Either pass a pre-built `meta` dict, or pass the convenience args and
    we'll build one with make_frontmatter().
    """
    if kind not in ALL_KINDS:
        kind = "debug"
    if meta is None:
        meta = make_frontmatter(
            kind=kind,
            title=title,
            note_id=note_id or _slug(title),
            subsystem=subsystem,
            tags=tags,
            status=status,
            confidence=confidence,
            entities=entities,
            git=git,
            linked=linked,
            project=project,
        )
    fm = render_frontmatter(meta)
    body = render_body(kind, title, fields, sections=sections)
    return f"{fm}\n\n{body}"


# ──────────────────────────────────────────────────────────────────────────────
# Slug helper (used by writer.py too)
# ──────────────────────────────────────────────────────────────────────────────

def _slug(title: str, max_len: int = 50) -> str:
    """Conservative filename slug — keeps alnum + dash, collapses everything else."""
    import re
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "untitled")[:max_len]
