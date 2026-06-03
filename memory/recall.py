"""
memory/recall.py
memcon_recall — the fused platter. The soul of Memcon.

For a given problem, return the past notes that are:
  • SIMILAR     — semantic match (the embedding substrate)
  • RECENT      — lifted by recency, because your approach evolves and the
                  latest attempt reflects current reality (temporal)
  • OUTCOME-LABELLED — resolved / open / failed, surfaced not suppressed, so a
                  recent FAILURE warns you and a recent FIX answers you

Not search. Recall. The ranking core (fuse / recency_factor / fused_score /
normalize_outcome) is pure and unit-tested offline. The full recall() wires it
to semantic retrieval + note parsing and needs the index up.
"""
from __future__ import annotations
import os, sys, re
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg


# ──────────────────────────────────────────────────────────────────────────────
# Tunables — the shape of "recall"
# ──────────────────────────────────────────────────────────────────────────────

RECENCY_HALF_LIFE_DAYS = 30.0   # a note this old keeps half its recency lift
RECENCY_WEIGHT = 0.6            # how much recency lifts a similar note (0 = pure semantic)
FETCH_MULTIPLIER = 4            # over-fetch candidates before fusing/trimming


# ──────────────────────────────────────────────────────────────────────────────
# Pure ranking core (offline-testable — no Qdrant, no LLM)
# ──────────────────────────────────────────────────────────────────────────────

def recency_factor(age_days: float, half_life: float = RECENCY_HALF_LIFE_DAYS) -> float:
    """1.0 for a note written today, 0.5 at `half_life` days, → 0 as it ages.
    Exponential decay — smooth, no cliffs."""
    if age_days is None or age_days <= 0:
        return 1.0
    return 0.5 ** (age_days / half_life)


def fused_score(similarity: float, age_days: float) -> float:
    """Semantic-DOMINANT, lifted by recency:  sim · (1 + w · recency).

    Semantic stays the primary signal (an old-but-very-similar note still beats
    a recent-but-unrelated one), while recency breaks ties and floats the latest
    attempt among comparable matches.
    """
    return float(similarity) * (1.0 + RECENCY_WEIGHT * recency_factor(age_days))


# Map the many status strings notes use → three meaningful outcomes.
_OUTCOME_MAP = {
    "fixed": "resolved", "resolved": "resolved", "closed": "resolved",
    "done": "resolved", "solved": "resolved", "verified": "resolved",
    "open": "open", "investigating": "open", "wip": "open", "in-progress": "open",
    "failed": "failed", "abandoned": "failed", "wontfix": "failed", "reverted": "failed",
}


def normalize_outcome(status: str | None) -> str:
    """Collapse a note's status into resolved | open | failed | unknown."""
    return _OUTCOME_MAP.get((status or "").strip().lower(), "unknown")


