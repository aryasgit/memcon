import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from ingestion.ingest import ingest_file
from config import cfg

VAULT = Path(cfg('vault','path'))
SKIP = set(cfg('vault','skip_dirs'))

total = 0
files = [
    f for f in VAULT.rglob("*")
    if f.is_file()
    and f.suffix.lower() in {".md", ".pdf"}
    and not any(part in SKIP for part in f.parts)
]
print(f"[ingest_all] Found {len(files)} files ({sum(1 for f in files if f.suffix.lower()=='.md')} md, {sum(1 for f in files if f.suffix.lower()=='.pdf')} pdf)")
for f in files:
    total += ingest_file(str(f))
print(f"\n✅ Done. Total chunks ingested: {total}")
