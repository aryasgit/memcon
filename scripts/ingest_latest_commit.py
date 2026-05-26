#!/usr/bin/env python3
"""
Ingest the latest git commit (HEAD) from a target repo into Memcon.

Designed to be invoked by a git post-commit hook so every commit message
+ shortstat becomes searchable memory automatically. Fast — embeds and
upserts a single chunk.

Usage:
    python3 scripts/ingest_latest_commit.py [REPO_PATH]

REPO_PATH defaults to $MEMCON_CODE_DIR, then $BARQ_REPO, then $(pwd).
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import git as gitpy
except ImportError:
    print("[git-hook] gitpython not installed; skipping ingest. "
          "Run `pip install gitpython` in the Memcon venv.", file=sys.stderr)
    sys.exit(0)  # don't break commits — silent skip

from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, upsert_chunks


def main() -> int:
    target = (
        sys.argv[1] if len(sys.argv) > 1
        else os.environ.get("MEMCON_CODE_DIR")
        or os.environ.get("BARQ_REPO")
        or os.getcwd()
    )

    try:
        repo = gitpy.Repo(target, search_parent_directories=True)
    except Exception as e:
        print(f"[git-hook] not a git repo at {target}: {e}", file=sys.stderr)
        return 0  # don't break commits

    commit = repo.head.commit
    short = commit.hexsha[:8]

    # Shortstat: e.g. "3 files changed, 42 insertions(+), 5 deletions(-)"
    try:
        stats = commit.stats.total
        stat_line = f"{stats['files']} files, +{stats['insertions']} / -{stats['deletions']}"
    except Exception:
        stat_line = ""

    # Author + date in a stable format
    when = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    author = (commit.author.name or "").strip()

    text = "\n".join(filter(None, [
        f"Commit {short} · {when}" + (f" · {author}" if author else ""),
        stat_line,
        "",
        commit.message.strip(),
    ]))

    chunk = {
        "text": text,
        "source": f"git:{repo.working_dir}",
        "doc_name": f"commit_{short}",
        "chunk_id": f"git:{commit.hexsha}",
        "memory_type": "episodic",
        "subsystem": "version_control",
        "tags": ["git", "commit"],
    }

    ensure_collection()
    vectors = embed([chunk["text"]])
    n = upsert_chunks([chunk], vectors)
    print(f"[git-hook] ingested commit {short} ({n} chunk)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
