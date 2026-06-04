import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from ingestion.chunker import chunk_file
from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, upsert_chunks, delete_by_doc

try:
    from config import cfg
except Exception:
    cfg = None

# Files that must NEVER enter the searchable index — mirrors the .gitignore
# private-doc markers. A note named *PRIVATE* / *STRATEGY* / *ROADMAP* /
# *_REFERENCE is treated as private and skipped by EVERY ingest path (the
# walker, the watcher, and writer re-ingests), so a private doc on disk can
# never leak into memcon_query / memcon_recall results.
_PRIVATE_RE = re.compile(r"(PRIVATE|STRATEGY|ROADMAP|_REFERENCE)", re.IGNORECASE)


def _is_excluded(filepath: str) -> bool:
    name = os.path.basename(filepath)
    if _PRIVATE_RE.search(name):
        return True
    skip = set()
    if cfg is not None:
        try:
            skip = set(cfg('vault', 'skip_dirs') or [])
        except Exception:
            skip = set()
    skip |= {".memcon", "_templates"}
    return any(part in skip for part in Path(filepath).parts)


def ingest_file(filepath: str) -> int:
    if _is_excluded(filepath):
        print(f"[ingest] skipped (private/excluded): {filepath}", file=sys.stderr)
        return 0
    ensure_collection()
    chunks = chunk_file(filepath)
    if not chunks:
        print(f"[ingest] No chunks found in {filepath}", file=sys.stderr)
        return 0
    texts = [c["text"] for c in chunks]
    vectors = embed(texts)
    # Clean replace: drop any existing chunks for this doc BEFORE adding the new
    # ones, so a re-ingest of an edited/shrunk note never leaves stale orphan
    # chunks (which is how an emptied-then-refilled note stayed unsearchable).
    doc = chunks[0].get("doc_name")
    if doc:
        delete_by_doc(doc)
    n = upsert_chunks(chunks, vectors)
    print(f"[ingest] {filepath} → {n} chunks added", file=sys.stderr)
    return n


def reindex_vault() -> dict:
    """Re-ingest every note in the vault so the search index matches what's
    actually on disk. Heals drift: notes written while Qdrant was down, edits
    made directly in Obsidian, the data-loss-then-refill case. Each file is a
    clean replace, so no orphans remain.

    Returns {files, chunks}.
    """
    if cfg is None:
        return {"files": 0, "chunks": 0}
    vault = Path(cfg('vault', 'path'))
    nf = nc = 0
    for p in vault.rglob("*.md"):
        try:
            rel = p.relative_to(vault)
        except ValueError:
            continue
        if any(part.startswith('_backup') or part == '.memcon' for part in rel.parts):
            continue
        try:
            added = ingest_file(str(p))   # ingest_file applies private/skip filters
            if added:
                nf += 1
                nc += added
        except Exception as e:
            print(f"[reindex] {p}: {e}", file=sys.stderr)
    return {"files": nf, "chunks": nc}
