"""
Reliability regression suite for memcon — locks in the June-2026 hardening so the
hang / data-loss / thrash incident can't silently come back.

Runs against the LIVE embedder + a throwaway Qdrant collection (see conftest).
NO Ollama is required — every test exercises the synchronous / library paths or
mocks the LLM, which also proves the "lean / Ollama-optional" direction works.
"""
import os
import sys
import gc
import json
import time
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import pytest
import urllib.request


def _qdrant_up() -> bool:
    try:
        urllib.request.urlopen("http://localhost:6333/healthz", timeout=2)
        return True
    except Exception:
        return False


requires_qdrant = pytest.mark.skipif(not _qdrant_up(), reason="Qdrant not running on :6333")


# ── Theme B — atomic writes ───────────────────────────────────────────────
def test_atomic_write_is_complete(tmp_path):
    from memory.fsutil import atomic_write_text
    p = tmp_path / "note.md"
    atomic_write_text(p, "hello\nworld\n")
    assert p.read_text() == "hello\nworld\n"
    assert not list(tmp_path.glob(".*tmp*")), "temp file left behind"


def test_note_lock_acquires_and_releases(tmp_path):
    from memory.fsutil import note_lock
    with note_lock(tmp_path / "x.md"):
        pass
    # second acquisition must succeed (lock was released)
    with note_lock(tmp_path / "x.md"):
        pass


# ── Theme A / E — one bounded worker pool ─────────────────────────────────
def test_worker_runs_jobs_and_caps_threads():
    from memory import worker
    ev = threading.Event()
    out = []
    worker.submit(lambda: (out.append(1), ev.set()))
    assert ev.wait(5), "worker never ran the job"
    assert out == [1]
    time.sleep(0.1)
    bg = [t for t in threading.enumerate() if t.name.startswith("memcon-bg")]
    assert 1 <= len(bg) <= int(os.getenv("MEMCON_BG_WORKERS", "2")), f"thread cap broken: {len(bg)}"


# ── Theme F — SQLite connection hygiene ───────────────────────────────────
def test_entity_index_no_connection_leak():
    from memory import entity_index
    entity_index.index_note(
        doc_name="leaktest",
        entities={"files": ["servo.cpp"], "symbols": ["set_torque"]},
        path="/x/leaktest.md",
    )
    base = sum(1 for o in gc.get_objects() if isinstance(o, sqlite3.Connection))
    for _ in range(40):
        entity_index.lookup("servo.cpp")
        entity_index.stats()
    after = sum(1 for o in gc.get_objects() if isinstance(o, sqlite3.Connection))
    assert after <= base + 1, f"SQLite connection leak: {base} -> {after}"
    hits = entity_index.lookup("servo.cpp")
    assert any(h["doc_name"] == "leaktest" for h in hits), "entity lookup broken"


# ── capture kind heuristic (LLM-FREE — lean-ready) ────────────────────────
def test_capture_heuristic_kind_is_llm_free():
    from memory.capture import _heuristic_kind
    assert _heuristic_kind("we decided to use the bus servo", "auto") == "decision"
    assert _heuristic_kind("traceback: error, the board crashed", "auto") == "debug"
    assert _heuristic_kind("just some musings today", "auto") == "session"
    assert _heuristic_kind("anything here", "concept") == "concept"  # explicit hint wins


def test_slug_is_filesystem_safe():
    from memory.templates import _slug
    s = _slug("RR Servo: Overheats!! (backward gait)")
    assert s and "/" not in s and " " not in s and s == s.lower()


# ── Theme G — hybrid retrieval degrades without the vector store ──────────
def test_hybrid_query_degrades_when_semantic_fails(monkeypatch):
    import memory.retrieve as r
    monkeypatch.setattr(r, "query_semantic", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("qdrant down")))
    out = r.query("anything at all")
    assert isinstance(out, list)  # entity-only fallback, never raises


