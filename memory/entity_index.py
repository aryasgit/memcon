"""
memory/entity_index.py
SQLite-backed inverted index of entities → notes.

The vector store gives fuzzy semantic recall. This module gives the *exact*
recall side — when someone mentions a file name, function name, or error
string, every note that references it shows up regardless of cosine distance.

Storage: {vault}/.memcon/entities.db (auto-created)

Schema:
    CREATE TABLE entities (
        entity     TEXT,                  -- the raw string, case-preserved
        entity_lc  TEXT,                  -- lowercase for fast lookup
        kind       TEXT,                  -- files | symbols | errors | packages | urls | concepts
        doc_name   TEXT,                  -- slug, matches Qdrant payload doc_name
        path       TEXT,                  -- absolute file path
        last_seen  TEXT,                  -- ISO timestamp
        PRIMARY KEY (entity_lc, kind, doc_name)
    );
    CREATE INDEX idx_entities_lc ON entities(entity_lc);
    CREATE INDEX idx_entities_doc ON entities(doc_name);

Public API:
    index_note(doc_name, entities, path)   — replace all entries for that doc
    clear_doc(doc_name)                    — remove all entries for that doc
    lookup(query, limit=10)                — [(doc_name, entity, kind, matched_token), ...]
    stats()                                — {n_entities, n_docs, by_kind}
"""
from __future__ import annotations
import os, sys, sqlite3, re
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg


# ──────────────────────────────────────────────────────────────────────────────
# Database path + connection
# ──────────────────────────────────────────────────────────────────────────────

def _db_path() -> Path:
    """{vault}/.memcon/entities.db — co-located with vault so multi-project use
    via MEMCON_VAULT just works."""
    vault = Path(cfg('vault', 'path'))
    db_dir = vault / ".memcon"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "entities.db"


