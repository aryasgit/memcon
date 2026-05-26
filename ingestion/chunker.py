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
