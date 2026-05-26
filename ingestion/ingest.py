import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ingestion.chunker import chunk_markdown
from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, upsert_chunks

def ingest_file(filepath: str) -> int:
    ensure_collection()
    chunks = chunk_markdown(filepath)
    if not chunks:
        print(f"[ingest] No chunks found in {filepath}", file=sys.stderr)
        return 0
    texts = [c["text"] for c in chunks]
    vectors = embed(texts)
    n = upsert_chunks(chunks, vectors)
    print(f"[ingest] {filepath} → {n} chunks added", file=sys.stderr)
    return n