# ── Theme G — get_stats distinguishes ok vs outage ────────────────────────
@requires_qdrant
def test_get_stats_reports_status_ok():
    from memory.qdrant_store import get_stats, ensure_collection
    ensure_collection()
    s = get_stats()
    assert s.get("status") == "ok"
    assert isinstance(s.get("total_chunks"), int)


# ── Theme D — ingest_file is idempotent (the amplification killer) ─────────
@requires_qdrant
def test_ingest_file_idempotent(tmp_path):
    from ingestion.ingest import ingest_file, _manifest_read, _manifest_path, _atomic_write_text
    from memory.qdrant_store import delete_by_doc
    f = tmp_path / "idem_note.md"
    f.write_text("# Idem\n\nbody about servo brownout and power rails")
    try:
        n1 = ingest_file(str(f))
        n2 = ingest_file(str(f))                       # unchanged -> SKIP
        assert n1 > 0 and n2 == 0, f"not idempotent: {n1},{n2}"
        os.utime(f, (time.time() + 10, time.time() + 10))
        n3 = ingest_file(str(f))                       # changed -> ingest
        n4 = ingest_file(str(f), force=True)           # force -> ingest
        assert n3 > 0 and n4 > 0
    finally:
        delete_by_doc("idem_note")
        m = _manifest_read(); m.pop("idem_note", None)
        _atomic_write_text(_manifest_path(), json.dumps(m))


# ── Theme D — watcher debounces and never dies ────────────────────────────
def test_watcher_debounces_and_survives_errors(tmp_path):
    import ingestion.watcher as w

    seen = []
    w.ingest_file = lambda p: seen.append(p)
    di = w.DebouncedIngestor(debounce=0.3)
    p1 = str(tmp_path / "a.md"); open(p1, "w").write("x")
    for _ in range(8):
        di.submit(p1)
    time.sleep(0.9)
    di.stop()
    assert seen.count(p1) == 1, f"debounce failed: {seen}"

    seen2 = []
    def boom(p):
        seen2.append(p)
        raise RuntimeError("simulated qdrant blip")
    w.ingest_file = boom
    di2 = w.DebouncedIngestor(debounce=0.2)
    pe = str(tmp_path / "e.md"); open(pe, "w").write("x")
    pok = str(tmp_path / "o.md"); open(pok, "w").write("y")
    di2.submit(pe); time.sleep(0.5)
    di2.submit(pok); time.sleep(0.5)
    di2.stop()
    assert pe in seen2 and pok in seen2, f"worker died after an error: {seen2}"


# ── Theme A + B + J — write is instant, atomic, date-prefixed, searchable ─
@requires_qdrant
def test_write_is_instant_atomic_and_searchable():
    from ingestion.embedder import embed
    from memory.writer import log_decision
    from memory import worker
    from memory.retrieve import query
    from memory.qdrant_store import delete_by_doc
    from memory.entity_index import clear_doc
    from ingestion.ingest import _manifest_read, _manifest_path, _atomic_write_text

    embed(["warm"])  # warm the model so timing reflects steady state
    t0 = time.time()
    p = log_decision(
        "Pytest unique alpha note",
        "Run every deferred write operation on a single bounded background worker pool "
        "instead of spawning one daemon thread per write.",
        "The old per-write thread plus git subprocess fan-out thrashed the sixteen gigabyte "
        "machine during the bulk import incident, so we cap background concurrency.",
        "version_control", ["pytest"],
    )
    dt = time.time() - t0
    stem = Path(p).stem
    try:
        assert dt < 2.0, f"write not instant ({dt:.2f}s) — heavy work not deferred"
        assert os.path.exists(p), "note not durably on disk when the call returned"
        assert stem.startswith(datetime.now().strftime("%Y-%m-%d") + "_"), f"not date-prefixed: {stem}"
        body = Path(p).read_text()
        assert body.startswith("---") and "bounded background worker pool" in body, "note looks incomplete"
        worker._q.join()
        time.sleep(0.3)
        hits = query("bounded background worker pool for deferred writes", top_k=5)
        assert any(h.get("doc_name") == stem for h in hits), "not searchable after the worker finalized"
    finally:
        if os.path.exists(p):
            os.remove(p)
        for _ in range(2):
            delete_by_doc(stem); time.sleep(0.2)
        clear_doc(stem)
        m = _manifest_read(); m.pop(stem, None)
        _atomic_write_text(_manifest_path(), json.dumps(m))


