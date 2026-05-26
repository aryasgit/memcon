import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from memory.retrieve import query
from ingestion.ingest import ingest_file
from memory.qdrant_store import ensure_collection, get_stats
from openai import OpenAI
from dotenv import load_dotenv
from config import cfg
load_dotenv()

app = FastAPI(title="Engram API")
llm = OpenAI(
    base_url=cfg('llm','base_url'),
    api_key=os.getenv("LLM_API_KEY", "ollama")
)

@app.on_event("startup")
def startup():
    ensure_collection()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    subsystem: str | None = None

class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    subsystem: str | None = None

class IngestRequest(BaseModel):
    filepath: str

@app.get("/ui", response_class=HTMLResponse)
def ui():
    ui_path = os.path.join(os.path.dirname(__file__), "ui.html")
    with open(ui_path) as f:
        return f.read()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    return get_stats()

@app.get("/config")
def config():
    return {
        "project": cfg('project','name'),
        "domain": cfg('project','domain'),
        "subsystems": cfg('subsystems'),
        "memory_types": cfg('memory_types'),
        "llm_model": cfg('llm','model'),
    }

@app.post("/query")
def query_memory(req: QueryRequest):
    results = query(req.query, top_k=req.top_k, subsystem=req.subsystem)
    return {"results": results}

@app.post("/ask")
def ask(req: AskRequest):
    results = query(req.question, top_k=req.top_k, subsystem=req.subsystem)
    if not results:
        return {"answer": "No relevant memory found.", "sources": [], "chunks_used": 0, "raw_chunks": []}
    context = "\n\n---\n\n".join([
        f"[{r['memory_type']} | {r['subsystem']} | score={r['score']}]\n{r['text']}"
        for r in results
    ])
    prompt = f"""You are an engineering memory assistant.
Answer using ONLY the context below. Be concise and technical.
If the context doesn't answer the question, say so explicitly.

CONTEXT:
{context}

QUESTION: {req.question}

ANSWER:"""
    response = llm.chat.completions.create(
        model=cfg('llm','model'),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=cfg('llm','max_tokens'),
    )
    return {
        "answer": response.choices[0].message.content,
        "sources": list(set(r["doc_name"] for r in results)),
        "chunks_used": len(results),
        "raw_chunks": results,
    }

@app.post("/ingest")
def ingest(req: IngestRequest):
    n = ingest_file(req.filepath)
    return {"chunks_added": n}
