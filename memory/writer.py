"""
memory/writer.py
Memcon writes and updates memory automatically.

Public API (the canonical entry point)
--------------------------------------
    log_universal(kind, title, fields, **frontmatter_kwargs) → str (filepath)

Convenience wrappers (back-compat with the existing MCP tools)
--------------------------------------------------------------
    log_debug(title, symptom, cause, fix, status, subsystem, tags)
    log_decision(title, decision, reasoning, subsystem, tags)
    log_experiment(title, hypothesis, result, conclusion, subsystem, tags)
    log_concept(title, definition, why, example, pitfalls, ...)
    log_reference(title, summary, key_points, notes, source, ...)
    log_meeting(title, attendees, notes, decisions, actions, ...)
    log_breakthrough(title, background, insight, implication, next_steps, ...)
    summarise_session(summary, subsystem)

Every new note gets:
  - Rich YAML frontmatter (id, type, created, updated, subsystem, tags, status,
    confidence, entities, git, linked) via templates.make_frontmatter()
  - Per-type body sections via templates.render_body()
  - Auto-generated `## Related` section with Obsidian [[wikilinks]] pointing
    at the top-K semantically similar existing notes
  - Auto-enrichment kicked off in the background (git context, see-also lines)
    via memory.enricher
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable

from config import cfg
from ingestion.ingest import ingest_file
from memory.templates import (
    ALL_KINDS, FOLDER_FOR, SECTIONS_FOR, _slug,
    make_frontmatter, render_body, render_frontmatter, render,
)

VAULT = Path(cfg('vault', 'path'))


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _find_related(query_text: str, exclude_doc: str, top_k: int = 4, max_links: int = 3) -> list[str]:
    """Return up to `max_links` doc_names semantically nearest to query_text.

    Excludes the note we're about to write (by doc_name) so a note never
    links to itself. Best-effort: any failure (no embedder, no Qdrant, empty
    vault) returns [].
    """
    try:
        from memory.retrieve import query as _semantic_query
        results = _semantic_query(query_text, top_k=top_k)
    except Exception:
        return []
    seen, out = set(), []
    for r in results:
        dn = r.get('doc_name')
        if not dn or dn == exclude_doc or dn in seen:
            continue
        seen.add(dn)
        out.append(dn)
        if len(out) >= max_links:
            break
    return out


def _related_md(links: list[str]) -> str:
    """Build the body of the ## Related section from a list of doc_names."""
    if not links:
        return ""
    return "\n".join(f"- [[{name}]]" for name in links)


def _project_name() -> str:
    try:
        return cfg('project', 'name')
    except Exception:
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Canonical entry point
# ──────────────────────────────────────────────────────────────────────────────

def log_universal(
    kind: str,
    title: str,
    fields: dict,
    *,
    subsystem: str | list[str] = "unknown",
    tags: Iterable[str] | None = None,
    status: str = "",
    confidence: str = "",
    entities: dict | None = None,
    git: dict | None = None,
    project: str | None = None,
    extras: dict | None = None,
    enrich: bool = True,
) -> str:
    """Write any kind of note to the vault.

    Steps:
      1. Build a `note_id` from the title (timestamp-prefixed for uniqueness).
      2. Compute Obsidian wikilinks to top-3 semantic neighbours.
      3. Build frontmatter (rich) + body (per-type sections + Context + Related).
      4. Write to {vault}/{folder-for-kind}/{slug}.md.
      5. Ingest the new file into Qdrant.
      6. Update the entity index (best-effort).
      7. Kick off background enrichment (best-effort).

    Returns the absolute filepath.
    """
    if kind not in ALL_KINDS:
        kind = "debug"

    slug = _slug(title)
    date = datetime.now().strftime('%Y-%m-%d')
    note_id = f"{date}_{slug}"

    # Compose a representative chunk for the related-link search. We use the
    # title + the first big body field as the query text so neighbours match
    # the *substance* of the note, not just its name.
    semantic_query_text = title + "\n" + _semantic_summary(kind, fields)
    related = _find_related(semantic_query_text, exclude_doc=slug)

    # Merge "linked" frontmatter list — caller can pre-seed it, related fills gaps
    linked_set: list[str] = list(dict.fromkeys(list(extras.pop("linked", []) if extras else []) + related))

    fields = dict(fields)  # don't mutate caller's dict
    fields["related_md"] = _related_md(related)
    # Caller can pass context_raw / see_also in fields directly — we just pass-through.

    meta = make_frontmatter(
        kind=kind,
        title=title,
        note_id=note_id,
        subsystem=subsystem,
        tags=tags,
        status=status,
        confidence=confidence,
        entities=entities,
        git=git,
        linked=linked_set,
        project=project if project is not None else _project_name(),
        extras=extras,
    )

    content = render(kind=kind, title=title, fields=fields, meta=meta)

    folder = FOLDER_FOR.get(kind, "debugging")
    target_dir = VAULT / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / f"{slug}.md"

    if filepath.exists():
        # Append-on-exists: preserve the original frontmatter, append a divider
        # + an Update block with the new body sections. This way recurrence is
        # naturally preserved.
        with open(filepath, 'a') as f:
            f.write(
                f"\n\n---\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
                + render_body(kind, title, fields)
            )
    else:
        with open(filepath, 'w') as f:
            f.write(content)

    # Ingest into Qdrant immediately so semantic search picks it up.
    try:
        ingest_file(str(filepath))
    except Exception as e:
        print(f"[writer] ingest failed (continuing): {e}", file=sys.stderr)

    # Update entity index (best-effort — module may not be present yet at boot).
    if entities:
        try:
            from memory.entity_index import index_note
            index_note(doc_name=slug, entities=entities, path=str(filepath))
        except Exception as e:
            print(f"[writer] entity-index update failed (continuing): {e}", file=sys.stderr)

    # Kick off background enrichment (non-blocking).
    if enrich:
        try:
            from memory.enricher import enrich_async
            enrich_async(str(filepath), kind=kind, title=title, related=related)
        except Exception:
            pass  # enrichment is optional — never break the write path

    return str(filepath)


