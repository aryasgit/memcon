"""
memory/capture.py
memcon_capture's fast, timeout-proof write path.

WHY THIS EXISTS
The multi-pass extractor (classify → structure → entities → optional critique)
on a long input with a local model can take minutes — far past an MCP client's
~60s tool-call timeout (the "Tool result could not be submitted / request
expired" failure). Running it synchronously inside the tool call is what timed
capture out. So capture is split:

  SYNCHRONOUS (fast, bounded): pick the kind (a single short classify with a
    hard timeout + heuristic fallback), write a PROVISIONAL note immediately —
    raw text preserved under ## Context, a first-line TL;DR — and RETURN the
    path. The tool call never blocks on the slow structure pass, so it can't
    time out.

  ASYNCHRONOUS (background daemon): run the full extraction and OVERWRITE the
    note in place with structured sections + entities + the adaptive template.
    If anything fails, the provisional note (already valid, with the raw text)
    simply stands.

The note's path is locked at the synchronous step (kind + first-line title), so
the background pass refines content WITHOUT moving the file.
"""
from __future__ import annotations
import os, sys, re, threading
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg
from memory.templates import ALL_KINDS


# How long the synchronous classify may take before we fall back to a heuristic.
SYNC_CLASSIFY_TIMEOUT_S = 12


# ──────────────────────────────────────────────────────────────────────────────
# Fast, LLM-free helpers
# ──────────────────────────────────────────────────────────────────────────────

def _first_line_title(text: str) -> str:
    """A reasonable title from the first non-trivial line of the input."""
    for line in (text or "").splitlines():
        s = line.strip().lstrip("#").strip()
        # skip obvious labels like "Session:" prefixes — keep the substance
        if len(s) >= 8:
            s = re.sub(r"\s+", " ", s)
            return s[:70].rstrip(" .:-")
    return "Captured note"


_KIND_HINTS = [
    ("decision",     ("decided", "chose", "we picked", "going with", "trade-off", "tradeoff")),
    ("experiment",   ("hypothesis", "experiment", "we tried", "measured", "benchmark", "tested whether")),
    ("breakthrough", ("breakthrough", "finally figured", "aha", "unlocked", "key insight")),
    ("meeting",      ("meeting", "sync", "attendees", "we discussed", "standup")),
    ("reference",    ("api reference", "docs say", "spec:", "according to the docs", "datasheet")),
    ("concept",      ("is defined as", "the concept of", "what is ", "mental model")),
    ("debug",        ("bug", "error", "traceback", "crash", "overheat", "failed", "fix", "symptom", "broke")),
    ("session",      ("session", "today we", "this session", "worked on", "progress", "wrapped up")),
]


def _heuristic_kind(text: str, hint: str) -> str:
    """Instant kind guess (no LLM). Used as the fallback when the quick classify
    is slow or unavailable."""
    if hint and hint != "auto" and hint in ALL_KINDS:
        return hint
    low = (text or "").lower()
    for kind, needles in _KIND_HINTS:
        if any(n in low for n in needles):
            return kind
    return "session"  # the most common freeform-capture case


def _quick_classify(text: str, hint: str) -> str:
    """Decide the note kind with a HARD time budget. Tries one short LLM
    classify on a capped slice of the input; if it doesn't finish within
    SYNC_CLASSIFY_TIMEOUT_S (slow/no Ollama), falls back to the heuristic."""
    if hint and hint != "auto" and hint in ALL_KINDS:
        return hint

    box: dict = {}

    def run():
        try:
            from memory.extractor import classify_type
            k, _ = classify_type(text[:1500])
            if k in ALL_KINDS:
                box["kind"] = k
        except Exception:
            pass

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout=SYNC_CLASSIFY_TIMEOUT_S)
    return box.get("kind") or _heuristic_kind(text, hint)


# ──────────────────────────────────────────────────────────────────────────────
# Background: full extraction → overwrite the provisional note
# ──────────────────────────────────────────────────────────────────────────────