def _connect() -> sqlite3.Connection:
    # Concurrency-safe by default: memcon often runs in TWO clients at once
    # (Claude Desktop + Code) sharing this one DB. WAL lets readers and a writer
    # coexist; busy_timeout makes a second writer WAIT up to 5s for the lock
    # instead of failing instantly with "database is locked".
    conn = sqlite3.connect(str(_db_path()), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            entity     TEXT NOT NULL,
            entity_lc  TEXT NOT NULL,
            kind       TEXT NOT NULL,
            doc_name   TEXT NOT NULL,
            path       TEXT,
            last_seen  TEXT NOT NULL,
            PRIMARY KEY (entity_lc, kind, doc_name)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_lc  ON entities(entity_lc)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_doc ON entities(doc_name)")
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# Write path
# ──────────────────────────────────────────────────────────────────────────────

def clear_doc(doc_name: str) -> int:
    """Remove every entity entry associated with a doc. Returns rows deleted."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM entities WHERE doc_name = ?", (doc_name,))
        return cur.rowcount


def index_note(*, doc_name: str, entities: dict, path: str = "") -> int:
    """Replace all entries for `doc_name` with the new entity dict.

    `entities` is the dict produced by extractor.extract_entities() — keyed by
    category, with list values.

    Returns the number of rows inserted.
    """
    if not entities:
        clear_doc(doc_name)
        return 0

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows: list[tuple[str, str, str, str, str, str]] = []
    for kind, values in entities.items():
        if not values:
            continue
        for v in values:
            if not isinstance(v, str):
                continue
            v = v.strip()
            if not v:
                continue
            rows.append((v, v.lower(), kind, doc_name, path, now))

    with _connect() as conn:
        conn.execute("DELETE FROM entities WHERE doc_name = ?", (doc_name,))
        conn.executemany(
            "INSERT OR REPLACE INTO entities "
            "(entity, entity_lc, kind, doc_name, path, last_seen) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        return len(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Read path — lookup
# ──────────────────────────────────────────────────────────────────────────────

# Tokens that should never match as entities (too generic).
_STOPWORDS = {
    "the","a","an","and","or","but","if","then","else","of","in","on","at","to",
    "for","with","without","by","as","is","are","was","were","be","being","been",
    "do","does","did","this","that","these","those","it","its","what","why","how",
    "when","where","which","who","why","whom","whose","not","no","yes","i","me",
    "my","mine","you","your","yours","we","us","our","ours","they","them","their",
    "from","into","about","after","before","over","under","up","down","out","off",
}


def _candidate_tokens(query: str) -> list[str]:
    """Pull entity-shaped substrings out of a freeform query string.

    We look for things engineers actually use in queries:
      - dotted-path tokens     (foo.bar.baz, file.cpp, file.ts)
      - slashed paths          (src/auth/jwt.ts, drivers/servo.cpp)
      - CamelCase / snake_case (ServoController, set_torque)
      - quoted strings         ("I2C OSError")
      - http(s) URLs
      - error-code-shaped      (errno=121, OSError, E_ACCES)
      - everything else        — whitespace-split, filtered through stopwords
    """
    if not query:
        return []

    out: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = s.strip().strip(",.!?;:")
        if not s or s.lower() in _STOPWORDS or s.lower() in seen:
            return
        if len(s) < 3 and not s.isupper():
            return
        seen.add(s.lower())
        out.append(s)

    # Quoted strings — multi-word entities
    for m in re.finditer(r'"([^"]{2,})"|\'([^\']{2,})\'|`([^`]{2,})`', query):
        add(m.group(1) or m.group(2) or m.group(3))

    # URLs
    for m in re.finditer(r'https?://[^\s]+', query):
        add(m.group(0))

    # Path-like (slash- or backslash-separated, with extension)
    for m in re.finditer(r'[\w./\\-]+[/\\][\w./\\-]+|\w+\.\w{1,8}', query):
        add(m.group(0))

    # CamelCase, snake_case, kebab-case tokens
    for m in re.finditer(r'[A-Za-z][A-Za-z0-9_\-]{2,}', query):
        tok = m.group(0)
        # Skip pure stopwords; keep CamelCase even if it'd be short
        if tok.lower() in _STOPWORDS and not (tok != tok.lower() and tok != tok.upper()):
            continue
        add(tok)

    # Numbers/codes like errno=121 → keep just the right side too
    for m in re.finditer(r'\b\d{3,}\b', query):
        add(m.group(0))

    return out


def lookup(query: str, *, limit: int = 10) -> list[dict]:
    """Find notes whose entities match tokens in `query`.

    Matching: case-insensitive. An entity matches if (a) its lowercased form
    equals a token, OR (b) the token is a substring of the entity, OR (c) the
    entity is a substring of the token (file.cpp ⊂ drivers/file.cpp).

    Returns up to `limit` hits, deduped per (doc_name, entity), sorted by
    descending match-score (number of distinct token matches in that doc).
    """
    tokens = _candidate_tokens(query)
    if not tokens:
        return []

    # Build a single query: SELECT ... WHERE entity_lc IN (...) OR LIKE matches
    # For LIKEs, do a separate UNION ALL — keeps the SQL readable.
    placeholders = ",".join(["?"] * len(tokens))
    tokens_lc = [t.lower() for t in tokens]

    rows: list[tuple] = []
    with _connect() as conn:
        # Exact (case-insensitive) hits
        cur = conn.execute(
            f"SELECT entity, kind, doc_name, path, entity_lc "
            f"FROM entities WHERE entity_lc IN ({placeholders})",
            tokens_lc,
        )
        rows.extend(cur.fetchall())

        # Substring hits — entity contains token OR token contains entity
        for tok in tokens_lc:
            if len(tok) < 4:
                continue  # too generic
            like = f"%{tok}%"
            cur = conn.execute(
                "SELECT entity, kind, doc_name, path, entity_lc FROM entities "
                "WHERE entity_lc LIKE ? OR ? LIKE '%' || entity_lc || '%'",
                (like, tok),
            )
            rows.extend(cur.fetchall())

    # Score by distinct tokens matched per doc; entity matches give 1 point each.
    by_doc: dict[str, dict] = {}
    for entity, kind, doc_name, path, entity_lc in rows:
        doc = by_doc.setdefault(doc_name, {
            "doc_name": doc_name,
            "path":     path,
            "matches":  [],
            "score":    0,
        })
        # Find which token caused the hit (best-effort)
        match_tok = next((t for t in tokens_lc if t == entity_lc or t in entity_lc or entity_lc in t), entity_lc)
        # Dedupe matches per (entity, kind, token)
        key = (entity, kind, match_tok)
        if key not in {(m["entity"], m["kind"], m["token"]) for m in doc["matches"]}:
            doc["matches"].append({"entity": entity, "kind": kind, "token": match_tok})
            doc["score"] += 1

    ranked = sorted(by_doc.values(), key=lambda d: (-d["score"], d["doc_name"]))
    return ranked[:limit]


# ──────────────────────────────────────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Return aggregate counts. Useful for memcon_stats and health checks."""
    with _connect() as conn:
        n_entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        n_docs = conn.execute("SELECT COUNT(DISTINCT doc_name) FROM entities").fetchone()[0]
        by_kind = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM entities GROUP BY kind"
        ).fetchall())
    return {
        "n_entities": n_entities,
        "n_docs":     n_docs,
        "by_kind":    by_kind,
        "db_path":    str(_db_path()),
    }
