"""
Memcon MCP Server — exposes Memcon memory as Model Context Protocol tools.

Lets Claude (Desktop, Cursor, Code) auto-query relevant past work before
answering, and auto-write debug sessions / decisions / experiments after
solving a problem. No HTTP, no manual notes — Memcon becomes a persistent
backend brain for any LLM session.

Run as stdio server (default for Claude Desktop / Cursor):
    python3 -m memcon_mcp.server

Tools exposed:
    memcon_query           — semantic search, returns relevant chunks
    memcon_ask             — LLM-grounded answer (uses Memcon's local LLM)
    memcon_write_debug     — save a debugging session note
    memcon_write_decision  — save an engineering decision
    memcon_write_experiment — save an experiment result
    memcon_session_summary — save an end-of-session summary
    memcon_update_note     — append findings to an existing note
    memcon_stats           — chunk count, project info
    memcon_subsystems      — list configured subsystems
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Any
from mcp.server.fastmcp import FastMCP

from config import cfg
from memory.retrieve import query as _query
from memory.writer import (
    log_debug, log_decision, log_experiment,
    log_concept, log_reference, log_meeting, log_breakthrough,
    log_universal, update_note, summarise_session,
)
from memory.qdrant_store import ensure_collection, get_stats
from memory.templates import ALL_KINDS

mcp = FastMCP("memcon")


@mcp.tool()
def memcon_query(query: str, top_k: int = 5, subsystem: str | None = None) -> dict:
    """
    Semantic search across the project's memory. Use this BEFORE answering any
    question about the project — it returns only the chunks relevant to the
    symptoms/keywords you pass, not the whole memory. Cheap to call.

    Args:
        query: Natural-language description of the problem or topic
               (e.g. "servo overheats during backward gait").
        top_k: How many top matches to return. Default 5.
        subsystem: Optional filter (e.g. "servo", "imu", "gait").

    Returns: { "results": [ {score, text, doc_name, subsystem, memory_type, tags}, ... ] }
    """
    ensure_collection()
    results = _query(query, top_k=top_k, subsystem=subsystem)
    return {"results": results, "count": len(results)}


@mcp.tool()
def memcon_ask(question: str, top_k: int = 5, subsystem: str | None = None) -> dict:
    """
    Ask Memcon's local LLM a question grounded in the project's memory.
    Use this when you want a self-contained answer with sources. Prefer
    memcon_query when you (the calling LLM) want raw context to reason over.

    Args:
        question: The question to answer.
        top_k: How many memory chunks to use as context.
        subsystem: Optional filter.

    Returns: { "answer", "sources", "chunks_used", "raw_chunks" }
    """
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()

    ensure_collection()
    results = _query(question, top_k=top_k, subsystem=subsystem)
    if not results:
        return {"answer": "No relevant memory found.", "sources": [],
                "chunks_used": 0, "raw_chunks": []}

    llm = OpenAI(
        base_url=cfg('llm', 'base_url'),
        api_key=os.getenv("LLM_API_KEY", "ollama"),
    )
    context = "\n\n---\n\n".join(
        f"[{r['memory_type']} | {r['subsystem']} | score={r['score']}]\n{r['text']}"
        for r in results
    )
    prompt = (
        "You are an engineering memory assistant.\n"
        "Answer using ONLY the context below. Be concise and technical.\n"
        "If the context doesn't answer the question, say so explicitly.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION: {question}\n\nANSWER:"
    )
    resp = llm.chat.completions.create(
        model=cfg('llm', 'model'),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=cfg('llm', 'max_tokens'),
    )
    return {
        "answer": resp.choices[0].message.content,
        "sources": sorted({r["doc_name"] for r in results}),
        "chunks_used": len(results),
        "raw_chunks": results,
    }


@mcp.tool()
def memcon_write_debug(
    title: str,
    symptom: str,
    cause: str = "",
    fix: str = "",
    status: str = "open",
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save a debugging session with PRE-STRUCTURED fields. Use this only when
    you already have title/symptom/etc. cleanly separated (e.g. from a form
    or another tool). For natural-language user requests like "save this
    debug session", prefer `memcon_capture` instead — it has the local LLM
    do the field extraction for you.

    Args:
        title: Short descriptive title (e.g. "RR Wrist Overheating").
        symptom: What was observed.
        cause: Root cause if known.
        fix: What resolved it (or current workaround).
        status: "open" | "fixed" | "investigating".
        subsystem: One of the configured subsystems (memcon_subsystems).
        tags: Optional list of free-form tags.
    """
    path = log_debug(title, symptom, cause, fix, status, subsystem, tags or [])
    return {"status": "written", "path": path}


