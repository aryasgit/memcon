"""
End-to-end search verification on the sample dataset + a concurrency stress test.
Runs in the isolated env from conftest (throwaway vault + test Qdrant collection).
"""
import os
import time
import json
import urllib.request
from pathlib import Path

import pytest


def _qdrant_up() -> bool:
    try:
        urllib.request.urlopen("http://localhost:6333/healthz", timeout=2)
        return True
    except Exception:
        return False


requires_qdrant = pytest.mark.skipif(not _qdrant_up(), reason="Qdrant not running on :6333")


def _tool(s, name, **kw):
    fn = getattr(s, name)
    fn = getattr(fn, "fn", fn)   # unwrap a FastMCP FunctionTool if present
    return fn(**kw)


@requires_qdrant
def test_sample_data_semantic_temporal_entity_recall():
    from ingestion.embedder import embed
    embed(["warm"])
    import scripts.load_sample_data as sd
    from memory.retrieve import query
    from memory.recall import recall
    import memcon_mcp.server as s

    try:
        paths = sd.load(reindex=True)
        assert len(paths) >= 12

        # SEMANTIC — query shares NO title keywords with the deadlock note
        docs = [h.get("doc_name", "") for h in query("two database transactions locking rows in a cycle under load", top_k=5)]
        assert any("deadlock" in d for d in docs), f"semantic miss (deadlock): {docs}"

        # SEMANTIC #2 — the redis/latency cluster, described differently than the title
        docs = [h.get("doc_name", "") for h in query("ran out of cache connections during a traffic spike", top_k=5)]
        assert any("redis" in d or "pool" in d for d in docs), f"semantic miss (redis): {docs}"

        # ENTITY / exact-ish — JWT
        docs = [h.get("doc_name", "") for h in query("JWT", top_k=5)]
        assert any("jwt" in d for d in docs), f"entity miss (JWT): {docs}"

        # REFERENCE-kind note must be searchable. Regression guard: a "...quick
        # reference" filename used to trip the private-doc filter (IGNORECASE
        # _REFERENCE) and get silently excluded from the index.
        docs = [h.get("doc_name", "") for h in query("postgres advisory locks for application mutual exclusion", top_k=5)]
        assert any("advisory_locks" in d for d in docs), f"reference note not indexed (private-filter false positive): {docs}"

        # RECALL — fused platter with outcome labels
        r = recall("redis is slow again under burst traffic", k=5)
        rdocs = [m["doc_name"] for m in r["matches"]]
        assert any("redis" in d for d in rdocs), f"recall miss: {rdocs}"
        assert all("outcome" in m for m in r["matches"]), "recall matches missing outcome labels"

        # TEMPORAL — last 7 days includes recent notes, excludes the 14/16-day-old ones
        tl = _tool(s, "memcon_timeline", since_days=7, limit=50)
        names = [n["name"] for n in tl["notes"]]
        assert tl["count"] >= 4, f"temporal(7d) returned too few: {tl['count']}"
        assert any("session" in n for n in names), "temporal(7d): today's session missing"
        assert not any("advisory_locks" in n or "n_1_queries" in n for n in names), \
            f"temporal(7d): a >7-day note leaked into the window: {names}"

        # TEMPORAL #2 — a 30-day window DOES include the 14-day reference note
        names30 = [n["name"] for n in _tool(s, "memcon_timeline", since_days=30, limit=50)["notes"]]
        assert any("advisory_locks" in n for n in names30), "temporal(30d): old reference missing"
    finally:
        sd.clean()


# Distinct codenames → distinct embeddings → reliable per-note retrieval.
_CODENAMES = ["zephyr", "quartz", "mango", "cobalt", "willow", "tungsten", "saffron",
              "indigo", "basalt", "cedar", "onyx", "marlin", "peridot", "juniper", "sable", "flint"]


@requires_qdrant
def test_concurrent_writes_never_lose_data():
    import concurrent.futures
    from memory.writer import log_decision
    from memory import worker
    from memory.retrieve import query
    from memory.qdrant_store import delete_by_doc
    from memory.entity_index import clear_doc
    import ingestion.ingest as ing
    from ingestion.embedder import embed
    embed(["warm"])

    N = len(_CODENAMES)

    def w(i):
        cn = _CODENAMES[i]
        return log_decision(
            f"Stresstest decision codename {cn}",
            f"Adopt the {cn} approach for the widget pipeline so it scales under load.",
            f"Because {cn} avoids the contention measured in the {cn} trial.",
            "version_control", ["stresstest"],
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        paths = list(ex.map(w, range(N)))

    try:
        # Atomic writes: every note is durably on disk the instant its call returned.
        assert all(os.path.exists(p) for p in paths), "a concurrent write was lost from disk"
        assert len(set(paths)) == N, "two concurrent writes collided onto the same file"
        # Drain the bounded worker, then every note must be searchable.
        worker._q.join()
        time.sleep(1.0)
        missing = []
        for i, p in enumerate(paths):
            stem = Path(p).stem
            hits = query(f"{_CODENAMES[i]} approach widget pipeline", top_k=5)
            if not any(h.get("doc_name") == stem for h in hits):
                missing.append(_CODENAMES[i])
        assert not missing, f"{len(missing)}/{N} concurrent writes not searchable: {missing}"
    finally:
        for p in paths:
            stem = Path(p).stem
            if os.path.exists(p):
                os.remove(p)
            delete_by_doc(stem)
            clear_doc(stem)
            m = ing._manifest_read()
            m.pop(stem, None)
            ing._atomic_write_text(ing._manifest_path(), json.dumps(m))
