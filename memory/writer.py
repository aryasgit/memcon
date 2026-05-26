"""
memory/writer.py
Memcon writes and updates memory automatically.
- log_decision()   → creates a decisions/ note
- log_debug()      → creates a debugging/ note
- update_note()    → appends new findings to existing note
- summarise_session() → end-of-session auto-summary

Every new note gets an auto-generated `## Related` section with Obsidian
[[wikilinks]] pointing at the top-K semantically similar existing notes —
so the graph view fills itself in.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from datetime import datetime
from config import cfg
from ingestion.ingest import ingest_file

VAULT = Path(cfg('vault', 'path'))


def _find_related(query_text: str, exclude_doc: str, top_k: int = 4, max_links: int = 3) -> list[str]:
    """Return up to `max_links` doc_names semantically nearest to query_text.

    Excludes the note we're about to write (by doc_name) so a note never
    links to itself. Best-effort: any failure (no embedder, no Qdrant, empty
    vault) returns []."""
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


def _write_note(folder: str, filename: str, content: str) -> str:
    """Write a note to vault, append related [[wikilinks]], and ingest."""
    target_dir = VAULT / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / f"{filename}.md"

    # Find semantically related notes BEFORE writing — so the new note isn't
    # in the index yet and can't show up as its own neighbour.
    related = _find_related(content, exclude_doc=filename)
    if related:
        content = content.rstrip() + "\n\n## Related\n" + \
                  "\n".join(f"- [[{name}]]" for name in related) + "\n"

    # Append-on-exists, write fresh otherwise
    if filepath.exists():
        with open(filepath, 'a') as f:
            f.write(f"\n\n---\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{content}")
    else:
        with open(filepath, 'w') as f:
            f.write(content)

    ingest_file(str(filepath))
    return str(filepath)


def log_decision(title: str, decision: str, reasoning: str,
                 subsystem: str = "unknown", tags: list = None) -> str:
    """Log an engineering decision to decisions/ vault."""
    tags_str = str(tags or [])
    date = datetime.now().strftime('%Y-%m-%d')
    slug = title.lower().replace(' ', '_')[:40]

    content = f"""---
memory_type: causal
subsystem: {subsystem}
tags: {tags_str}
date: {date}
---

# {title}

## Decision
{decision}

## Reasoning
{reasoning}

## Date
{date}
"""
    return _write_note('decisions', slug, content)


def log_debug(title: str, symptom: str, cause: str = "",
              fix: str = "", status: str = "open",
              subsystem: str = "unknown", tags: list = None) -> str:
    """Log a debugging session to debugging/ vault."""
    tags_str = str(tags or [])
    date = datetime.now().strftime('%Y-%m-%d')
    slug = title.lower().replace(' ', '_')[:40]

    content = f"""---
memory_type: episodic
subsystem: {subsystem}
tags: {tags_str}
date: {date}
---

# {title}

## Symptom
{symptom}

## Cause
{cause if cause else "Under investigation."}

## Fix Applied
{fix if fix else "None yet."}

## Status
{status}
"""
    return _write_note('debugging', slug, content)


def update_note(filepath: str, new_content: str) -> str:
    """Append new findings to an existing note and re-ingest."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Note not found: {filepath}")
    with open(path, 'a') as f:
        f.write(f"\n\n---\n*Update — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{new_content}\n")
    ingest_file(str(path))
    return str(path)


def log_experiment(title: str, hypothesis: str, result: str,
                   conclusion: str, subsystem: str = "unknown",
                   tags: list = None) -> str:
    """Log an experiment result to experiments/ vault."""
    tags_str = str(tags or [])
    date = datetime.now().strftime('%Y-%m-%d')
    slug = title.lower().replace(' ', '_')[:40]

    content = f"""---
memory_type: episodic
subsystem: {subsystem}
tags: {tags_str}
date: {date}
---

# {title}

## Hypothesis
{hypothesis}

## Result
{result}

## Conclusion
{conclusion}
"""
    return _write_note('experiments', slug, content)


def summarise_session(summary: str, subsystem: str = "unknown") -> str:
    """Auto-write a session summary at end of work session."""
    date = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    content = f"""---
memory_type: episodic
subsystem: {subsystem}
tags: [session-summary]
date: {date}
---

# Session Summary — {date}

{summary}
"""
    return _write_note('decisions', f"session_{timestamp}", content)
