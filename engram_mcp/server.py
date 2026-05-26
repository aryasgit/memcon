"""
Engram MCP Server — exposes Engram memory as Model Context Protocol tools.

Lets Claude (Desktop, Cursor, Code) auto-query relevant past work before
answering, and auto-write debug sessions / decisions / experiments after
solving a problem. No HTTP, no manual notes — Engram becomes a persistent
backend brain for any LLM session.

Run as stdio server (default for Claude Desktop / Cursor):
    python3 -m engram_mcp.server

Tools exposed:
    engram_query           — semantic search, returns relevant chunks
    engram_ask             — LLM-grounded answer (uses Engram's local LLM)
    engram_write_debug     — save a debugging session note
    engram_write_decision  — save an engineering decision
    engram_write_experiment — save an experiment result
    engram_session_summary — save an end-of-session summary
    engram_update_note     — append findings to an existing note
    engram_stats           — chunk count, project info
    engram_subsystems      — list configured subsystems
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

mcp = FastMCP("engram")


@mcp.tool()
def engram_query(query: str, top_k: int = 5, subsystem: str | None = None) -> dict:
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
def engram_ask(question: str, top_k: int = 5, subsystem: str | None = None) -> dict:
    """
    Ask Engram's local LLM a question grounded in the project's memory.
    Use this when you want a self-contained answer with sources. Prefer
    engram_query when you (the calling LLM) want raw context to reason over.

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
def engram_write_debug(
    title: str,
    symptom: str,
    cause: str = "",
    fix: str = "",
    status: str = "open",
    subsystem: str = "unknown",
    tags: list[str] | None = None,
) -> dict:
    """
    Save a debugging session to memory. Call this after diagnosing or solving
    a problem so the next session (yours or someone else's) can find it.

    Args:
        title: Short descriptive title (e.g. "RR Wrist Overheating").
        symptom: What was observed.
        cause: Root cause if known.
        fix: What resolved it (or current workaround).
        status: "open" | "fixed" | "investigating".
        subsystem: One of the configured subsystems (engram_subsystems).
        tags: Optional list of free-form tags.
    """
    path = log_debug(title, symptom, cause, fix, status, subsystem, tags or [])
    return {"status": "written", "path": path}


@mcp.tool()
def engram_write_decision(
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
def engram_write_experiment(
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
def engram_session_summary(summary: str, subsystem: str = "unknown") -> dict:
    """
    Save an end-of-session summary capturing what was worked on, broken, fixed,
    or decided. Call this near the end of a working session.
    """
    path = summarise_session(summary, subsystem)
    return {"status": "written", "path": path}


@mcp.tool()
def engram_update_note(filepath: str, content: str) -> dict:
    """
    Append new findings to an existing note (e.g. when a previously-open debug
    session gets resolved). `filepath` is the path returned by an earlier
    engram_write_* call, or a doc_name visible in engram_query results.
    """
    path = update_note(filepath, content)
    return {"status": "updated", "path": path}


@mcp.tool()
def engram_stats() -> dict:
    """
    Project info — chunk count, collection name, project name. Cheap diagnostic.
    """
    s = get_stats()
    s["project"] = cfg('project', 'name')
    s["domain"] = cfg('project', 'domain')
    return s


@mcp.tool()
def engram_subsystems() -> dict:
    """
    List the configured subsystems for this project. Use as a guide when
    deciding which `subsystem` value to pass to write/query tools.
    """
    return {
        "subsystems": cfg('subsystems'),
        "memory_types": cfg('memory_types'),
    }


def main() -> None:
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
