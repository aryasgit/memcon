from sentence_transformers import SentenceTransformer

_model = None

def get_model():
    global _model
    if _model is None:
        print("[embedder] Loading model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[embedder] Model ready.")
    return _model

def embed(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, batch_size=32, show_progress_bar=False).tolist()
