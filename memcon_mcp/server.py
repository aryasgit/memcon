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

# Load .env from the REPO dir explicitly. Claude Desktop spawns this server with
# cwd=/ (the MCP registration has no cwd), so a bare load_dotenv() finds nothing;
# an explicit path makes LLM_API_KEY / overrides load regardless of cwd.
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import time as _time

def _get_llm():
    """Shared OPTIONAL local-LLM client with a hard timeout (see memory.llm).
    Callers gate on memory.llm.is_available() first — memcon runs fine with no
    local LLM (the assistant does the reasoning)."""
    from memory.llm import get_client
    return get_client()


_last_autosync = [0.0]
_AUTOSYNC_THROTTLE_S = 3.0


def _autosync() -> None:
    """Trigger an index reconcile in the BACKGROUND — never on the read path.

    The old version ran a full vault reconcile synchronously before every read,
    so the first read after a bulk write became a re-ingest storm that froze the
    client. Now the read returns immediately and the bounded worker brings the
    index current within a moment (the debounced watcher + startup reindex are
    the other convergence paths). Throttled so rapid reads don't pile up syncs."""
    now = _time.monotonic()
    if now - _last_autosync[0] < _AUTOSYNC_THROTTLE_S:
        return
    _last_autosync[0] = now
    try:
        from memory.worker import submit
        from ingestion.ingest import sync_index
        submit(sync_index)
    except Exception:
        pass


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
    _autosync()
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
    _autosync()
    ensure_collection()
    results = _query(question, top_k=top_k, subsystem=subsystem)
    if not results:
        return {"answer": "No relevant memory found.", "sources": [],
                "chunks_used": 0, "raw_chunks": []}

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
    sources = sorted({r["doc_name"] for r in results})
    from memory.llm import is_available
    if not is_available():
        # Lean mode (no local LLM): hand the grounding chunks back so YOU, the
        # calling assistant, compose the answer. This is the default path.
        return {
            "answer": None,
            "note": "No local LLM configured — compose the answer yourself from raw_chunks.",
            "sources": sources,
            "chunks_used": len(results),
            "raw_chunks": results,
        }
    try:
        resp = _get_llm().chat.completions.create(
            model=cfg('llm', 'model'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg('llm', 'max_tokens'),
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        # LLM down/timed out — still return the grounding chunks rather than
        # hanging the stdio path or erroring the whole tool call.
        answer = (f"(Local LLM unavailable: {e}. The relevant memory chunks are "
                  f"returned below for you to reason over.)")
    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(results),
        "raw_chunks": results,
    }


@mcp.tool()
def memcon_recall(problem: str, k: int = 5) -> dict:
    """
    THE flagship recall tool — reach for this the MOMENT the user hits a
    problem, bug, error, regression, or asks "have we dealt with this before?"
    / "didn't this happen already?" / "what did we try last time?".

    Unlike memcon_query (which returns raw chunks), memcon_recall returns a
    FUSED PLATTER of the most relevant past work, ranked by three axes at once:

      • SIMILAR  — past notes semantically matching the current problem
      • RECENT   — lifted toward the latest attempt, because the approach
                   evolves and the newest try reflects current reality
      • OUTCOME  — every match labelled resolved / open / failed, so a past
                   FAILURE warns you ("you tried X, it didn't hold") and a
                   past FIX answers you ("last time this was fixed by Y")

    It also returns a one-line `summary` like:
        "You've hit something like this 3 times. Most recent (11d ago) was
         fixed by: re-seated connectors + bumped PSU 3A→5A."

    Use memcon_recall for debugging / "am I repeating myself?" moments; use
    memcon_query only when you want raw context chunks to reason over.

    Args:
        problem: natural-language description of what's happening NOW
                 (e.g. "RR servo overheating during backward gait again").
        k: how many past matches to return. Default 5.

    Returns: { problem, summary,
               matches: [{doc_name, title, similarity, age_days, recency,
                          score, outcome, what_was_tried, excerpt}],
               count }
    """
    _autosync()
    from memory.recall import recall as _recall
    return _recall(problem, k=k)


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
    from memory.llm import is_available
    if not is_available():
        # Lean mode: no local LLM. Hand the recent notes back for YOU to summarise.
        return {
            "summary": None,
            "note": "No local LLM configured — summarise the notes below yourself.",
            "notes": [{"name": n, "folder": f} for n, f, _, _ in recent],
            "notes_considered": len(recent),
            "since_days": since_days,
        }
    try:
        resp = _get_llm().chat.completions.create(
            model=cfg('llm', 'model'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg('llm', 'max_tokens'),
        )
        summary = resp.choices[0].message.content
    except Exception as e:
        summary = (f"(Local LLM unavailable: {e}.) {len(recent)} notes were touched "
                   f"in the last {since_days} days.")
    return {
        "summary": summary,
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
    error logs, conversation excerpts) and call this tool.

    THIS CALL RETURNS INSTANTLY. It writes a note immediately with your raw
    text preserved (already searchable), then runs the multi-pass local-LLM
    extraction IN THE BACKGROUND to fill in structured sections + entities +
    the adaptive template. You do NOT need to wait, poll, or re-call — the
    structuring completes on its own within ~a minute. (This is deliberate:
    the extraction can take minutes on a long input with a local model, which
    would otherwise blow past the MCP tool-call timeout. Never block on it.)

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
                      The richer the text, the better the background extraction.
        hint:         "auto" (default) lets the classifier pick the kind. Force
                      one of: "debug" | "decision" | "experiment" | "concept" |
                      "reference" | "meeting" | "breakthrough" | "session".
        run_critique: Adds a self-critique pass to the BACKGROUND extraction
                      (slower, slightly higher quality). Safe to enable — it
                      runs off the tool-call thread, so it never affects this
                      call's latency. Default False.

    Returns instantly: { "status": "saved", "kind", "path", "note" }
    The note at `path` exists and is searchable immediately; structured
    sections + entities appear shortly after.
    """
    from memory.capture import capture as _capture
    try:
        return _capture(text, hint=hint, run_critique=run_critique)
    except Exception as e:
        return {"error": f"capture failed: {e}",
                "fallback": "use memcon_write_debug/decision/experiment/concept/reference/meeting/breakthrough/session_summary directly"}


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


@mcp.tool()
def memcon_reindex() -> dict:
    """Rebuild the search index from the vault files. Call this whenever
    memcon_recall / memcon_query / memcon_ask come back EMPTY for content you
    KNOW is written in a note — it means the search index drifted from the files
    on disk (a note saved while Qdrant was down, a note edited directly in
    Obsidian, or a once-empty note that got refilled). Re-ingests every note as
    a clean replace so search matches exactly what's on disk. Fast for a normal
    vault. After this, retry the recall — the content will be findable.

    Returns: { status, files, chunks }
    """
    # Run the full rebuild on the background worker so the stdio call returns
    # immediately instead of blocking on a whole-vault re-embed. Watch the chunk
    # count climb via memcon_stats as it completes.
    from memory.worker import submit
    from ingestion.ingest import reindex_vault
    if submit(reindex_vault):
        return {"status": "reindex started in background",
                "note": "Re-ingesting every note off-thread; call memcon_stats to watch progress."}
    # Worker saturated — fall back to synchronous so the request still completes.
    return {"status": "reindexed", **reindex_vault()}


def main() -> None:
    # Self-heal: reconcile the search index with the vault files in the
    # BACKGROUND on startup. A note written while Qdrant was down (or edited in
    # Obsidian) becomes searchable shortly after Claude reconnects — without
    # blocking the server from coming up. The index stops silently drifting.
    import threading

    def _bg_prewarm():
        # Warm (or first-run DOWNLOAD) the embedding model in the background so the
        # first write never pays it on the stdio path. find_related skips related
        # links until this finishes, so writes stay instant either way.
        try:
            from ingestion.embedder import get_model
            get_model()
        except Exception:
            pass

    def _bg_reindex():
        try:
            from ingestion.ingest import sync_index
            sync_index()
        except Exception:
            pass

    threading.Thread(target=_bg_prewarm, daemon=True, name="memcon-startup-prewarm").start()
    threading.Thread(target=_bg_reindex, daemon=True, name="memcon-startup-reindex").start()
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
