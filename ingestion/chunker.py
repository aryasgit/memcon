import frontmatter
import re
from pathlib import Path

def chunk_markdown(filepath: str, chunk_size: int = 400) -> list[dict]:
    try:
        with open(filepath) as f:
            post = frontmatter.load(f)
    except Exception as e:
        print(f"[chunker] Skipping {filepath}: {e}")
        return []

    text = post.content
    meta = dict(post.metadata)
    filename = Path(filepath).stem
    sections = re.split(r'\n(?=#{1,3} )', text)

    chunks = []
    for i, section in enumerate(sections):
        words = section.split()
        for j in range(0, len(words), chunk_size):
            chunk_text = ' '.join(words[j:j+chunk_size])
            if len(chunk_text.strip()) < 30:
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
