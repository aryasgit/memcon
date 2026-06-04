import sys, os, re, json, threading
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


# ──────────────────────────────────────────────────────────────────────────────
# Incremental auto-sync — the FULLY AUTOMATIC index reconciliation
# ──────────────────────────────────────────────────────────────────────────────

_SYNC_LOCK = threading.Lock()          # serialize within this process

try:
    import portalocker                  # cross-process lock (already a dependency)
except Exception:                       # degrade gracefully if unavailable
    portalocker = None


def _manifest_path() -> Path:
    return Path(cfg('vault', 'path')) / '.memcon' / 'index_manifest.json'


def _sync_lock_path() -> Path:
    return Path(cfg('vault', 'path')) / '.memcon' / 'sync.lock'


def _reconcile() -> dict:
    """The mtime-manifest reconcile itself. Callers must already hold the sync
    locks (see sync_index)."""
    vault = Path(cfg('vault', 'path'))
    mpath = _manifest_path()
    try:
        manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    except Exception:
        manifest = {}

    current: dict = {}
    for p in vault.rglob("*.md"):
        try:
            rel = p.relative_to(vault)
        except ValueError:
            continue
        if any(part.startswith('_backup') or part == '.memcon' for part in rel.parts):
            continue
        if _is_excluded(str(p)):
            continue
        try:
            current[p.stem] = (str(p), p.stat().st_mtime)
        except OSError:
            continue

    synced = 0
    for doc, (path, mtime) in current.items():
        if manifest.get(doc) != mtime:            # new or modified since last sync
            try:
                if ingest_file(path):             # clean-replace handles stale chunks
                    manifest[doc] = mtime
                    synced += 1
            except Exception as e:
                print(f"[sync] {path}: {e}", file=sys.stderr)

    removed = 0
    for doc in list(manifest.keys()):
        if doc not in current:                    # note deleted from disk → prune
            delete_by_doc(doc)
            del manifest[doc]
            removed += 1

    try:
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(manifest))
    except Exception:
        pass
    return {"synced": synced, "removed": removed}


def sync_index() -> dict:
    """Reconcile the search index with the vault files INCREMENTALLY, using an
    mtime manifest. Reingest only notes that are new or changed since the last
    sync; drop chunks for notes deleted from disk. Cheap when nothing changed
    (just a stat scan) — so it's safe to call before EVERY read.

    This is what makes search always reflect what's on disk, with zero manual
    steps and no restart: a note saved while Qdrant was down becomes findable on
    the very next recall; an Obsidian edit is picked up automatically; a deleted
    note's chunks are pruned automatically.

    Concurrency-safe: memcon often runs in two clients at once (Claude Desktop +
    Code). A per-process lock plus a cross-process file lock ensure only ONE
    instance reconciles at a time — if another is already syncing, this call
    skips cleanly (the other brings the index current) rather than both
    redundantly reingesting and contending on Qdrant + the entity DB.

    Returns {synced, removed} (plus skipped="..." when another instance held it).
    """
    if cfg is None:
        return {"synced": 0, "removed": 0}
    with _SYNC_LOCK:                                       # intra-process guard
        if portalocker is None:
            return _reconcile()
        try:
            lp = _sync_lock_path()
            lp.parent.mkdir(parents=True, exist_ok=True)
            lock = portalocker.Lock(str(lp), timeout=0.1, fail_when_locked=True)
        except Exception:
            return _reconcile()                           # lock setup failed → just sync
        try:
            lock.acquire()
        except Exception:
            return {"synced": 0, "removed": 0, "skipped": "another instance syncing"}
        try:
            return _reconcile()
        finally:
            try:
                lock.release()
            except Exception:
                pass
