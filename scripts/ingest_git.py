import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv()
import git
from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, upsert_chunks

REPO_PATH = os.getenv("MEMCON_CODE_DIR") or os.getenv("BARQ_REPO") or "."
ensure_collection()

try:
    repo = git.Repo(REPO_PATH)
except Exception as e:
    print(f"[git] Could not open repo at {REPO_PATH}: {e}")
    sys.exit(1)

chunks = []
for commit in repo.iter_commits(max_count=200):
    text = f"Commit {commit.hexsha[:8]} | {commit.committed_datetime}\n{commit.message.strip()}"
    chunks.append({
        "text": text,
        "source": "git",
        "doc_name": f"commit_{commit.hexsha[:8]}",
        "chunk_id": f"git_{commit.hexsha}",
        "memory_type": "episodic",
        "subsystem": "version_control",
        "tags": ["git", "commit"],
    })

vectors = embed([c["text"] for c in chunks])
n = upsert_chunks(chunks, vectors)
print(f"✅ Ingested {n} git commits from {REPO_PATH}")
