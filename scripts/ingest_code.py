#!/usr/bin/env python3
"""
Index a source-code directory into Memcon.

This makes semantic queries like "where is the IMU initialised?" or "find
the gait phase continuity logic" return actual code, not just notes.

Usage:
    python3 scripts/ingest_code.py [PATH]

PATH defaults to $MEMCON_CODE_DIR, then $BARQ_REPO, then ./ — the current
project directory. Respects a sensible exclusion list (.git, .venv,
node_modules, __pycache__, build/dist/target, *.lock, binary blobs).

Each file becomes one or more chunks tagged subsystem="code", memory_type=
"procedural", with `language` and a synthetic title inferred from the path.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingestion.embedder import embed
from memory.qdrant_store import ensure_collection, upsert_chunks


# What we index
LANG_BY_EXT = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".rs": "rust", ".go": "go", ".java": "java", ".kt": "kotlin",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp",
    ".cs": "csharp", ".swift": "swift", ".rb": "ruby",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".fish": "shell",
    ".bat": "batch", ".ps1": "powershell",
    ".lua": "lua", ".r": "r", ".jl": "julia", ".scala": "scala",
    ".php": "php", ".pl": "perl",
    ".sql": "sql",
    ".html": "html", ".css": "css", ".scss": "css",
    ".vue": "vue", ".svelte": "svelte",
    ".yml": "yaml", ".yaml": "yaml",
    ".toml": "toml",
    ".dockerfile": "dockerfile", "Dockerfile": "dockerfile",
    ".gradle": "groovy", ".cmake": "cmake",
}

# Dirs we skip outright
SKIP_DIRS = {
    ".git", ".venv", "venv", ".env",
    "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "build", "dist", "target", "out", ".next", ".nuxt", ".turbo",
    ".cache", ".idea", ".vscode", ".cursor",
    "qdrant_storage", "vault", "tmp",
}

# Files we always skip
SKIP_FILE_SUFFIXES = (
    ".lock", ".min.js", ".min.css", ".map",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".mp3", ".mp4", ".wav", ".webm", ".mov",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe", ".bin",
    ".class", ".jar", ".o", ".obj", ".a", ".lib",
)

MAX_FILE_BYTES = 250_000   # skip absolute monsters (logs, generated, etc.)
CHUNK_LINES    = 80        # ~80 lines per chunk gives ~1.5KB per piece
MIN_CHUNK_LEN  = 60        # chars — skip near-empty chunks


def detect_language(path: Path) -> str | None:
    """Best-effort language detection from filename + extension."""
    name = path.name
    if name in LANG_BY_EXT:
        return LANG_BY_EXT[name]
    suffix = path.suffix.lower()
    return LANG_BY_EXT.get(suffix)


def should_index(path: Path, root: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
        return False
    if path.name.startswith('.') and path.suffix not in {'.gitignore', '.env.example'}:
        # hidden files like .DS_Store, .env, .lock — skip
        return False
    if path.name.lower().endswith(SKIP_FILE_SUFFIXES):
        return False
    if path.is_symlink():
        return False
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return False
        if path.stat().st_size == 0:
            return False
    except OSError:
        return False
    return detect_language(path) is not None


def chunk_code(path: Path, root: Path) -> list[dict]:
    """Split a source file into line-based chunks tagged with language + path."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"[code] skip {path}: {e}", file=sys.stderr)
        return []

    lines = text.splitlines()
    language = detect_language(path) or "text"
    rel_path = path.relative_to(root).as_posix()
    doc_name = rel_path.replace("/", "·")  # avoids treating slashes as wikilink delimiters

    chunks: list[dict] = []
    for i in range(0, len(lines), CHUNK_LINES):
        block = "\n".join(lines[i:i + CHUNK_LINES])
        if len(block.strip()) < MIN_CHUNK_LEN:
            continue
        # Prefix each chunk with its source so the embedding has structural signal
        body = f"```{language}\n# {rel_path}  (L{i+1}-L{min(i+CHUNK_LINES, len(lines))})\n{block}\n```"
        chunks.append({
            "text": body,
            "source": str(path.resolve()),
            "doc_name": doc_name,
            "chunk_id": f"code:{rel_path}:{i}",
            "memory_type": "procedural",
            "subsystem": "code",
            "tags": [language, "code"],
        })
    return chunks


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else (
        os.environ.get("MEMCON_CODE_DIR") or
        os.environ.get("BARQ_REPO") or
        "."
    )
    root = Path(target).resolve()
    if not root.exists():
        print(f"[code] target not found: {root}", file=sys.stderr)
        return 1

    print(f"[code] indexing {root}")
    ensure_collection()

    candidates = [p for p in root.rglob("*") if p.is_file() and should_index(p, root)]
    print(f"[code] {len(candidates)} files matched")

    all_chunks: list[dict] = []
    for p in candidates:
        all_chunks.extend(chunk_code(p, root))
    if not all_chunks:
        print("[code] nothing to ingest")
        return 0

    print(f"[code] embedding {len(all_chunks)} chunks...")
    # Batch embedding to keep memory bounded
    BATCH = 64
    total_added = 0
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i:i + BATCH]
        vectors = embed([c["text"] for c in batch])
        total_added += upsert_chunks(batch, vectors)
    print(f"[code] done. {total_added} chunks added to Qdrant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
