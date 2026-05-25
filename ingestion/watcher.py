import time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ingestion.ingest import ingest_file

class VaultHandler(FileSystemEventHandler):
    def _try_ingest(self, path):
        if path.endswith(".md") and os.path.exists(path):
            ingest_file(path)

    def on_modified(self, event):
        if not event.is_directory:
            self._try_ingest(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._try_ingest(event.src_path)

    def on_moved(self, event):
        # Obsidian renames Untitled.md → real name on first save
        if not event.is_directory:
            self._try_ingest(event.dest_path)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "vault"
    handler = VaultHandler()
    observer = Observer()
    observer.schedule(handler, path, recursive=True)
    observer.start()
    print(f"👁  Watching {path}/ for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