# ── capture: instant provisional, raw preserved, NO Ollama (lean-ready) ───
def test_capture_provisional_is_llm_free(monkeypatch):
    import memory.worker as worker
    # Stub the worker so the background (Ollama) structuring never runs — proving
    # the synchronous capture path needs no local LLM.
    monkeypatch.setattr(worker, "submit", lambda *a, **k: True)
    from memory.capture import capture
    raw = "We browned out the RR servo during backward gait, then bumped the PSU to 5A. Test."
    res = capture(raw, hint="debug")
    p = res["path"]
    stem = Path(p).stem
    try:
        assert res["status"] == "saved" and res["kind"] == "debug"
        assert stem.startswith(datetime.now().strftime("%Y-%m-%d") + "_")
        assert "browned out the RR servo" in Path(p).read_text(), "raw text not preserved"
    finally:
        if os.path.exists(p):
            os.remove(p)


# ── MCP server surface ────────────────────────────────────────────────────
def test_mcp_server_registers_18_tools():
    import asyncio
    import memcon_mcp.server as s
    tools = asyncio.run(s.mcp.list_tools())
    assert len(tools) == 18, f"expected 18 tools, got {len(tools)}"


def test_mcp_llm_client_has_timeout():
    import memcon_mcp.server as s
    assert getattr(s._get_llm(), "timeout", None), "LLM client missing a timeout"


def test_mcp_autosync_is_nonblocking():
    import memcon_mcp.server as s
    t0 = time.time()
    s._autosync(); s._autosync()
    assert time.time() - t0 < 0.5, "autosync is blocking the read path"


# ── Lean / Ollama-optional ────────────────────────────────────────────────
def test_llm_enabled_by_default():
    from memory import llm
    # Default on, so a present Ollama auto-works; the probe handles 'not installed'.
    assert llm.enabled() is True


def test_capture_lean_keeps_raw_note_without_llm(monkeypatch):
    import memory.llm as llm
    monkeypatch.setattr(llm, "is_available", lambda *a, **k: False)
    from memory.capture import capture
    res = capture("Lean note: the IMU drifted during the turn; recalibrated the bias offset.", hint="debug")
    p = res["path"]
    try:
        assert res["structured"] is False, "must not claim background structuring without a local LLM"
        assert "memcon_write_debug" in res["note"], "should steer the assistant to the LLM-free write tool"
        assert "IMU drifted" in open(p).read(), "raw text must be preserved"
    finally:
        if os.path.exists(p):
            os.remove(p)


def test_extract_skips_cleanly_without_llm(monkeypatch):
    import memory.llm as llm
    monkeypatch.setattr(llm, "is_available", lambda *a, **k: False)
    from memory.extractor import extract
    out = extract("anything at all here", hint="debug")
    assert out["meta"].get("llm") == "unavailable"
    assert out["fields"] == {} and out["entities"] == {}, "no LLM should mean no fabricated structure"


def test_api_ask_degrades_to_chunks_without_llm(monkeypatch):
    import memory.llm as llm
    monkeypatch.setattr(llm, "is_available", lambda *a, **k: False)
    import api.main as A
    monkeypatch.setattr(A, "query", lambda *a, **k: [
        {"doc_name": "d1", "text": "t", "subsystem": "", "memory_type": "", "score": 0.9}
    ])
    out = A.ask(A.AskRequest(question="anything"))
    assert out["answer"] is None and out["raw_chunks"], "lean ask must return chunks for the caller"
    assert "No local LLM" in out["note"]