# ──────────────────────────────────────────────────────────────────────────────
# Per-type convenience wrappers — preserved API surface
# ──────────────────────────────────────────────────────────────────────────────

def log_debug(
    title: str, symptom: str, cause: str = "",
    fix: str = "", status: str = "open",
    subsystem: str = "unknown", tags: list | None = None,
    *, tldr: str = "", investigation: str = "", verification: str = "",
    context_raw: str = "", entities: dict | None = None,
    confidence: str = "",
) -> str:
    """Log a debugging session. New optional kwargs (tldr/investigation/etc.)
    are picked up automatically when memcon_capture or callers populate them."""
    return log_universal(
        kind="debug",
        title=title,
        fields={
            "tldr":          tldr,
            "symptom":       symptom,
            "investigation": investigation,
            "cause":         cause,
            "fix":           fix,
            "verification":  verification,
            "context_raw":   context_raw,
        },
        subsystem=subsystem,
        tags=tags,
        status=status,
        confidence=confidence,
        entities=entities,
    )


def log_decision(
    title: str, decision: str, reasoning: str,
    subsystem: str = "unknown", tags: list | None = None,
    *, tldr: str = "", context: str = "", options: str = "",
    consequences: str = "", context_raw: str = "",
    entities: dict | None = None, confidence: str = "",
) -> str:
    """Log an engineering decision."""
    return log_universal(
        kind="decision",
        title=title,
        fields={
            "tldr":         tldr,
            "context":      context,
            "options":      options,
            "decision":     decision,
            "reasoning":    reasoning,
            "consequences": consequences,
            "context_raw":  context_raw,
        },
        subsystem=subsystem,
        tags=tags,
        confidence=confidence,
        entities=entities,
    )


def log_experiment(
    title: str, hypothesis: str, result: str,
    conclusion: str, subsystem: str = "unknown",
    tags: list | None = None,
    *, tldr: str = "", setup: str = "", context_raw: str = "",
    entities: dict | None = None, confidence: str = "",
) -> str:
    """Log an experiment / measurement / test run."""
    return log_universal(
        kind="experiment",
        title=title,
        fields={
            "tldr":        tldr,
            "hypothesis":  hypothesis,
            "setup":       setup,
            "result":      result,
            "conclusion":  conclusion,
            "context_raw": context_raw,
        },
        subsystem=subsystem,
        tags=tags,
        confidence=confidence,
        entities=entities,
    )


def log_concept(
    title: str, definition: str,
    *, why: str = "", example: str = "", pitfalls: str = "",
    tldr: str = "", subsystem: str = "unknown",
    tags: list | None = None, context_raw: str = "",
    entities: dict | None = None, confidence: str = "",
) -> str:
    """Log a concept / definition / mental model."""
    return log_universal(
        kind="concept",
        title=title,
        fields={
            "tldr":        tldr,
            "definition":  definition,
            "why":         why,
            "example":     example,
            "pitfalls":    pitfalls,
            "context_raw": context_raw,
        },
        subsystem=subsystem,
        tags=tags,
        confidence=confidence,
        entities=entities,
    )


