import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import frontmatter
import re
from pathlib import Path
from config import cfg


def chunk_markdown(filepath: str) -> list[dict]:
    try:
        with open(filepath) as f:
            post = frontmatter.load(f)
    except Exception as e:
        print(f"[chunker] Skipping {filepath}: {e}", file=sys.stderr)
        return []

    text = post.content
    meta = dict(post.metadata)
    filename = Path(filepath).stem
    chunk_size = cfg('vault','chunk_size')
    min_length = cfg('vault','min_chunk_length')
    sections = re.split(r'\n(?=#{1,3} )', text)

    chunks = []
    for i, section in enumerate(sections):
        words = section.split()
        for j in range(0, len(words), chunk_size):
            chunk_text = ' '.join(words[j:j+chunk_size])
            if len(chunk_text.strip()) < min_length:
                continue
            chunks.append({
                "text": chunk_text,
                "source": filepath,
                "doc_name": filename,
                "chunk_id": f"{filename}_{i}_{j}",
                "memory_type": meta.get("memory_type", "semantic"),
                "subsystem": meta.get("subsystem", "unknown"),
                "tags": meta.get("tags", []),
            })
    return chunks


def chunk_pdf(filepath: str) -> list[dict]:
    """Extract text from a PDF and chunk it by page-window, tagged subsystem='docs'.

    Best-effort: encrypted / image-only / corrupted PDFs are skipped silently
    rather than crashing the watcher.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        print("[chunker] pypdf not installed; skipping PDF. "
              "Run `pip install pypdf` in the Memcon venv.", file=sys.stderr)
        return []

    try:
        reader = PdfReader(filepath)
    except Exception as e:
        print(f"[chunker] Cannot read PDF {filepath}: {e}", file=sys.stderr)
        return []

    if reader.is_encrypted:
        try:
            reader.decrypt("")  # try empty-password unlock
        except Exception:
            print(f"[chunker] Skipping encrypted PDF: {filepath}", file=sys.stderr)
            return []

    filename = Path(filepath).stem
    chunk_size = cfg('vault', 'chunk_size')
    min_length = cfg('vault', 'min_chunk_length')

    # Walk pages, build a flat token stream tagged with page numbers
    parts: list[tuple[int, str]] = []
    for page_idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            parts.append((page_idx, text))
    if not parts:
        return []

    chunks: list[dict] = []
    # Chunk page-by-page so retrieved context cites a meaningful page
    for page_idx, text in parts:
        words = text.split()
        for j in range(0, len(words), chunk_size):
            chunk_text = ' '.join(words[j:j + chunk_size])
            if len(chunk_text.strip()) < min_length:
                continue
            chunks.append({
                "text": f"[{filename} · p.{page_idx}]\n{chunk_text}",
                "source": filepath,
                "doc_name": filename,
                "chunk_id": f"pdf:{filename}:p{page_idx}:{j}",
                "memory_type": "semantic",
                "subsystem": "docs",
                "tags": ["pdf", "docs"],
            })
    return chunks


def chunk_file(filepath: str) -> list[dict]:
    """Dispatch to the right chunker based on file extension."""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return chunk_pdf(filepath)
    return chunk_markdown(filepath)
