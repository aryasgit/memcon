import sys, os, time, threading
from collections import defaultdict, deque
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
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

from contextlib import asynccontextmanager


@asynccontextmanager
async def _lifespan(_app):
    # Startup: ensure the collection exists and pre-warm the embedding model in
    # the background so the first /query or /ask doesn't pay the one-time load.
    try:
        ensure_collection()
    except Exception:
        pass

    def _warm():
        try:
            from ingestion.embedder import get_model
            get_model()
        except Exception:
            pass
    threading.Thread(target=_warm, daemon=True, name="memcon-api-warm").start()
    yield


app = FastAPI(title="Memcon API", lifespan=_lifespan)
try:
    _LLM_TIMEOUT = float(cfg('llm', 'timeout'))
except Exception:
    _LLM_TIMEOUT = 90.0
# Hard timeout so a hung/cold Ollama can't pin a worker thread forever on /ask.
llm = OpenAI(
    base_url=cfg('llm','base_url'),
    api_key=os.getenv("LLM_API_KEY", "ollama"),
    timeout=_LLM_TIMEOUT,
)

# ── REQUEST GUARD: body-size limit + tiered rate limiting ──────────────────
# The API binds to localhost by default (memcon.config.yaml / start.sh). These
# guards are defence-in-depth so a runaway or hostile *local* client can't
# (a) OOM the box with a giant body, or (b) peg it by hammering the LLM/embed
# endpoints. Dependency-free; every limit is configurable in memcon.config.yaml.
def _cfg_int(section, key, default):
    try:
        return int(cfg(section, key))
    except Exception:
        return default

def _cfg_list(section, key):
    try:
        v = cfg(section, key)
        return list(v) if v else []
    except Exception:
        return []

MAX_BODY_BYTES   = _cfg_int('api', 'max_body_bytes', 1_000_000)       # ~1 MB
RATE_LIMIT       = _cfg_int('api', 'rate_limit_per_min', 300)         # all routes
WRITE_RATE_LIMIT = _cfg_int('api', 'write_rate_limit_per_min', 60)    # write/LLM routes
_RL_WINDOW = 60.0
_rl_global = defaultdict(deque)
_rl_write  = defaultdict(deque)
_rl_lock   = threading.Lock()
_RL_EXEMPT = {"/health"}                        # only the health probe is uncapped
_STRICT_PATHS = {                               # expensive or state-changing
    "/ask", "/ingest",
    "/memory/decision", "/memory/debug", "/memory/experiment",
    "/memory/update", "/memory/session",
}

def _prune(dq, cutoff):
    while dq and dq[0] <= cutoff:
        dq.popleft()

@app.middleware("http")
async def request_guard(request: Request, call_next):
    path = request.url.path

    # 1) Reject oversized bodies up front (cheap Content-Length check).
    clen = request.headers.get("content-length")
    if clen is not None:
        try:
            if int(clen) > MAX_BODY_BYTES:
                return JSONResponse(status_code=413,
                    content={"detail": f"request body too large (>{MAX_BODY_BYTES} bytes)"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "invalid Content-Length"})

    # 2) Tiered rate limit: every route shares a global budget; the expensive /
    #    state-changing routes also share a stricter budget.
    if path not in _RL_EXEMPT:
        now = time.monotonic()
        cutoff = now - _RL_WINDOW
        client = request.client.host if request.client else "local"
        strict = path in _STRICT_PATHS
        with _rl_lock:
            g = _rl_global[client]; _prune(g, cutoff)
            w = _rl_write[client] if strict else None
            if strict:
                _prune(w, cutoff)
            if len(g) >= RATE_LIMIT:
                retry = max(1, int(_RL_WINDOW - (now - g[0])))
                return JSONResponse(status_code=429,
                    content={"detail": f"rate limit exceeded ({RATE_LIMIT}/min)"},
                    headers={"Retry-After": str(retry)})
            if strict and len(w) >= WRITE_RATE_LIMIT:
                retry = max(1, int(_RL_WINDOW - (now - w[0])))
                return JSONResponse(status_code=429,
                    content={"detail": f"rate limit exceeded ({WRITE_RATE_LIMIT}/min on write/LLM routes)"},
                    headers={"Retry-After": str(retry)})
            g.append(now)
            if strict:
                w.append(now)
    return await call_next(request)


# ── HOST ALLOWLIST: defeat DNS-rebinding ───────────────────────────────────
# A malicious web page can re-point its own domain at 127.0.0.1 and fetch this
# API as if same-origin (DNS rebinding), bypassing the localhost bind. The Host
# header still carries the attacker's domain, so we reject any Host that isn't a
# known-local name. Legit clients (the dashboard, the vscode extension) always
# send Host: localhost / 127.0.0.1, so this is invisible to them. Add more in
# memcon.config.yaml → api.allowed_hosts if you front the API with a proxy.
_ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
_ALLOWED_HOSTS |= {str(h).lower() for h in _cfg_list('api', 'allowed_hosts')}
try:
    _ALLOWED_HOSTS.add(str(cfg('api', 'host')).lower())
