import uuid, sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from config import cfg

COLLECTION = cfg('memory','collection')
DIM = cfg('memory','vector_dim')

# Every Qdrant call gets a hard timeout so a hung or slow Qdrant can NEVER block
# the caller (the MCP stdio thread, the API event loop, or the watcher) forever.
# The client is built LAZILY so importing this module does no network I/O at
# process start — a down Qdrant must not stop the MCP server from booting (the
# default client constructor otherwise does a synchronous version-probe call).
try:
    _CLIENT_TIMEOUT = float(cfg('qdrant', 'timeout'))
except Exception:
    _CLIENT_TIMEOUT = 5.0

_client = None
_client_lock = threading.Lock()


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = QdrantClient(
                    host=os.getenv('MEMCON_QDRANT_HOST', cfg('qdrant','host')),
                    port=int(os.getenv('MEMCON_QDRANT_PORT', cfg('qdrant','port'))),
                    timeout=_CLIENT_TIMEOUT,
                    check_compatibility=False,  # no version-probe network call at construct
                )
    return _client


_collection_ready = False


def ensure_collection():
    """Create the collection if missing. Memoized — after the first success this
    is a no-op, so we don't pay a get_collections() round-trip on every single
    ingest (which, under the watcher storm, was ~140 wasted round-trips)."""
    global _collection_ready
    if _collection_ready:
        return
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )
        print(f"[qdrant] Created collection: {COLLECTION}", file=sys.stderr)
    _collection_ready = True


def upsert_chunks(chunks: list[dict], vectors: list[list[float]]) -> int:
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])),
            vector=v,
            payload=c,
        )
        for c, v in zip(chunks, vectors)
    ]
    _get_client().upsert(collection_name=COLLECTION, points=points)
    return len(points)

def delete_by_doc(doc_name: str) -> None:
    """Remove every point for a given doc_name. Used as a clean-replace before
    re-ingesting a note, so editing or shrinking a note never leaves orphan
    chunks (e.g. the title chunk of a once-empty note) lingering in the index."""
    try:
        _get_client().delete(
            collection_name=COLLECTION,
            points_selector=Filter(must=[
                FieldCondition(key="doc_name", match=MatchValue(value=doc_name))
            ]),
        )
    except Exception as e:
        print(f"[qdrant] delete_by_doc({doc_name}) failed: {e}", file=sys.stderr)


def search(query_vec: list[float], top_k: int = 5, subsystem: str = None) -> list[dict]:
    query_filter = None
    if subsystem:
        query_filter = Filter(must=[
            FieldCondition(key="subsystem", match=MatchValue(value=subsystem))
        ])
    results = _get_client().query_points(
        collection_name=COLLECTION,
        query=query_vec,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    ).points
    return [{"score": round(r.score, 4), **r.payload} for r in results]

def get_stats() -> dict:
    try:
        info = _get_client().get_collection(COLLECTION)
        return {
            "total_chunks": info.points_count,
            "collection": COLLECTION,
            "vector_dim": DIM,
            "project": cfg('project','name'),
            "status": "ok",
        }
    except Exception as e:
        # Distinguish a real outage from an empty vault — the old bare `except`
        # returned total_chunks:0, so an unreachable Qdrant looked like a healthy
        # empty index and masked the very outage you'd be trying to diagnose.
        return {"total_chunks": 0, "collection": COLLECTION, "status": "error", "error": str(e)}
