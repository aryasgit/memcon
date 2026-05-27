"""
memory/enricher.py
Background note enrichment — runs after a write returns, never blocks it.

What it adds:
  - **Git context** in frontmatter: {commit, branch, changed_files} for the
    project the user is currently working in.
  - **## See also** section appended to the note body: one-line summaries of
    each related note (read from their TL;DR or first prose line).

Entry point:
    enrich_async(filepath, kind, title, related) → returns immediately
        Spawns a daemon thread. All failures swallowed and logged to stderr.

The thread does:
    1. Re-read the file on disk.
    2. Probe git for project root + HEAD info.
    3. Read each related note's first prose line as its one-liner.
    4. Patch the YAML frontmatter (in-place) with git block.
    5. Append a `## See also` section if not already present.
    6. Re-ingest into Qdrant so the enriched content is searchable.
"""
from __future__ import annotations
import os, sys, subprocess, threading, re
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg


# ──────────────────────────────────────────────────────────────────────────────
# Public entry
# ──────────────────────────────────────────────────────────────────────────────

def enrich_async(
    filepath: str,
    *,
    kind: str,
    title: str,
    related: list[str] | None = None,
) -> None:
    """Spawn a daemon thread that enriches `filepath`. Returns immediately.

    Caller never sees errors — enrichment is opportunistic. The note is fully
    valid before enrichment runs, so partial failure is fine.
    """
    t = threading.Thread(
        target=_enrich_safe,
        args=(filepath, kind, title, list(related or [])),
        daemon=True,
        name=f"memcon-enrich-{Path(filepath).stem}",
    )
    t.start()


