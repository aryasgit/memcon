import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastapi import FastAPI
from pydantic import BaseModel
from memory.retrieve import query
from ingestion.ingest import ingest_file
from memory.qdrant_store import ensure_collection
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="BARQ Hive Mind API")

# Ollama runs an OpenAI-compatible server locally
llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

@app.on_event("startup")
def startup():
    ensure_collection()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    subsystem: str = None

class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    subsystem: str = None

class IngestRequest(BaseModel):
    filepath: str

@app.post("/query")
def query_memory(req: QueryRequest):
    results = query(req.query, top_k=req.top_k, subsystem=req.subsystem)
    return {"results": results}

@app.post("/ask")
def ask(req: AskRequest):
    results = query(req.question, top_k=req.top_k, subsystem=req.subsystem)

    if not results:
        return {"answer": "No relevant memory found.", "sources": [], "chunks_used": 0}

    context = "\n\n---\n\n".join([
        f"[{r['memory_type']} | {r['subsystem']} | score={r['score']}]\n{r['text']}"
        for r in results
    ])

    prompt = f"""You are BARQ's engineering memory assistant for a 12-DOF quadruped robot.
Answer using ONLY the context below. Be concise and technical.
If the context doesn't answer the question, say so explicitly.

CONTEXT:
{context}

QUESTION: {req.question}

ANSWER:"""

    response = llm.chat.completions.create(
        model="qwen2.5-coder:7b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": list(set(r["doc_name"] for r in results)),
        "chunks_used": len(results)
    }

@app.post("/ingest")
def ingest(req: IngestRequest):
    n = ingest_file(req.filepath)
    return {"chunks_added": n}

@app.get("/health")
def health():
    return {"status": "ok", "collection": "barq_memory"}
