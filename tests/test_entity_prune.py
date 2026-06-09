"""
Entity-index pruning — locks the fix for the phantom-recall bug: a deleted or
edited note must not leave stale exact-entity rows. SQLite-only, no Qdrant.
"""
import pytest
from memory import entity_index


@pytest.fixture(autouse=True)
def _clean(vault):
    for d in ("prune-doc", "edit-doc"):
        entity_index.clear_doc(d)
    yield
    for d in ("prune-doc", "edit-doc"):
        entity_index.clear_doc(d)


def _docs(hits):
    return {h["doc_name"] for h in hits}


def test_clear_doc_removes_all_entities_for_doc():
    entity_index.index_note(
        doc_name="prune-doc",
        entities={"files": ["jwt_helper.ts"], "errors": ["EADDRINUSE"]},
        path="/x/prune-doc.md",
    )
    assert "prune-doc" in _docs(entity_index.lookup("EADDRINUSE"))

    removed = entity_index.clear_doc("prune-doc")
    assert removed >= 1
    # gone from every token it used to match
    assert "prune-doc" not in _docs(entity_index.lookup("EADDRINUSE"))
    assert "prune-doc" not in _docs(entity_index.lookup("jwt_helper.ts"))


def test_index_note_replace_drops_removed_entities():
    entity_index.index_note(
        doc_name="edit-doc",
        entities={"files": ["old_module.py", "kept_module.py"]},
        path="/x/edit-doc.md", replace=True,
    )
    assert "edit-doc" in _docs(entity_index.lookup("old_module.py"))

    # Note edited: old_module removed. A clean replace must drop the stale entity
    # so recall can never surface it on a now-deleted symbol.
    entity_index.index_note(
        doc_name="edit-doc",
        entities={"files": ["kept_module.py"]},
        path="/x/edit-doc.md", replace=True,
    )
    assert "edit-doc" not in _docs(entity_index.lookup("old_module.py"))
    assert "edit-doc" in _docs(entity_index.lookup("kept_module.py"))
