"""
memory/worker.py
One bounded background worker pool for ALL of memcon's deferred work — ingest,
entity indexing, reciprocal links, enrichment, and capture's structuring pass.

WHY: the old pattern spawned a fresh daemon thread per write and per capture
(and the enricher spawned yet another), so a 20-note bulk import fanned out into
dozens of concurrent threads, each loading model context + forking `git` + doing
embeds, and thrashed the machine. Here a SMALL FIXED pool drains a BOUNDED queue,
so background load is capped no matter how fast writes arrive. This is the
backpressure that was missing.

Anything enqueued here is best-effort: the note is always already durably on
disk before work is submitted, and the manifest/reconcile + watcher are the
backstop that will index it even if a job is dropped under flood.
"""
from __future__ import annotations
import os, sys, threading, queue

_WORKERS = max(1, int(os.getenv("MEMCON_BG_WORKERS", "2")))
_MAXQ = max(16, int(os.getenv("MEMCON_BG_QUEUE", "2000")))

_q: "queue.Queue" = queue.Queue(maxsize=_MAXQ)
_started = False
_start_lock = threading.Lock()


def _run() -> None:
    while True:
        fn, args, kwargs = _q.get()
        try:
            fn(*args, **kwargs)
        except Exception as e:
            name = getattr(fn, "__name__", repr(fn))
            print(f"[worker] job {name} failed: {e}", file=sys.stderr)
        finally:
            _q.task_done()


def _ensure_started() -> None:
    global _started
    if _started:
        return
    with _start_lock:
        if _started:
            return
        for i in range(_WORKERS):
            threading.Thread(target=_run, name=f"memcon-bg-{i}", daemon=True).start()
        _started = True


def submit(fn, *args, **kwargs) -> bool:
    """Enqueue background work. Returns True if queued, False if the queue is
    full. On False the caller's data is already on disk, so the reconcile/watcher
    backstop will pick it up — dropping is safe, blocking the stdio thread is not."""
    _ensure_started()
    try:
        _q.put_nowait((fn, args, kwargs))
        return True
    except queue.Full:
        print("[worker] queue full — deferring to reconcile/watcher backstop", file=sys.stderr)
        return False
