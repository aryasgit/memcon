import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from ingestion.chunker import chunk_file
from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, upsert_chunks

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
    n = upsert_chunks(chunks, vectors)
    print(f"[ingest] {filepath} → {n} chunks added", file=sys.stderr)
    return n
