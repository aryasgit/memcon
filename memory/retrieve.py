import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, search

def query(text: str, top_k: int = 5, subsystem: str = None) -> list[dict]:
    ensure_collection()
    vec = embed([text])[0]
    return search(vec, top_k=top_k, subsystem=subsystem)

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "servo overheating"
    results = query(q)
    for r in results:
        print(f"\n[{r['score']}] {r['doc_name']} ({r['subsystem']})")
        print(r['text'][:200])
