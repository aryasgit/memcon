import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from memory.retrieve import query
from memory.writer import log_decision, log_debug, log_experiment, update_note, summarise_session
from ingestion.ingest import ingest_file
from memory.qdrant_store import ensure_collection, get_stats
from openai import OpenAI
from dotenv import load_dotenv
from config import cfg
load_dotenv()

VAULT_ROOT = Path(cfg('vault', 'path')).resolve()
SKIP_DIRS = set(cfg('vault', 'skip_dirs') or [])

app = FastAPI(title="Memcon API")
llm = OpenAI(
    base_url=cfg('llm','base_url'),
    api_key=os.getenv("LLM_API_KEY", "ollama")
)

@app.on_event("startup")
def startup():
    ensure_collection()

# ── REQUEST MODELS ────────────────────────────────────────

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

class DecisionRequest(BaseModel):
    title: str
    decision: str
    reasoning: str
    subsystem: str = "unknown"
    tags: list = []

class DebugRequest(BaseModel):
    title: str
    symptom: str
    cause: str = ""
    fix: str = ""
    status: str = "open"
    subsystem: str = "unknown"
    tags: list = []

class ExperimentRequest(BaseModel):
    title: str
    hypothesis: str
    result: str
    conclusion: str
    subsystem: str = "unknown"
    tags: list = []

class UpdateRequest(BaseModel):
    filepath: str
    content: str

class SessionRequest(BaseModel):
    summary: str
    subsystem: str = "unknown"

# ── READ ENDPOINTS ────────────────────────────────────────

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
        return {"answer": "No relevant memory found.", "sources": [],
                "chunks_used": 0, "raw_chunks": []}
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

# ── WRITE ENDPOINTS ───────────────────────────────────────

@app.post("/memory/decision")
def write_decision(req: DecisionRequest):
    path = log_decision(req.title, req.decision, req.reasoning,
                        req.subsystem, req.tags)
    return {"status": "written", "path": path}

@app.post("/memory/debug")
def write_debug(req: DebugRequest):
    path = log_debug(req.title, req.symptom, req.cause,
                     req.fix, req.status, req.subsystem, req.tags)
    return {"status": "written", "path": path}

@app.post("/memory/experiment")
def write_experiment(req: ExperimentRequest):
    path = log_experiment(req.title, req.hypothesis, req.result,
                          req.conclusion, req.subsystem, req.tags)
    return {"status": "written", "path": path}

@app.post("/memory/update")
def write_update(req: UpdateRequest):
    path = update_note(req.filepath, req.content)
    return {"status": "updated", "path": path}

@app.post("/memory/session")
def write_session(req: SessionRequest):
    path = summarise_session(req.summary, req.subsystem)
    return {"status": "written", "path": path}

@app.post("/ingest")
def ingest(req: IngestRequest):
    n = ingest_file(req.filepath)
    return {"chunks_added": n}

# ── RECENT ACTIVITY + NOTE PREVIEW ───────────────────────

@app.get("/memory/recent")
def recent(limit: int = 10):
    """Latest notes in the vault, sorted by modification time."""
    if not VAULT_ROOT.exists():
        return {"notes": []}
    notes = []
    for p in VAULT_ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(VAULT_ROOT).parts):
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        notes.append({
            "path": str(p.relative_to(VAULT_ROOT.parent)),
            "name": p.stem,
            "folder": p.parent.name,
            "mtime": st.st_mtime,
            "size": st.st_size,
        })
    notes.sort(key=lambda n: n["mtime"], reverse=True)
    return {"notes": notes[:limit]}


@app.get("/memory/note")
def note(path: str):
    """Return raw markdown of a vault note. Path is validated to stay inside the vault."""
    candidate = (VAULT_ROOT.parent / path).resolve()
    try:
        candidate.relative_to(VAULT_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="path outside vault")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return {
        "path": str(candidate.relative_to(VAULT_ROOT.parent)),
        "content": candidate.read_text(),
    }
