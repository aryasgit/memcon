"""
memory/retrieve.py
Hybrid retrieval: semantic (Qdrant) + entity (SQLite inverted index).

Why hybrid: the vector store excels at "this is roughly about that," but is
weak at "the note that mentions servo.cpp". The entity index complements it
with exact-string recall — together you get both fuzzy and precise.

Public entry points:
    query(text, top_k=5, subsystem=None)             — merged hybrid hits (default)
    query_semantic(text, top_k=5, subsystem=None)    — vector-only
    query_entities(text, top_k=10)                   — entity-only (returns docs)
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, search


# ──────────────────────────────────────────────────────────────────────────────
# Tunables (could move to config.yaml if we want them user-controllable)
# ──────────────────────────────────────────────────────────────────────────────

ENTITY_BOOST_FACTOR = 0.15   # per matched token, added to semantic score
MAX_ENTITY_BOOST    = 0.45   # cap on total entity boost (so a doc with 10
                             # matches doesn't drown out a strong semantic hit)
ENTITY_ONLY_FLOOR   = 0.30   # base score for docs found only via entities
                             # (no semantic hit) so they're rank-comparable


# ──────────────────────────────────────────────────────────────────────────────
# Semantic-only (the original behaviour)
# ──────────────────────────────────────────────────────────────────────────────

def query_semantic(text: str, top_k: int = 5, subsystem: str | None = None) -> list[dict]:
    """Pure semantic search via Qdrant. Same contract as the v1 query()."""
    ensure_collection()
    vec = embed([text])[0]
    return search(vec, top_k=top_k, subsystem=subsystem)


# ──────────────────────────────────────────────────────────────────────────────
# Entity-only
# ──────────────────────────────────────────────────────────────────────────────

def query_entities(text: str, top_k: int = 10) -> list[dict]:
    """Entity-index lookup. Returns dicts shaped like:
        {doc_name, path, score, matches: [{entity, kind, token}, ...]}
    """
    try:
        from memory.entity_index import lookup
        return lookup(text, limit=top_k)
    except Exception as e:
        print(f"[retrieve] entity lookup failed: {e}", file=sys.stderr)
        return []


# ──────────────────────────────────────────────────────────────────────────────
# Hybrid (default)
# ──────────────────────────────────────────────────────────────────────────────

def query(text: str, top_k: int = 5, subsystem: str | None = None) -> list[dict]:
    """Hybrid retrieval — merge semantic + entity hits and rerank.

    Output shape matches the legacy semantic-only contract so existing callers
    (memcon_query, memcon_ask, FastAPI ui.html) don't need to change:
        [{score, text, doc_name, subsystem, memory_type, tags, ...}, ...]

    Extra fields added on hybrid hits:
        - "via":         "semantic" | "entity" | "both"
        - "entity_hits": list of {entity, kind, token} when via != "semantic"
    """
    # Over-fetch so we have headroom for reranking. Cap at 25.
    fetch_k = min(max(top_k * 3, 8), 25)

    # 1) Semantic hits — full payload (text, subsystem, etc.). Degrade to
    #    entity-only if Qdrant is down/slow: a read must never crash or hang the
    #    caller just because the vector store is unavailable — the entity index
    #    alone still answers exact-string queries.
    try:
        sem_hits = query_semantic(text, top_k=fetch_k, subsystem=subsystem)
    except Exception as e:
        print(f"[retrieve] semantic search unavailable, entity-only: {e}", file=sys.stderr)
        sem_hits = []
    sem_by_doc: dict[str, dict] = {}
    for h in sem_hits:
        doc = h.get("doc_name")
        if not doc:
            continue
        # Keep the highest-scoring chunk per doc for the merged view, but stash
        # all chunks so the caller can still see multiple matches per doc.
        cur = sem_by_doc.get(doc)
        if cur is None or h.get("score", 0) > cur.get("score", 0):
            sem_by_doc[doc] = h

    # 2) Entity hits — doc_name-keyed, no chunk text
    ent_hits = query_entities(text, top_k=fetch_k)
    ent_by_doc = {h["doc_name"]: h for h in ent_hits}

    # 3) Merge — keep semantic payload, augment with entity boost
    merged: dict[str, dict] = {}

    for doc, h in sem_by_doc.items():
        merged[doc] = dict(h)
        merged[doc]["via"] = "semantic"
        merged[doc]["entity_hits"] = []

    for doc, h in ent_by_doc.items():
        boost = min(ENTITY_BOOST_FACTOR * h["score"], MAX_ENTITY_BOOST)
        if doc in merged:
            merged[doc]["score"] = round(merged[doc].get("score", 0) + boost, 4)
            merged[doc]["via"] = "both"
            merged[doc]["entity_hits"] = h["matches"]
        else:
            # Entity-only hit: synthesize a minimal payload so downstream callers
            # don't choke. Optionally pull the chunk text from Qdrant by doc_name
            # in a future revision.
            merged[doc] = {
                "score":       round(ENTITY_ONLY_FLOOR + boost, 4),
                "text":        f"(entity match: {', '.join(m['entity'] for m in h['matches'][:3])})",
                "doc_name":    doc,
                "subsystem":   "",
                "memory_type": "",
                "tags":        [],
                "via":         "entity",
                "entity_hits": h["matches"],
            }

    ranked = sorted(merged.values(), key=lambda r: r.get("score", 0), reverse=True)
    return ranked[:top_k]


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "servo overheating"
    results = query(q)
    for r in results:
        via = r.get("via", "semantic")
        marker = {"semantic": "S", "entity": "E", "both": "★"}.get(via, "?")
        print(f"\n[{marker} {r['score']}] {r['doc_name']} ({r.get('subsystem', '')})")
        if r.get("entity_hits"):
            print("  entities:", ", ".join(f"{m['entity']}({m['kind']})" for m in r['entity_hits'][:5]))
        print("  text:", r['text'][:200])