except Exception:
    pass
app.add_middleware(TrustedHostMiddleware, allowed_hosts=sorted(_ALLOWED_HOSTS))


# ── PATH SAFETY: keep user-supplied paths inside the vault ─────────────────
def _vault_safe(path_str: str) -> Path:
    """Resolve a user-supplied note path and confine it to the vault. Accepts an
    absolute path (as the write tools return) or one relative to the vault's
    parent. Raises HTTP 400 on traversal — closes the path-traversal write/read
    on /memory/update, /ingest and /memory/note."""
    if not isinstance(path_str, str) or not path_str.strip():
        raise HTTPException(status_code=400, detail="empty path")
    p = Path(path_str)
    candidate = (p if p.is_absolute() else (VAULT_ROOT.parent / p)).resolve()
    try:
        candidate.relative_to(VAULT_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="path must be inside the vault")
    return candidate


# (startup logic now lives in the _lifespan handler near the top of this file)

# ── REQUEST MODELS ────────────────────────────────────────
# Every string field is length-bounded and every numeric field range-bounded, so
# an oversized/malformed request is rejected with 422 before it reaches the
# model / embedder / LLM. The body-size middleware is the global backstop.
MAX_TEXT  = 50_000   # big prose fields (symptom, reasoning, content, summary…)
MAX_TITLE = 300
MAX_SHORT = 64       # subsystem, status

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(5, ge=1, le=50)
    subsystem: str | None = Field(None, max_length=MAX_SHORT)

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(5, ge=1, le=50)
    subsystem: str | None = Field(None, max_length=MAX_SHORT)

class IngestRequest(BaseModel):
    filepath: str = Field(..., min_length=1, max_length=1024)

class DecisionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TITLE)
    decision: str = Field(..., max_length=MAX_TEXT)
    reasoning: str = Field(..., max_length=MAX_TEXT)
    subsystem: str = Field("unknown", max_length=MAX_SHORT)
    tags: list[str] = Field(default_factory=list, max_length=32)

class DebugRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TITLE)
    symptom: str = Field(..., max_length=MAX_TEXT)
    cause: str = Field("", max_length=MAX_TEXT)
    fix: str = Field("", max_length=MAX_TEXT)
    status: str = Field("open", max_length=MAX_SHORT)
    subsystem: str = Field("unknown", max_length=MAX_SHORT)
    tags: list[str] = Field(default_factory=list, max_length=32)

class ExperimentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TITLE)
    hypothesis: str = Field(..., max_length=MAX_TEXT)
    result: str = Field(..., max_length=MAX_TEXT)
    conclusion: str = Field(..., max_length=MAX_TEXT)
    subsystem: str = Field("unknown", max_length=MAX_SHORT)
    tags: list[str] = Field(default_factory=list, max_length=32)

class UpdateRequest(BaseModel):
    filepath: str = Field(..., min_length=1, max_length=1024)
    content: str = Field(..., min_length=1, max_length=MAX_TEXT)

class SessionRequest(BaseModel):
    summary: str = Field(..., min_length=1, max_length=MAX_TEXT)
    subsystem: str = Field("unknown", max_length=MAX_SHORT)

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
    from memory.llm import is_available
    if not is_available():
        # Lean mode: no local LLM — return the grounding chunks for the caller.
        return {
            "answer": None,
            "note": "No local LLM configured — compose the answer from raw_chunks.",
            "sources": list(set(r["doc_name"] for r in results)),
            "chunks_used": len(results),
            "raw_chunks": results,
        }
    try:
        response = llm.chat.completions.create(
            model=cfg('llm','model'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg('llm','max_tokens'),
        )
        answer = response.choices[0].message.content
    except Exception as e:
        # LLM down/timed out — still return the grounding chunks instead of 500.
        answer = (f"(Local LLM unavailable: {e}. The relevant memory chunks are "
                  f"returned below.)")
    return {
        "answer": answer,
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
    safe = _vault_safe(req.filepath)          # confine writes to the vault
    path = update_note(str(safe), req.content)
    return {"status": "updated", "path": path}

@app.post("/memory/session")
def write_session(req: SessionRequest):
    path = summarise_session(req.summary, req.subsystem)
    return {"status": "written", "path": path}

@app.post("/ingest")
def ingest(req: IngestRequest):
    safe = _vault_safe(req.filepath)          # confine ingestion to the vault
    n = ingest_file(str(safe))
    return {"chunks_added": n}

# ── RECENT ACTIVITY + NOTE PREVIEW ───────────────────────

@app.get("/memory/recent")
def recent(limit: int = Query(10, ge=1, le=200)):
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
def note(path: str = Query(..., min_length=1, max_length=1024)):
    """Return raw markdown of a vault note. Path is confined to the vault."""
    candidate = _vault_safe(path)
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return {
        "path": str(candidate.relative_to(VAULT_ROOT.parent)),
        "content": candidate.read_text(),
    }
