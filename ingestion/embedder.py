import sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sentence_transformers import SentenceTransformer
from config import cfg

_model = None
_model_lock = threading.Lock()

def get_model():
    # Double-checked locking: under the bulk-import burst the watcher thread and
    # the writer's first ingest can both see `_model is None` and load the
    # ~90 MB model simultaneously (2x memory + 2x slow CPU load on a 16GB box).
    # The lock guarantees exactly one load.
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                model_name = cfg('memory','embedding_model')
                print(f"[embedder] Loading {model_name}...", file=sys.stderr)
                _model = SentenceTransformer(model_name)
                print("[embedder] Model ready.", file=sys.stderr)
    return _model

def embed(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, batch_size=32, show_progress_bar=False).tolist()
