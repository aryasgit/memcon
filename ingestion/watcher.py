"""
ingestion/watcher.py
Vault file-watcher → incremental ingest.

Hardened against the write-amplification incident:
  - DEBOUNCE + COALESCE: rapid events on the same path collapse into one ingest
    after a quiet window, instead of one synchronous ingest per fs event.
  - SINGLE WORKER: ingests run on one background thread, never on the watchdog
    dispatcher thread, so a slow ingest can't stall event delivery.
  - NEVER-DIE: every ingest is wrapped — one exception (e.g. a transient Qdrant
    blip) can no longer kill the dispatcher and silently stop watching.
  - SELF-WRITE SUPPRESSION: ingest_file is manifest-aware (idempotent by mtime),
    so memcon's own writes self-skip; only genuine external edits cost an embed.
  - SELF-HEAL: if the observer thread dies, it is restarted.
"""
import time, sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ingestion.ingest import ingest_file

INGESTIBLE_SUFFIXES = (".md", ".pdf")
DEBOUNCE_SECONDS = float(os.getenv("MEMCON_WATCH_DEBOUNCE", "2.0"))


class DebouncedIngestor:
    """Coalesce filesystem events per path and ingest each at most once per quiet
    window, on a single daemon worker thread."""

    def __init__(self, debounce: float = DEBOUNCE_SECONDS):
        self._debounce = debounce
        self._pending: dict[str, float] = {}   # path -> last-event monotonic ts
        self._cv = threading.Condition()
        self._stop = False
        self._worker = threading.Thread(
            target=self._run, name="memcon-watch-ingest", daemon=True
        )
        self._worker.start()

    def submit(self, path: str) -> None:
        if not path.lower().endswith(INGESTIBLE_SUFFIXES):
            return
        with self._cv:
            self._pending[path] = time.monotonic()
            self._cv.notify()

    def stop(self) -> None:
        with self._cv:
            self._stop = True
            self._cv.notify()

    def _run(self) -> None:
        while True:
            with self._cv:
                while not self._pending and not self._stop:
                    self._cv.wait()
                if self._stop and not self._pending:
                    return
                now = time.monotonic()
                ready = [p for p, t in self._pending.items() if now - t >= self._debounce]
                if not ready:
                    # Nothing due yet — sleep until the soonest pending path matures.
                    soonest = min(self._pending.values())
                    self._cv.wait(timeout=max(0.05, self._debounce - (now - soonest)))
                    continue
                for p in ready:
                    self._pending.pop(p, None)
            # Ingest OUTSIDE the lock. A failure here must NEVER propagate — it
            # would otherwise kill this worker and the vault would stop syncing.
            for p in ready:
                try:
                    if os.path.exists(p):
                        ingest_file(p)   # manifest-aware: self-skips unchanged files
                except Exception as e:
                    print(f"[watcher] ingest failed (continuing): {p}: {e}", file=sys.stderr)


class VaultHandler(FileSystemEventHandler):
    def __init__(self, ingestor: DebouncedIngestor):
        self._ingestor = ingestor

    def on_modified(self, event):
        if not event.is_directory:
            self._ingestor.submit(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._ingestor.submit(event.src_path)

    def on_moved(self, event):
        # Obsidian renames Untitled.md → real name on first save
        if not event.is_directory:
            self._ingestor.submit(event.dest_path)


def _start_observer(handler, path) -> Observer:
    obs = Observer()
    obs.schedule(handler, path, recursive=True)
    obs.start()
    return obs


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "vault"
    ingestor = DebouncedIngestor()
    handler = VaultHandler(ingestor)
    observer = _start_observer(handler, path)
    print(f"👁  Watching {path}/ for changes (debounced {DEBOUNCE_SECONDS}s)...", file=sys.stderr)
    try:
        while True:
            time.sleep(1)
            # Self-heal: if the observer thread died for any reason, restart it so
            # the vault never silently stops being watched.
            if not observer.is_alive():
                print("[watcher] observer thread died — restarting", file=sys.stderr)
                try:
                    observer.stop()
                except Exception:
                    pass
                observer = _start_observer(handler, path)
    except KeyboardInterrupt:
        observer.stop()
        ingestor.stop()
    observer.join()
