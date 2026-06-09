"""
recall() self-healing — locks the phantom-recall fix end-to-end: an entity hit
whose note no longer exists on disk must be DROPPED (not surfaced as a fresh
"today" result), while a hit whose note DOES exist must still surface.
Retrieval is monkeypatched, so no Qdrant is needed.
"""
import pytest
from memory import recall as recall_mod
from memory import retrieve as retrieve_mod
from memory import entity_index as ei


def test_recall_drops_candidate_with_no_file_on_disk(monkeypatch, vault):
    monkeypatch.setattr(retrieve_mod, "query_semantic", lambda *a, **k: [])
    monkeypatch.setattr(ei, "lookup", lambda *a, **k: [{"doc_name": "ghost-doc"}])

    out = recall_mod.recall("ghost-doc", k=5)
    names = [m["doc_name"] for m in out["matches"]]
    assert "ghost-doc" not in names          # the phantom is dropped
    assert out["count"] == 0
    assert "Nothing in memory" in out["summary"]


def test_recall_surfaces_candidate_that_exists_on_disk(monkeypatch, vault):
    note = vault / "debugging" / "real-doc.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("---\nstatus: resolved\n---\n# Real\n## Fix\nbumped the pool\n")

    monkeypatch.setattr(retrieve_mod, "query_semantic", lambda *a, **k: [])
    monkeypatch.setattr(ei, "lookup", lambda *a, **k: [{"doc_name": "real-doc"}])

    out = recall_mod.recall("real-doc", k=5)
    names = [m["doc_name"] for m in out["matches"]]
    assert "real-doc" in names                # a real note is NOT over-dropped
    assert out["count"] == 1

    note.unlink()  # clean up so the shared temp vault doesn't leak between tests
