import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastapi import FastAPI
from pydantic import BaseModel
from memory.retrieve import query
from ingestion.ingest import ingest_file
from memory.qdrant_store import ensure_collection

app = FastAPI(title="BARQ Hive Mind API")

@app.on_event("startup")
def startup():
    ensure_collection()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    subsystem: str = None

class IngestRequest(BaseModel):
    filepath: str

@app.post("/query")
def query_memory(req: QueryRequest):
    results = query(req.query, top_k=req.top_k, subsystem=req.subsystem)
    return {"results": results}

@app.post("/ingest")
def ingest(req: IngestRequest):
    n = ingest_file(req.filepath)
    return {"chunks_added": n}

@app.get("/health")
def health():
    return {"status": "ok", "collection": "barq_memory"}
