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
    update_note, summarise_session,
)
from memory.qdrant_store import ensure_collection, get_stats

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
    Project info — chunk count, collection name, project name. Cheap diagnostic.
    """
    s = get_stats()
    s["project"] = cfg('project', 'name')
    s["domain"] = cfg('project', 'domain')
    return s


@mcp.tool()
def memcon_subsystems() -> dict:
    """
    List the configured subsystems for this project. Use as a guide when
    deciding which `subsystem` value to pass to write/query tools.
    """
    return {
        "subsystems": cfg('subsystems'),
        "memory_types": cfg('memory_types'),
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
def memcon_capture(text: str, hint: str = "auto") -> dict:
    """
    DEFAULT WRITE TOOL — use this for ANY user instruction of the form
    "save this", "log this", "remember this", "save the debugging session",
    "log my decision", etc. Do NOT ask the user to spell out title/symptom/
    cause/fix yourself; instead, summarise the relevant span of the current
    conversation into `text` and call this tool. The local LLM running
    inside memcon will extract the structured fields itself.

    Concretely, when the user says ONE of:
      • "save this"  /  "save it"  /  "log this"
      • "save the debugging session"  /  "log this debug"
      • "save my decision (to use X)"  /  "log this decision"
      • "remember this experiment"  /  "log the experiment"
      • "session summary"  /  "save today's session"

    → look back over the recent conversation, write a clear paragraph that
       describes what happened (the problem, the cause if known, the fix if
       known — or the decision and its reasoning, etc.), and pass that as
       `text`. Always include enough detail that someone reading the saved
       note cold would understand it.

    Auto-routes to debug | decision | experiment | session_summary based on
    content, unless `hint` forces a kind. Auto-links to the top-3
    semantically related existing notes via Obsidian [[wikilinks]].

    ONLY fall back to memcon_write_debug / _decision / _experiment /
    session_summary when the user is explicitly giving you pre-structured
    fields ("title: ..., symptom: ..., fix: ...").

    Args:
        text: The content to capture. Pass a self-contained paragraph
              summarising the conversation — NOT a one-word command. The
              richer the text, the better the structured extraction.
        hint: "auto" (default) lets the LLM pick. Force with
              "debug" | "decision" | "experiment" | "session".

    Returns: { "status", "kind", "path", "extracted" }

    Example invocation (after a debugging conversation):
        memcon_capture(text="The RR servo overheated during backward gait.
            Diagnosed as vibration-loosened wiring causing power brownouts
            from servo current spikes. Fixed by re-seating the connectors
            and bumping the bench PSU current limit from 3A to 5A.")
    """
    import json as _json
    import re as _re
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()

    llm = OpenAI(
        base_url=cfg('llm', 'base_url'),
        api_key=os.getenv("LLM_API_KEY", "ollama"),
    )

    subs = cfg('subsystems')
    sub_list = ", ".join(subs)
    type_hint = "" if hint == "auto" else f"\nThe user explicitly tagged this as kind=\"{hint}\". Use that kind."

    prompt = f"""You are a structuring assistant. Read the input below and emit a single JSON object that fits one of these schemas. Pick the kind that fits best.{type_hint}

KIND = "debug":
  {{"kind":"debug","title":"...","symptom":"...","cause":"...","fix":"...","status":"open|fixed|investigating","subsystem":"<one of: {sub_list}>","tags":["..."]}}

KIND = "decision":
  {{"kind":"decision","title":"...","decision":"...","reasoning":"...","subsystem":"<one of: {sub_list}>","tags":["..."]}}

KIND = "experiment":
  {{"kind":"experiment","title":"...","hypothesis":"...","result":"...","conclusion":"...","subsystem":"<one of: {sub_list}>","tags":["..."]}}

KIND = "session":
  {{"kind":"session","summary":"...","subsystem":"<one of: {sub_list}>"}}

Rules:
- Title: <= 60 chars, descriptive, no quotes.
- subsystem MUST be one of the listed values, else "unknown".
- tags: 2-5 lowercase kebab-case terms, no #.
- If a field is genuinely unknown, use an empty string "" (not null).
- Output ONLY the JSON object. No markdown fences, no commentary, no leading text.

INPUT:
{text}

JSON:"""

    try:
        resp = llm.chat.completions.create(
            model=cfg('llm', 'model'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg('llm', 'max_tokens'),
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
    except Exception as e:
        return {"error": f"LLM call failed: {e}", "fallback": "use memcon_write_debug/decision/experiment/session_summary directly"}

    # Strip code fences if the model wrapped output anyway
    raw = _re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=_re.IGNORECASE | _re.MULTILINE).strip()
    # Grab the first {...} block to be defensive
    m = _re.search(r"\{.*\}", raw, _re.DOTALL)
    if not m:
        return {"error": "LLM did not return JSON", "raw_response": raw[:400]}
    try:
        data = _json.loads(m.group(0))
    except _json.JSONDecodeError as e:
        return {"error": f"could not parse JSON: {e}", "raw_response": raw[:400]}

    kind = (data.get("kind") or hint or "debug").lower()
    subsystem = data.get("subsystem") or "unknown"
    if subsystem not in subs:
        subsystem = "unknown"
    tags = data.get("tags") or []

    if kind == "decision":
        path = log_decision(
            title=data.get("title", "(untitled decision)"),
            decision=data.get("decision", ""),
            reasoning=data.get("reasoning", ""),
            subsystem=subsystem,
            tags=tags,
        )
    elif kind == "experiment":
        path = log_experiment(
            title=data.get("title", "(untitled experiment)"),
            hypothesis=data.get("hypothesis", ""),
            result=data.get("result", ""),
            conclusion=data.get("conclusion", ""),
            subsystem=subsystem,
            tags=tags,
        )
    elif kind == "session":
        path = summarise_session(
            summary=data.get("summary", text),
            subsystem=subsystem,
        )
    else:  # debug (default)
        kind = "debug"
        path = log_debug(
            title=data.get("title", "(untitled debug session)"),
            symptom=data.get("symptom", text[:200]),
            cause=data.get("cause", ""),
            fix=data.get("fix", ""),
            status=data.get("status", "open"),
            subsystem=subsystem,
            tags=tags,
        )

    return {"status": "written", "kind": kind, "path": path, "extracted": data}


def main() -> None:
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
