import sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sentence_transformers import SentenceTransformer
from config import cfg

_model = None
_model_lock = threading.Lock()
_encode_lock = threading.Lock()

def is_loaded() -> bool:
    """True if the embedding model is already in memory. Latency-sensitive paths
    (note writes) use this to embed only when WARM and skip gracefully when cold —
    instead of blocking on a multi-second load or, on a fresh install, the ~90MB
    first-run model DOWNLOAD from HuggingFace."""
    return _model is not None

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
    # Serialize encodes: the underlying torch model is NOT safe to call from many
    # threads at once — high concurrency can leak threads / segfault. In normal
    # use embeds are near-serial anyway (the bounded worker + single stdio
    # thread), so the lock costs ~nothing; under a stress burst it keeps the
    # process stable instead of crashing.
    model = get_model()
    with _encode_lock:
        return model.encode(texts, batch_size=32, show_progress_bar=False).tolist()
