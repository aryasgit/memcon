import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sentence_transformers import SentenceTransformer
from config import cfg

_model = None

def get_model():
    global _model
    if _model is None:
        model_name = cfg('memory','embedding_model')
        print(f"[embedder] Loading {model_name}...", file=sys.stderr)
        _model = SentenceTransformer(model_name)
        print("[embedder] Model ready.", file=sys.stderr)
    return _model

def embed(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, batch_size=32, show_progress_bar=False).tolist()
