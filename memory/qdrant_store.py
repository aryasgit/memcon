import uuid, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from config import cfg

client = QdrantClient(
    host=os.getenv('ENGRAM_QDRANT_HOST', cfg('qdrant','host')),
    port=int(os.getenv('ENGRAM_QDRANT_PORT', cfg('qdrant','port'))),
)
COLLECTION = cfg('memory','collection')
DIM = cfg('memory','vector_dim')

def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )
        print(f"[qdrant] Created collection: {COLLECTION}", file=sys.stderr)

def upsert_chunks(chunks: list[dict], vectors: list[list[float]]) -> int:
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])),
            vector=v,
            payload=c,
        )
        for c, v in zip(chunks, vectors)
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)

def search(query_vec: list[float], top_k: int = 5, subsystem: str = None) -> list[dict]:
    query_filter = None
    if subsystem:
        query_filter = Filter(must=[
            FieldCondition(key="subsystem", match=MatchValue(value=subsystem))
        ])
    results = client.query_points(
        collection_name=COLLECTION,
        query=query_vec,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    ).points
    return [{"score": round(r.score, 4), **r.payload} for r in results]

def get_stats() -> dict:
    try:
        info = client.get_collection(COLLECTION)
        return {
            "total_chunks": info.points_count,
            "collection": COLLECTION,
            "vector_dim": DIM,
            "project": cfg('project','name'),
        }
    except:
        return {"total_chunks": 0, "collection": COLLECTION}
