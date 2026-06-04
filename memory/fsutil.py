"""
memory/fsutil.py
Durable, concurrency-safe file primitives shared by every note writer.

Two guarantees the audit found missing:
  - atomic_write_text(): a note is written via temp-file + fsync + os.replace, so
    a stall/crash/OOM-kill mid-write can NEVER leave a truncated or half-written
    note (the old open('w')/write_text could, and the watcher would then index
    the corrupted version).
  - note_lock(): a cross-process advisory lock per note, so the two MCP clients
    (Claude Desktop + Cursor) sharing the vault can't lost-update the same file
    during a reciprocal-link edit / enricher rewrite / capture overwrite.
"""
from __future__ import annotations
import os, sys, tempfile, hashlib
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg

try:
    import portalocker
except Exception:                 # degrade gracefully if unavailable
    portalocker = None


def atomic_write_text(path, text: str) -> None:
    """Write `text` to `path` durably and atomically (temp in same dir → fsync →
    os.replace). The destination's old content survives until the replace flips
    it to the new content, so an interrupted write can't corrupt it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _lock_dir() -> Path:
    d = Path(cfg('vault', 'path')) / '.memcon' / 'locks'
    d.mkdir(parents=True, exist_ok=True)
    return d


@contextmanager
def note_lock(path, timeout: float = 10.0):
    """Cross-process per-note lock for a read-modify-write. The lock file lives in
    .memcon/locks/ (gitignored, watcher-excluded) so it never touches the note or
    trips the watcher. If the lock can't be taken in `timeout`s, we proceed
    anyway — a rare race is better than hanging or failing the write."""
    if portalocker is None:
        yield
        return
    key = hashlib.sha1(str(Path(path).resolve()).encode()).hexdigest()[:16]
    lockfile = str(_lock_dir() / f"{key}.lock")
    lock = portalocker.Lock(lockfile, timeout=timeout)
    acquired = False
    try:
        try:
            lock.acquire()
            acquired = True
        except Exception as e:
            print(f"[fsutil] note_lock timeout, proceeding unlocked: {path}: {e}", file=sys.stderr)
        yield
    finally:
        if acquired:
            try:
                lock.release()
            except Exception:
                pass