def _enrich_safe(filepath: str, kind: str, title: str, related: list[str]) -> None:
    try:
        _enrich(filepath, kind=kind, title=title, related=related)
    except Exception as e:
        print(f"[enricher] {filepath}: {e}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# Core enrichment
# ──────────────────────────────────────────────────────────────────────────────

def _enrich(filepath: str, *, kind: str, title: str, related: list[str]) -> None:
    path = Path(filepath)
    if not path.exists():
        return

    raw = path.read_text()
    fm, body = _split_frontmatter(raw)

    # ── Git block ───────────────────────────────────────────────────────────
    git = _git_context()
    if git:
        fm = _patch_frontmatter(fm, "git", _yaml_inline_dict(git))

    # ── See also ────────────────────────────────────────────────────────────
    see_also_body = _see_also_lines(related)
    if see_also_body:
        body = _ensure_section(body, "See also", see_also_body)

    new_raw = (fm + "\n\n" + body).rstrip() + "\n"
    if new_raw != raw:
        path.write_text(new_raw)
        # Re-ingest so the enriched chunks land in Qdrant too. Soft-fail.
        try:
            from ingestion.ingest import ingest_file
            ingest_file(str(path))
        except Exception as e:
            print(f"[enricher] re-ingest failed: {e}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# Git detection
# ──────────────────────────────────────────────────────────────────────────────

def _project_root_candidates() -> list[Path]:
    """Best-effort guesses for the user's project root.

    Order:
      1. $MEMCON_PROJECT_ROOT
      2. CWD (if not "/")
      3. vault's parent (most installs are vault-inside-project)
      4. vault itself (someone might use vault/ as the root)
    """
    out: list[Path] = []
    env_root = os.environ.get("MEMCON_PROJECT_ROOT")
    if env_root:
        out.append(Path(env_root).expanduser())
    cwd = Path.cwd()
    if str(cwd) not in ("/", ""):
        out.append(cwd)
    vault = Path(cfg('vault', 'path'))
    out.append(vault.parent)
    out.append(vault)
    return out


def _git_context() -> dict:
    """Probe git for commit/branch/recently-changed files. Returns {} if no
    git repo is found in any candidate project root."""
    for root in _project_root_candidates():
        if not root.exists():
            continue
        if not (root / ".git").exists():
            # `.git` could also be a file (worktrees) — accept either
            if not _git_works_in(root):
                continue
        commit = _git(root, "rev-parse", "--short", "HEAD")
        if not commit:
            continue
        branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD") or ""
        changed = _git(root, "diff", "--name-only", "HEAD~5..HEAD") or ""
        files = [f for f in changed.splitlines() if f.strip()][:10]
        return {
            "commit":        commit,
            "branch":        branch,
            "changed_files": files,
        }
    return {}


def _git(cwd: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except Exception:
        return None


def _git_works_in(cwd: Path) -> bool:
    return _git(cwd, "rev-parse", "--is-inside-work-tree") == "true"


# ──────────────────────────────────────────────────────────────────────────────
# See-also rendering
# ──────────────────────────────────────────────────────────────────────────────

def _see_also_lines(related: list[str]) -> str:
    """For each related note, find its file in the vault and pull the first
    line of prose under the H1 (or the TL;DR if present). Returns markdown
    bullet lines."""
    if not related:
        return ""
    vault = Path(cfg('vault', 'path'))
    out: list[str] = []
    for doc in related:
        oneliner = _first_oneliner_for(vault, doc)
        if oneliner:
            out.append(f"- [[{doc}]] — {oneliner}")
        else:
            out.append(f"- [[{doc}]]")
    return "\n".join(out)


def _first_oneliner_for(vault: Path, doc_name: str) -> str:
    """Find {vault}/**/{doc_name}.md and return the first non-trivial line of
    prose under the H1 heading (preferring the TL;DR section)."""
    matches = list(vault.rglob(f"{doc_name}.md"))
    if not matches:
        return ""
    try:
        text = matches[0].read_text(errors="ignore")
    except OSError:
        return ""

    # Strip frontmatter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]

    # Prefer the TL;DR section's first non-empty line
    tldr_m = re.search(r"##\s*TL;DR\s*\n+(.+?)(?=\n##|\Z)", text, re.DOTALL | re.IGNORECASE)
    if tldr_m:
        line = next((l.strip() for l in tldr_m.group(1).splitlines() if l.strip()), "")
        if line:
            return _truncate(line, 140)

    # Fall back: first prose line after H1
    h1_m = re.search(r"^#\s+.+\n+([^\n#].+)", text, re.MULTILINE)
    if h1_m:
        return _truncate(h1_m.group(1).strip(), 140)

    return ""


def _truncate(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


# ──────────────────────────────────────────────────────────────────────────────
# Frontmatter editing — tolerant of any YAML the writer emits
# ──────────────────────────────────────────────────────────────────────────────

def _split_frontmatter(raw: str) -> tuple[str, str]:
    """Split a markdown doc into (frontmatter_block, body). Frontmatter
    includes its leading and trailing '---' lines. If there's no frontmatter,
    returns ('---\\n---', raw)."""
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            return raw[: end + 4], raw[end + 4 :].lstrip("\n")
    return "---\n---", raw


def _patch_frontmatter(fm: str, key: str, value_line: str) -> str:
    """Insert-or-replace a top-level key in the frontmatter block.

    `value_line` is the *value* portion (right of ': ') — e.g. for git block
    we pass '{commit: ..., branch: ..., changed_files: [...]}'.
    """
    lines = fm.splitlines()
    # Find existing key (top-level only — no indentation)
    key_re = re.compile(rf"^{re.escape(key)}\s*:")
    replaced = False
    new_lines: list[str] = []
    for ln in lines:
        if not replaced and key_re.match(ln):
            new_lines.append(f"{key}: {value_line}")
            replaced = True
        else:
            new_lines.append(ln)
    if not replaced:
        # Insert before the closing '---'
        if new_lines and new_lines[-1].strip() == "---":
            new_lines.insert(-1, f"{key}: {value_line}")
        else:
            new_lines.append(f"{key}: {value_line}")
    return "\n".join(new_lines)


def _yaml_inline_dict(d: dict) -> str:
    """Render a dict as an inline YAML object."""
    parts = []
    for k, v in d.items():
        parts.append(f"{k}: {_yaml_value(v)}")
    return "{" + ", ".join(parts) + "}"


def _yaml_value(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_yaml_value(x) for x in v) + "]"
    s = str(v)
    if any(c in s for c in ":#[]{},&*!|>'\"%@`") or " " in s:
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s or '""'


# ──────────────────────────────────────────────────────────────────────────────
# Body editing — ensure section exists
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_section(body: str, section_title: str, section_body: str) -> str:
    """If `body` already has a `## {section_title}` heading, replace its
    contents. Otherwise append a fresh section."""
    head_re = re.compile(rf"^##\s+{re.escape(section_title)}\s*$", re.MULTILINE)
    m = head_re.search(body)
    if m:
        # Replace contents up to next heading (or end of file)
        start = m.end()
        next_head = re.search(r"^##\s+", body[start:], re.MULTILINE)
        end = start + next_head.start() if next_head else len(body)
        return body[: start].rstrip() + "\n\n" + section_body.rstrip() + "\n\n" + body[end:].lstrip()
    # Append fresh section
    return body.rstrip() + f"\n\n## {section_title}\n\n{section_body.rstrip()}\n"