def _enrich_in_background(path: str, text: str, kind: str, title: str,
                          run_critique: bool) -> None:
    """Run the full multi-pass extraction and replace the provisional note with
    its structured version, IN PLACE (same path). All best-effort: on any
    failure the provisional note stands."""
    try:
        from memory.extractor import extract
        from memory.writer import log_universal

        try:
            subs = list(cfg('subsystems') or [])
        except Exception:
            subs = []

        # Force the kind we already committed to (locks the file location).
        result = extract(text, hint=kind, run_critique=run_critique,
                         valid_subsystems=subs or None)

        subsystem = result.get("subsystem", "unknown")
        if subs and subsystem not in subs:
            subsystem = "unknown"

        fields = dict(result.get("fields") or {})

        # CRITICAL: always preserve the full raw text. This is the source of
        # truth — structure is derived from it. FORCE it (the extractor can
        # return an empty context_raw, which must NEVER be allowed to wipe the
        # original). setdefault was the data-loss bug.
        fields["context_raw"] = text[:16000]

        # GUARD: if the extraction produced essentially nothing (model hiccup,
        # empty/unparseable JSON), do NOT overwrite — the provisional note
        # already holds the full raw text. Overwriting with an empty structure
        # would destroy content. Keep the provisional instead.
        structured = {
            k: v for k, v in fields.items()
            if k not in ("context_raw", "tldr") and isinstance(v, str) and v.strip()
        }
        if not structured:
            print("[capture] extraction yielded no structure — keeping provisional "
                  "note (full raw text already preserved)", file=sys.stderr)
            return

        # Drop empty entity categories so an empty/garbage extraction doesn't
        # write phantom entities.
        entities = {k: v for k, v in (result.get("entities") or {}).items() if v}

        # Overwrite the provisional with the structured note. Same kind + title
        # → same slug → same file. The forced context_raw guarantees the raw
        # text survives the overwrite no matter what.
        log_universal(
            kind=kind,
            title=title,
            fields=fields,
            subsystem=subsystem,
            tags=result.get("tags", []),
            status=result.get("status", ""),
            confidence=result.get("confidence", ""),
            entities=entities,
            overwrite=True,
            enrich=True,
        )
    except Exception as e:
        print(f"[capture] background structuring failed (provisional note kept): {e}",
              file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# Public entry
# ──────────────────────────────────────────────────────────────────────────────

def capture(text: str, hint: str = "auto", run_critique: bool = False) -> dict:
    """Fast capture: write a provisional note now, structure it in the
    background. Returns immediately — never blocks on the slow extraction."""
    from datetime import datetime
    from memory.templates import render, FOLDER_FOR, _slug

    # Pick the kind with the INSTANT heuristic — NO LLM on the synchronous path,
    # so the write returns in milliseconds even on a cold server. The background
    # daemon still runs the full multi-pass extraction (structure + entities).
    kind = _heuristic_kind(text, hint)
    title = _first_line_title(text)
    slug = _slug(title)
    note_id = f"{datetime.now().strftime('%Y-%m-%d')}_{slug}"

    # Provisional note — written DIRECTLY to disk: no Qdrant query, no embedder,
    # no ingest, NO LLM. The synchronous path is just an instant heuristic
    # classify + a file write, so it returns in milliseconds even on a cold
    # server. The raw text is preserved under ## Context.
    content = render(
        kind=kind,
        title=title,
        fields={"tldr": title, "context_raw": text[:16000]},
        note_id=note_id,
        subsystem="unknown",
    )
    vault = Path(cfg('vault', 'path'))
    target = vault / FOLDER_FOR.get(kind, "debugging")
    target.mkdir(parents=True, exist_ok=True)
    # Filename = date-prefixed note_id (matches the frontmatter id and the
    # background structuring pass, which recomputes the same id → overwrites this
    # exact file rather than orphaning it).
    path = str(target / f"{note_id}.md")
    from memory.fsutil import atomic_write_text, note_lock
    with note_lock(path):
        atomic_write_text(path, content)

    # ALWAYS index the raw note immediately (on the bounded worker) so it is
    # genuinely searchable right away — independent of any local LLM. (Regression
    # fix: in Claude mode this used to never enqueue an ingest, so captured notes
    # sat on disk INVISIBLE to recall until the next startup reindex.)
    from memory.worker import submit
    from ingestion.ingest import ingest_file
    submit(ingest_file, path)

    # Background structuring needs a LOCAL LLM, which is OPTIONAL. When one is
    # present it restructures the note and re-indexes it; otherwise the raw note
    # (already indexed above) stands and the assistant can add structure via
    # memcon_write_*.
    from memory.llm import is_available
    llm_on = is_available()
    if llm_on:
        submit(_enrich_in_background, path, text, kind, title, run_critique)
        note = ("Saved instantly — raw text already searchable. A local LLM is "
                "structuring it into sections + entities in the background; no need "
                "to wait or re-call.")
    else:
        wk = kind if kind in ALL_KINDS else "<kind>"
        note = ("Saved instantly — raw text preserved and already searchable. No "
                "local LLM is configured, so for a richer structured note, extract "
                f"the fields yourself and call memcon_write_{wk}.")

    return {
        "status": "saved",
        "kind": kind,
        "path": path,
        "structured": llm_on,
        "note": note,
    }
