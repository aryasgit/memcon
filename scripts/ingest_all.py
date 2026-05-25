import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pathlib import Path
from ingestion.ingest import ingest_file

VAULT = Path("vault")
SKIP_DIRS = {"_templates"}

total = 0
files = [
    f for f in VAULT.rglob("*.md")
    if not any(part in SKIP_DIRS for part in f.parts)
]
print(f"[ingest_all] Found {len(files)} markdown files")
for md in files:
    total += ingest_file(str(md))
print(f"\n✅ Done. Total chunks ingested: {total}")