def fuse(candidates: list[dict], *, k: int = 5) -> list[dict]:
    """Rank candidates by fused score; attach recency + normalized outcome.

    PURE — given candidate dicts with at least {similarity, age_days, status},
    returns the top-k enriched + sorted. No I/O. This is the heart of recall.
    """
    ranked: list[dict] = []
    for c in candidates:
        sim = float(c.get("similarity", 0) or 0)
        age = float(c.get("age_days", 0) or 0)
        ranked.append({
            **c,
            "recency": round(recency_factor(age), 3),
            "score": round(fused_score(sim, age), 4),
            "outcome": normalize_outcome(c.get("status")),
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:k]


def summarize(problem: str, ranked: list[dict]) -> str:
    """One-line headline for the platter: how many times, how recent, what
    happened. The 'treat' served on top of the matches."""
    if not ranked:
        return f"No prior memory resembles: {problem!r}. This looks new."
    n = len(ranked)
    top = ranked[0]
    age = top.get("age_days", 0)
    when = "today" if age < 1 else f"{int(age)}d ago"
    out = top.get("outcome", "unknown")
    verb = {"resolved": "was fixed", "failed": "failed", "open": "is still open",
            "unknown": "was logged"}.get(out, "was logged")
    tried = (top.get("what_was_tried") or "").strip()
    tail = f" by: {tried[:120]}" if tried and out == "resolved" else ""
    plural = "time" if n == 1 else "times"
    return (f"You've hit something like this {n} {plural}. "
            f"Most recent ({when}) {verb}{tail}.")


# ──────────────────────────────────────────────────────────────────────────────
# Full recall — wires the core to retrieval + note parsing (needs the index up)
# ──────────────────────────────────────────────────────────────────────────────

def _note_meta(doc_name: str) -> dict:
    """Best-effort: find {doc_name}.md in the vault and pull age_days, status,
    title, and 'what was tried' (the resolution-ish section) + a short excerpt."""
    vault = Path(cfg('vault', 'path'))
    matches = list(vault.rglob(f"{doc_name}.md"))
    if not matches:
        return {}
    path = matches[0]
    try:
        text = path.read_text(errors="ignore")
        st = path.stat()
    except OSError:
        return {}

    # age from frontmatter `updated`/`created` if present, else file mtime
    age_days = None
    fm_match = re.search(r"^updated:\s*\"?([0-9T:\-Z]+)", text, re.MULTILINE) \
        or re.search(r"^created:\s*\"?([0-9T:\-Z]+)", text, re.MULTILINE)
    if fm_match:
        try:
            dt = datetime.fromisoformat(fm_match.group(1).replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400
        except ValueError:
            pass
    if age_days is None:
        age_days = (datetime.now(timezone.utc).timestamp() - st.st_mtime) / 86400

    # status: frontmatter field first, then fall back to an old-schema
    # `## Status` body section (pre-v3.1 notes store outcome there).
    status_m = re.search(r"^status:\s*\"?([A-Za-z\-]+)", text, re.MULTILINE)
    status = status_m.group(1) if status_m else ""
    if not status:
        body_status = re.search(r"^##\s+Status\s*\n+([A-Za-z\-]+)", text, re.MULTILINE)
        if body_status:
            status = body_status.group(1)
    title_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)

    # "what was tried" — the resolution-bearing section, by kind heuristic
    tried = ""
    for heading in ("Fix", "Decision", "Result", "Insight", "Conclusion", "Cause"):
        m = re.search(rf"^##\s+{heading}\s*\n+(.+?)(?=\n##|\Z)", text, re.DOTALL | re.MULTILINE)
        if m:
            tried = re.sub(r"\s+", " ", m.group(1)).strip()
            break

    return {
        "title": title_m.group(1).strip() if title_m else doc_name,
        "age_days": round(age_days, 2),
        "status": status,
        "what_was_tried": tried,
        "path": str(path),
    }


def recall(problem: str, k: int = 5) -> dict:
    """The fused platter for `problem`. Semantic search → enrich each hit with
    recency + outcome + what-was-tried → fuse → summarize.

    Returns: {problem, summary, matches:[{doc_name,title,similarity,age_days,
              recency,score,outcome,what_was_tried,excerpt}], count}.
    Best-effort: if retrieval fails (index down), returns an empty platter with
    a clear note rather than raising.
    """
    try:
        from memory.retrieve import query_semantic
        hits = query_semantic(problem, top_k=max(k * FETCH_MULTIPLIER, 8))
    except Exception as e:
        return {"problem": problem, "summary": f"(memory index unavailable: {e})",
                "matches": [], "count": 0}

    # one candidate per doc (keep best-scoring chunk), enriched with note meta
    best: dict[str, dict] = {}
    for h in hits:
        dn = h.get("doc_name")
        if not dn:
            continue
        sim = float(h.get("score", 0) or 0)
        if dn not in best or sim > best[dn]["similarity"]:
            best[dn] = {"doc_name": dn, "similarity": sim,
                        "excerpt": (h.get("text", "") or "")[:200]}
    candidates = []
    for dn, c in best.items():
        c.update(_note_meta(dn))
        candidates.append(c)

    ranked = fuse(candidates, k=k)
    return {
        "problem": problem,
        "summary": summarize(problem, ranked),
        "matches": ranked,
        "count": len(ranked),
    }