@mcp.tool()
def memcon_write_decision(
    title: str,
    decision: str,
    reasoning: str,
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save an engineering decision to memory. Use this when a non-obvious choice
    was made (library, architecture, trade-off) so the rationale survives.
    """
    path = log_decision(title, decision, reasoning, subsystem, tags or [])
    return {"status": "written", "path": path}


@mcp.tool()
def memcon_write_experiment(
    title: str,
    hypothesis: str,
    result: str,
    conclusion: str,
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save an experiment / measurement / test run to memory.
    """
    path = log_experiment(title, hypothesis, result, conclusion, subsystem, tags or [])
    return {"status": "written", "path": path}


@mcp.tool()
def memcon_session_summary(summary: str, subsystem: str = "unknown") -> dict:
    """
    Save an end-of-session summary capturing what was worked on, broken, fixed,
    or decided. Call this near the end of a working session.
    """
    path = summarise_session(summary, subsystem)
    return {"status": "written", "path": path}


@mcp.tool()
def memcon_update_note(filepath: str, content: str) -> dict:
    """
    Append new findings to an existing note (e.g. when a previously-open debug
    session gets resolved). `filepath` is the path returned by an earlier
    memcon_write_* call, or a doc_name visible in memcon_query results.
    """
    path = update_note(filepath, content)
    return {"status": "updated", "path": path}


@mcp.tool()
def memcon_stats() -> dict:
    """
    Project info — chunk count, collection name, project name, entity index
    size. Cheap diagnostic. Call this when the user asks "how big is my
    memory?" or "what's in my vault?".
    """
    s = get_stats()
    s["project"] = cfg('project', 'name')
    s["domain"] = cfg('project', 'domain')
    try:
        from memory.entity_index import stats as _entity_stats
        s["entity_index"] = _entity_stats()
    except Exception as e:
        s["entity_index"] = {"error": str(e)}
    return s


@mcp.tool()
def memcon_subsystems() -> dict:
    """
    List the configured subsystems + note kinds for this project. Use this
    as a guide when picking a `subsystem` for write tools, or when telling
    the user which kinds of notes Memcon can produce.

    Returns:
        subsystems    — list of configured subsystem tags (can be empty,
                        meaning "accept any string").
        memory_types  — legacy field, still emitted for back-compat.
        note_kinds    — the full set of note types Memcon understands.
    """
    try:
        subs = list(cfg('subsystems') or [])
    except Exception:
        subs = []
    try:
        mtypes = list(cfg('memory_types') or [])
    except Exception:
        mtypes = []
    return {
        "subsystems":   subs,
        "memory_types": mtypes,
        "note_kinds":   list(ALL_KINDS),
    }


@mcp.tool()
def memcon_timeline(since_days: int = 7, limit: int = 30, subsystem: str | None = None) -> dict:
    """
    Time-bounded slice of project memory — what was written in the last
    N days, newest first. Use this for "what did I work on this week?"
    or "what changed in memory since Friday?" type questions.

    Args:
        since_days: Look back this many days from now. Default 7.
        limit: Max number of notes to return. Default 30.
        subsystem: Optional filter (e.g. "servo").

    Returns: { "notes": [{path, name, folder, mtime_iso, age_days}, ...],
               "since_days", "count" }
    """
    from pathlib import Path
    from datetime import datetime, timedelta, timezone

    vault = Path(cfg('vault', 'path'))
    skip = set(cfg('vault', 'skip_dirs') or [])
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    out = []
    if vault.exists():
        for p in vault.rglob("*.md"):
            try:
                rel = p.relative_to(vault)
            except ValueError:
                continue
            if any(part in skip for part in rel.parts):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue

            # Optional subsystem filter — read frontmatter
            if subsystem:
                try:
                    import frontmatter
                    with open(p) as f:
                        meta = frontmatter.load(f).metadata
                    if meta.get("subsystem") != subsystem:
                        continue
                except Exception:
                    continue

            age_secs = (datetime.now(timezone.utc) - mtime).total_seconds()
            out.append({
                "path": str(p.relative_to(vault.parent)),
                "name": p.stem,
                "folder": p.parent.name,
                "mtime_iso": mtime.isoformat(),
                "age_days": round(age_secs / 86400, 2),
            })

    out.sort(key=lambda n: n["mtime_iso"], reverse=True)
    return {"notes": out[:limit], "since_days": since_days, "count": len(out)}


@mcp.tool()
def memcon_digest(since_days: int = 7) -> dict:
    """
    LLM-generated summary of what landed in memory over the last N days.
    Reads the recent notes from the vault and asks the local LLM to
    summarise themes, open items, and decisions. Use this for end-of-week
    standups, project status, or "remind me what I've been doing".

    Args:
        since_days: Look back this many days. Default 7.

    Returns: { "summary", "notes_considered", "since_days" }
    """
    from pathlib import Path
    from datetime import datetime, timedelta, timezone
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()

    vault = Path(cfg('vault', 'path'))
    skip = set(cfg('vault', 'skip_dirs') or [])
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    recent = []
    if vault.exists():
        for p in vault.rglob("*.md"):
            try:
                rel = p.relative_to(vault)
            except ValueError:
                continue
            if any(part in skip for part in rel.parts):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            if datetime.fromtimestamp(st.st_mtime, tz=timezone.utc) < cutoff:
                continue
            try:
                text = p.read_text()[:3000]  # cap each note to keep prompt small
            except Exception:
                continue
            recent.append((p.stem, p.parent.name, st.st_mtime, text))

    if not recent:
        return {"summary": f"No notes touched in the last {since_days} days.",
                "notes_considered": 0, "since_days": since_days}

    recent.sort(key=lambda r: r[2], reverse=True)
    recent = recent[:25]  # cap input length
    bundle = "\n\n---\n\n".join(
        f"## {folder}/{name}\n{text}" for name, folder, _, text in recent
    )

    llm = OpenAI(
        base_url=cfg('llm', 'base_url'),
        api_key=os.getenv("LLM_API_KEY", "ollama"),
    )
    prompt = (
        f"You are summarising an engineer's last {since_days} days of project memory.\n"
        f"Read the notes below (each is a debug session, decision, experiment, or session summary)\n"
        "and produce a concise digest with these sections:\n\n"
        "**Themes** — what topics came up repeatedly\n"
        "**Wins** — things that were fixed or decided\n"
        "**Open items** — things still in progress, status=open\n"
        "**Worth revisiting** — anything that might be worth following up\n\n"
        "Use 2-4 bullet points per section. No padding. If a section is empty, omit it.\n\n"
        f"NOTES:\n{bundle}\n\n"
        "DIGEST:"
    )
    resp = llm.chat.completions.create(
        model=cfg('llm', 'model'),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=cfg('llm', 'max_tokens'),
    )
    return {
        "summary": resp.choices[0].message.content,
        "notes_considered": len(recent),
        "since_days": since_days,
    }


@mcp.tool()
def memcon_capture(text: str, hint: str = "auto", run_critique: bool = False) -> dict:
    """
    DEFAULT WRITE TOOL — use this for ANY user instruction of the form
    "save this", "log this", "remember this", "save the debugging session",
    "log my decision", etc. Do NOT ask the user to spell out title/symptom/
    cause/fix yourself; instead, summarise the relevant span of the current
    conversation into `text` (the richer, the better — paragraphs, code,
    error logs, conversation excerpts — anything that gives the extractor
    something to work with) and call this tool. The local LLM runs a
    multi-pass extraction pipeline internally:

      1. CLASSIFY — picks the best kind from:
         debug | decision | experiment | concept | reference | meeting |
         breakthrough | session
      2. STRUCTURE — fills the per-kind sections (TL;DR + type-specific
         fields). Preserves a verbatim ## Context excerpt for embedding.
      3. ENTITIES — extracts files / symbols / errors / packages / urls /
         concepts mentioned, for keyword-exact recall later.
      4. (optional) CRITIQUE — second pass that re-reads the draft against
         the source. Only enable for long, complex inputs (doubles runtime).

    The note is then written with rich frontmatter (id, type, created,
    updated, subsystem, tags, status, confidence, entities, git, linked) and
    auto-linked to its top-3 semantic neighbours via Obsidian [[wikilinks]].
    A background pass adds git context + a `## See also` block after the
    write returns.

    When the user says ANY of:
      • "save this"  /  "save it"  /  "log this"  /  "remember this"
      • "save the debugging session"  /  "log this debug"
      • "save my decision (to use X)"  /  "log this decision"
      • "remember this experiment"  /  "log the experiment"
      • "save this concept"  /  "store this reference"  /  "log meeting notes"
      • "session summary"  /  "save today's session"
      → call this tool with a rich `text`.

    ONLY fall back to memcon_write_* when the user is explicitly providing
    pre-structured fields ("title: ..., symptom: ..., fix: ...").

    Args:
        text:         The content to capture — paragraphs, code, errors, logs.
                      The richer the text, the better the extraction.
        hint:         "auto" (default) lets the classifier pick. Force one of:
                      "debug" | "decision" | "experiment" | "concept" |
                      "reference" | "meeting" | "breakthrough" | "session".
        run_critique: If True, run a self-critique pass (doubles time, helps
                      on long inputs). Default False.

    Returns: { "status", "kind", "path", "title", "subsystem", "confidence",
               "entities", "passes_run" }
    """
    from memory.extractor import extract as _extract

    # Allowed subsystems from config — used as a soft constraint in the prompt.
    try:
        subs = list(cfg('subsystems') or [])
    except Exception:
        subs = []

    try:
        result = _extract(text, hint=hint, run_critique=run_critique, valid_subsystems=subs or None)
    except Exception as e:
        return {"error": f"extraction failed: {e}",
                "fallback": "use memcon_write_debug/decision/experiment/concept/reference/meeting/breakthrough/session_summary directly"}

    kind = result["kind"]
    if kind not in ALL_KINDS:
        kind = "debug"

    # If subsystems are constrained and the model picked one outside the list,
    # demote to "unknown" so retrieval filters don't silently drop the note.
    subsystem = result["subsystem"]
    if subs and subsystem not in subs:
        subsystem = "unknown"

    path = log_universal(
        kind=kind,
        title=result["title"],
        fields=result["fields"],
        subsystem=subsystem,
        tags=result["tags"],
        status=result["status"],
        confidence=result["confidence"],
        entities=result["entities"],
    )

    return {
        "status":     "written",
        "kind":       kind,
        "path":       path,
        "title":      result["title"],
        "subsystem":  subsystem,
        "confidence": result["confidence"],
        "entities":   result["entities"],
        "passes_run": result["meta"]["passes_run"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Concept / Reference / Meeting / Breakthrough — new note types in v3.1
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def memcon_write_concept(
    title: str,
    definition: str,
    why: str = "",
    example: str = "",
    pitfalls: str = "",
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save a concept / definition / mental model note. Use this when the user
    teaches you a domain term, explains a system invariant, or defines a
    "what is X" that should survive to future sessions.
    """
    path = log_concept(
        title=title, definition=definition, why=why,
        example=example, pitfalls=pitfalls,
        subsystem=subsystem, tags=tags or [],
    )
    return {"status": "written", "kind": "concept", "path": path}


@mcp.tool()
def memcon_write_reference(
    title: str,
    summary: str,
    key_points: str = "",
    notes: str = "",
    source: str = "",
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save a reference note — an API/spec/external resource captured locally
    so the relevant bits survive even if the source URL rots.
    """
    path = log_reference(
        title=title, summary=summary, key_points=key_points,
        notes=notes, source=source,
        subsystem=subsystem, tags=tags or [],
    )
    return {"status": "written", "kind": "reference", "path": path}


@mcp.tool()
def memcon_write_meeting(
    title: str,
    notes: str,
    attendees: str = "",
    decisions: str = "",
    actions: str = "",
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save meeting / sync notes. `decisions` and `actions` get their own
    sections so they're separately searchable.
    """
    path = log_meeting(
        title=title, notes=notes, attendees=attendees,
        decisions=decisions, actions=actions,
        subsystem=subsystem, tags=tags or [],
    )
    return {"status": "written", "kind": "meeting", "path": path}


@mcp.tool()
def memcon_write_breakthrough(
    title: str,
    insight: str,
    background: str = "",
    implication: str = "",
    next_steps: str = "",
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save a breakthrough / "aha" insight. Use when the user names a moment
    where understanding shifted — the kind of thing you want to find six
    months later.
    """
    path = log_breakthrough(
        title=title, insight=insight, background=background,
        implication=implication, next_steps=next_steps,
        subsystem=subsystem, tags=tags or [],
    )
    return {"status": "written", "kind": "breakthrough", "path": path}


def main() -> None:
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