def log_reference(
    title: str, summary: str,
    *, key_points: str = "", notes: str = "", source: str = "",
    tldr: str = "", subsystem: str = "unknown",
    tags: list | None = None, context_raw: str = "",
    entities: dict | None = None, confidence: str = "",
) -> str:
    """Log a reference / API / spec / external resource."""
    return log_universal(
        kind="reference",
        title=title,
        fields={
            "tldr":        tldr,
            "summary":     summary,
            "key_points":  key_points,
            "notes":       notes,
            "source":      source,
            "context_raw": context_raw,
        },
        subsystem=subsystem,
        tags=tags,
        confidence=confidence,
        entities=entities,
    )


def log_meeting(
    title: str, notes: str,
    *, attendees: str = "", decisions: str = "", actions: str = "",
    tldr: str = "", subsystem: str = "unknown",
    tags: list | None = None, context_raw: str = "",
    entities: dict | None = None, confidence: str = "",
) -> str:
    """Log meeting / sync notes."""
    return log_universal(
        kind="meeting",
        title=title,
        fields={
            "tldr":        tldr,
            "attendees":   attendees,
            "notes":       notes,
            "decisions":   decisions,
            "actions":     actions,
            "context_raw": context_raw,
        },
        subsystem=subsystem,
        tags=tags,
        confidence=confidence,
        entities=entities,
    )


def log_breakthrough(
    title: str, insight: str,
    *, background: str = "", implication: str = "", next_steps: str = "",
    tldr: str = "", subsystem: str = "unknown",
    tags: list | None = None, context_raw: str = "",
    entities: dict | None = None, confidence: str = "",
) -> str:
    """Log a breakthrough / 'aha' moment."""
    return log_universal(
        kind="breakthrough",
        title=title,
        fields={
            "tldr":        tldr,
            "background":  background,
            "insight":     insight,
            "implication": implication,
            "next_steps":  next_steps,
            "context_raw": context_raw,
        },
        subsystem=subsystem,
        tags=tags,
        confidence=confidence,
        entities=entities,
    )


def summarise_session(summary: str, subsystem: str = "unknown") -> str:
    """End-of-session roll-up. Accepts a single free-form summary string, or
    (preferred) a multi-section summary the LLM already structured.
    """
    title = f"Session — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return log_universal(
        kind="session",
        title=title,
        fields={
            "tldr":       summary[:280] if summary else "",
            "worked_on":  summary,
            "context_raw": "",
        },
        subsystem=subsystem,
        tags=["session-summary"],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Update existing note
# ──────────────────────────────────────────────────────────────────────────────

def update_note(filepath: str, new_content: str) -> str:
    """Append new findings to an existing note and re-ingest."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Note not found: {filepath}")
    with open(path, 'a') as f:
        f.write(
            f"\n\n---\n*Update — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
            f"{new_content}\n"
        )
    try:
        ingest_file(str(path))
    except Exception as e:
        print(f"[writer] re-ingest after update failed: {e}", file=sys.stderr)
    return str(path)


# ──────────────────────────────────────────────────────────────────────────────
# Internal helper — pull the "meatiest" field for related-search seeding
# ──────────────────────────────────────────────────────────────────────────────

def _semantic_summary(kind: str, fields: dict) -> str:
    """Pick the field with the most prose to use as the related-search query.

    Investigation > Notes > Reasoning > Definition > Result > anything else.
    """
    priority = [
        "investigation", "notes", "reasoning", "definition", "result",
        "insight", "summary", "symptom", "fix", "decision", "conclusion",
        "tldr", "context_raw",
    ]
    for key in priority:
        v = fields.get(key)
        if v and isinstance(v, str) and len(v.strip()) > 30:
            return v
    # Fallback: concatenate all non-empty string fields
    return "\n".join(str(v) for v in fields.values() if isinstance(v, str) and v.strip())[:1200]


# Re-export the helper for callers that already used it
def _write_note(folder: str, filename: str, content: str) -> str:
    """Legacy helper — writes raw markdown to vault/{folder}/{filename}.md.

    Kept for any external scripts that imported it. New code should use
    log_universal() instead.
    """
    target_dir = VAULT / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / f"{filename}.md"
    if filepath.exists():
        with open(filepath, 'a') as f:
            f.write(f"\n\n---\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{content}")
    else:
        with open(filepath, 'w') as f:
            f.write(content)
    try:
        ingest_file(str(filepath))
    except Exception as e:
        print(f"[writer] ingest failed: {e}", file=sys.stderr)
    return str(filepath)
