#!/usr/bin/env python3
"""
scripts/migrate_to_v3_1.py

Backfill existing vault notes into the v3.1 schema.

What it does, per note:
  1. Parse the existing frontmatter + body.
  2. Skip if the note already has `type:` in frontmatter (already migrated).
  3. Infer the kind from the folder name (or fall back to `memory_type`).
  4. Lift `## Heading` sections into the v3.1 field names for that kind.
  5. Compose a `tldr` if missing (first prose line of the first non-empty section).
  6. Preserve the original body verbatim under `## Context` so the embedder has
     real prose to work with.
  7. Extract entities — using the local LLM if available, regex fallback if not.
  8. Build new rich frontmatter via templates.make_frontmatter().
  9. Rewrite the file (after backing up the original).
 10. Update the entity index.
 11. Re-ingest the file into Qdrant.

CLI:
    python3 -m scripts.migrate_to_v3_1 [--vault PATH] [--dry-run] [--no-llm]
                                       [--limit N] [--no-backup] [--reingest]
                                       [--verbose]

By default it runs against the vault from memcon.config.yaml, backs originals
up to `{vault}/_backup_v3.1/`, and uses the local LLM if Ollama responds on
the first probe.

It's safe to re-run — already-migrated notes are detected and skipped.
"""
from __future__ import annotations
import argparse, os, sys, re, shutil
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg
from memory.templates import (
    ALL_KINDS, FOLDER_FOR, SECTIONS_FOR,
    make_frontmatter, render_body, render_frontmatter, _slug,
)


# ──────────────────────────────────────────────────────────────────────────────
# Folder → kind inference (reverse of templates.FOLDER_FOR + legacy folders)
# ──────────────────────────────────────────────────────────────────────────────

KIND_FROM_FOLDER: dict[str, str] = {
    # New folders introduced in v3.1
    "debugging":     "debug",
    "decisions":     "decision",
    "experiments":   "experiment",
    "concepts":      "concept",
    "references":    "reference",
    "meetings":      "meeting",
    "breakthroughs": "breakthrough",
    "sessions":      "session",
}

# Old memory_type values → new kind (used when folder doesn't tell us)
KIND_FROM_MEMORY_TYPE: dict[str, str] = {
    "causal":     "decision",
    "episodic":   "debug",
    "semantic":   "concept",
    "procedural": "reference",
}

# Per-kind: which old `## Headings` (case-insensitive) map to which v3.1 fields.
SECTION_MAP: dict[str, dict[str, str]] = {
    "debug": {
        "tldr":          "tldr",
        "summary":       "tldr",
        "symptom":       "symptom",
        "symptoms":      "symptom",
        "investigation": "investigation",
        "diagnosis":     "investigation",
        "cause":         "cause",
        "root cause":    "cause",
        "fix":           "fix",
        "fix applied":   "fix",
        "solution":      "fix",
        "verification":  "verification",
        "validation":    "verification",
    },
    "decision": {
        "tldr":         "tldr",
        "summary":      "tldr",
        "context":      "context",
        "background":   "context",
        "options":      "options",
        "options considered": "options",
        "alternatives": "options",
        "decision":     "decision",
        "reasoning":    "reasoning",
        "rationale":    "reasoning",
        "consequences": "consequences",
        "trade-offs":   "consequences",
        "tradeoffs":    "consequences",
    },
    "experiment": {
        "tldr":       "tldr",
        "summary":    "tldr",
        "hypothesis": "hypothesis",
        "setup":      "setup",
        "method":     "setup",
        "result":     "result",
        "results":    "result",
        "conclusion": "conclusion",
        "takeaway":   "conclusion",
    },
    "concept": {
        "tldr":           "tldr",
        "summary":        "tldr",
        "definition":     "definition",
        "what it is":     "definition",
        "why it matters": "why",
        "why":            "why",
        "example":        "example",
        "examples":       "example",
        "pitfalls":       "pitfalls",
        "gotchas":        "pitfalls",
    },
    "reference": {
        "tldr":         "tldr",
        "summary":      "summary",
        "what this is": "summary",
        "key points":   "key_points",
        "notes":        "notes",
        "source":       "source",
        "url":          "source",
    },
    "meeting": {
        "tldr":         "tldr",
        "summary":      "tldr",
        "attendees":    "attendees",
        "participants": "attendees",
        "notes":        "notes",
        "decisions":    "decisions",
        "action items": "actions",
        "actions":      "actions",
        "todos":        "actions",
    },
    "breakthrough": {
        "tldr":        "tldr",
        "summary":     "tldr",
        "background":  "background",
        "insight":     "insight",
        "the insight": "insight",
        "implication": "implication",
        "impact":      "implication",
        "next steps":  "next_steps",
        "next":        "next_steps",
    },
    "session": {
        "tldr":       "tldr",
        "summary":    "tldr",
        "worked on":  "worked_on",
        "solved":     "solved",
        "decided":    "decided",
        "open items": "open_items",
        "open":       "open_items",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Frontmatter parse (tolerant — no PyYAML dependency)
# ──────────────────────────────────────────────────────────────────────────────

def _split_frontmatter(raw: str) -> tuple[dict, str]:
    """Return (meta_dict, body). Body excludes the frontmatter block."""
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    fm_block = raw[4:end]  # skip leading "---\n"
    body = raw[end + 4:].lstrip("\n")
    return _parse_simple_yaml(fm_block), body


def _parse_simple_yaml(block: str) -> dict:
    """Parse a flat YAML block well enough for our frontmatter needs.

    Handles: scalars, inline lists [a, b], inline dicts {k: v}, nested
    indented sub-dicts. Doesn't try to be a full YAML parser — this is what
    our writer emits, and we round-trip it.
    """
    out: dict = {}
    current_key: str | None = None
    current_sub: dict | None = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # Sub-key under a current nested dict
        if line.startswith("  ") and current_sub is not None:
            sub_line = line.strip()
            if ":" in sub_line:
                k, _, v = sub_line.partition(":")
                current_sub[k.strip()] = _parse_value(v.strip())
            continue
        # Top-level
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        current_key = k
        if v == "":
            # Likely a nested dict on subsequent lines
            current_sub = {}
            out[k] = current_sub
        else:
            current_sub = None
            out[k] = _parse_value(v)
    return out


def _parse_value(v: str):
    """Parse a YAML scalar / inline list / inline dict / quoted string."""
    if not v:
        return ""
    if v[0] == '"' and v[-1] == '"':
        return v[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if v[0] == "'" and v[-1] == "'":
        return v[1:-1]
    if v[0] == "[" and v[-1] == "]":
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_parse_value(x.strip()) for x in _split_csv(inner)]
    if v[0] == "{" and v[-1] == "}":
        inner = v[1:-1].strip()
        if not inner:
            return {}
        out: dict = {}
        for kv in _split_csv(inner):
            if ":" in kv:
                k, _, vv = kv.partition(":")
                out[k.strip()] = _parse_value(vv.strip())
        return out
    if v.lower() == "true":  return True
    if v.lower() == "false": return False
    try:
        if "." not in v:
            return int(v)
        return float(v)
    except ValueError:
        return v


def _split_csv(s: str) -> list[str]:
    """Split on commas, respecting brackets/braces/quotes."""
    out: list[str] = []
    depth = 0
    in_quote: str | None = None
    buf: list[str] = []
    for ch in s:
        if in_quote:
            buf.append(ch)
            if ch == in_quote and (not buf or buf[-2:-1] != ["\\"]):
                in_quote = None
            continue
        if ch in '"\'':
            in_quote = ch
            buf.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Body parsing — split on H2 (## ) sections
# ──────────────────────────────────────────────────────────────────────────────

H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def _parse_sections(body: str) -> tuple[str, dict[str, str]]:
    """Return (h1_title, {section_title_lc: section_body}).

    h1_title is the `# Title` line if present (else empty). Section bodies
    are stripped of trailing whitespace, leading separators kept.
    """
    h1 = ""
    h1_m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    if h1_m:
        h1 = h1_m.group(1).strip()

    sections: dict[str, str] = {}
    matches = list(H2_RE.finditer(body))
    for i, m in enumerate(matches):
        title = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        if content:
            sections[title] = content
    return h1, sections


# ──────────────────────────────────────────────────────────────────────────────
# Field lifting
# ──────────────────────────────────────────────────────────────────────────────

def _lift_fields(kind: str, sections: dict[str, str]) -> dict[str, str]:
    """Map old `## Heading` content into the v3.1 field names for `kind`."""
    mapping = SECTION_MAP.get(kind, {})
    fields: dict[str, str] = {}
    for old_heading, content in sections.items():
        target = mapping.get(old_heading)
        if target and target not in fields:
            fields[target] = content
    return fields


def _derive_tldr(fields: dict[str, str], kind: str, body: str) -> str:
    """If no TL;DR was lifted, derive one from the first non-trivial content.

    Strategy:
      1. If the kind's "primary" field has content (e.g. cause for debug,
         decision for decision, insight for breakthrough), use its first
         sentence.
      2. Else take the first non-empty line of the body.
    Truncate to 200 chars.
    """
    if fields.get("tldr"):
        return fields["tldr"]
    primary = {
        "debug":        ["cause", "fix", "symptom"],
        "decision":     ["decision", "reasoning"],
        "experiment":   ["conclusion", "result", "hypothesis"],
        "concept":      ["definition", "why"],
        "reference":    ["summary", "key_points"],
        "meeting":      ["decisions", "notes"],
        "breakthrough": ["insight", "implication"],
        "session":      ["worked_on", "solved"],
    }.get(kind, ["tldr"])
    for f in primary:
        v = fields.get(f, "").strip()
        if v:
            return _truncate(_first_sentence(v), 200)
    # Last-resort: first prose line of body
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "-", "*", ">")) and not line.startswith("---"):
            return _truncate(line, 200)
    return ""


def _first_sentence(s: str) -> str:
    """Naively grab the first sentence (up to first `. ` or newline)."""
    m = re.search(r"[.!?](\s|$)|\n", s)
    if m:
        return s[: m.end()].strip().rstrip(".!?\n")
    return s.strip()


def _truncate(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


# ──────────────────────────────────────────────────────────────────────────────
# Entity extraction — LLM if available, regex fallback otherwise
# ──────────────────────────────────────────────────────────────────────────────

_ENTITY_PATTERNS = {
    "files":    re.compile(r"\b([\w./\\-]+\.[a-zA-Z]{1,8})\b"),
    "urls":     re.compile(r"https?://[^\s)>\]]+"),
    "errors":   re.compile(r"\b([A-Z][A-Za-z]*(?:Error|Exception|Warning))\b"),
    "symbols":  re.compile(r"\b([A-Z][A-Za-z0-9]+(?:::|\.)[A-Za-z_][A-Za-z0-9_]*)"),
    "packages": re.compile(r"`([a-z][a-z0-9._-]{2,})`"),
}


def _regex_entities(text: str) -> dict[str, list[str]]:
    """Cheap regex-based entity extraction. Used when --no-llm is set or
    when Ollama is unreachable."""
    out: dict[str, list[str]] = {k: [] for k in ("files", "symbols", "errors", "packages", "urls", "concepts")}
    for kind, pat in _ENTITY_PATTERNS.items():
        seen: set[str] = set()
        for m in pat.finditer(text):
            ent = m.group(1) if pat.groups else m.group(0)
            ent = ent.strip()
            if not ent or ent.lower() in seen:
                continue
            seen.add(ent.lower())
            out[kind].append(ent)
        out[kind] = out[kind][:25]
    return out


def _llm_available(timeout: float = 2.0) -> bool:
    """Quick probe — is the configured LLM responding?"""
    try:
        import urllib.request
        base = cfg('llm', 'base_url').rstrip("/").removesuffix("/v1")
        req = urllib.request.Request(f"{base}/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _extract_entities(text: str, use_llm: bool) -> dict[str, list[str]]:
    if use_llm:
        try:
            from memory.extractor import extract_entities
            return extract_entities(text)
        except Exception as e:
            print(f"  ⚠ LLM entity extraction failed ({e}); falling back to regex", file=sys.stderr)
    return _regex_entities(text)


# ──────────────────────────────────────────────────────────────────────────────
# Kind inference
# ──────────────────────────────────────────────────────────────────────────────

def _infer_kind(path: Path, vault: Path, old_meta: dict) -> str:
    """Pick the v3.1 kind for a legacy note."""
    try:
        rel = path.relative_to(vault)
    except ValueError:
        rel = path
    parts = [p for p in rel.parts[:-1]]  # parent folders only
    for part in parts:
        k = KIND_FROM_FOLDER.get(part.lower())
        if k:
            return k
    # Fall back to old memory_type
    mt = (old_meta.get("memory_type") or "").lower()
    if mt in KIND_FROM_MEMORY_TYPE:
        return KIND_FROM_MEMORY_TYPE[mt]
    return "debug"


def _already_migrated(meta: dict) -> bool:
    """A note is in v3.1 shape iff it has a top-level `type:` field whose
    value is one of ALL_KINDS."""
    t = meta.get("type")
    return isinstance(t, str) and t in ALL_KINDS


# ──────────────────────────────────────────────────────────────────────────────
# Per-file migration
# ──────────────────────────────────────────────────────────────────────────────

def migrate_file(path: Path, vault: Path, *, dry_run: bool, use_llm: bool,
                 backup_dir: Path | None, reingest: bool) -> dict:
    """Migrate one .md file. Returns a result dict for the summary."""
    try:
        raw = path.read_text(errors="ignore")
    except OSError as e:
        return {"action": "error", "path": str(path), "error": f"read: {e}"}

    old_meta, body = _split_frontmatter(raw)

    if _already_migrated(old_meta):
        return {"action": "skip", "reason": "already in v3.1", "path": str(path)}

    kind = _infer_kind(path, vault, old_meta)
    h1_title, sections = _parse_sections(body)
    fields = _lift_fields(kind, sections)
    fields["tldr"] = _derive_tldr(fields, kind, body)
    # context_raw should preserve newlines / formatting — don't collapse whitespace.
    fields["context_raw"] = body.strip()[:1500]

    # Title — prefer existing H1, else filename, else "(untitled)"
    title = h1_title or path.stem.replace("_", " ")

    # Subsystem — keep old value if present, otherwise "unknown"
    subsystem = old_meta.get("subsystem") or "unknown"
    if isinstance(subsystem, str):
        # New schema accepts both str and list — leave as str if single
        pass

    # Tags — pull from old frontmatter, normalize to list[str]
    tags = old_meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip().lstrip("#") for t in re.split(r"[,\s]+", tags) if t.strip()]
    tags = [str(t).strip().lstrip("#").lower() for t in tags][:5]

    # Status (debug only). Look in frontmatter first, then `## Status` body section.
    status = ""
    if kind == "debug":
        status = (old_meta.get("status") or sections.get("status", "")).strip().splitlines()[0].lower() if (
            old_meta.get("status") or sections.get("status")
        ) else ""
        # Normalise legacy values
        if status in ("done", "resolved", "closed"):
            status = "fixed"

    # Entities — extract from full original body
    entities = _extract_entities(body, use_llm=use_llm)

    # Build new frontmatter
    date_prefix = ""
    if isinstance(old_meta.get("date"), str):
        date_prefix = old_meta["date"]
    elif old_meta.get("created"):
        date_prefix = str(old_meta["created"])[:10]
    else:
        date_prefix = datetime.now().strftime("%Y-%m-%d")
    note_id = f"{date_prefix}_{_slug(title)}"

    meta = make_frontmatter(
        kind=kind,
        title=title,
        note_id=note_id,
        subsystem=subsystem,
        tags=tags,
        status=status,
        confidence="medium",  # we didn't extract it; safe middle
        entities=entities,
        git={},               # not detectable retroactively
        linked=[],
        project=str(old_meta.get("project") or _project_name()),
    )
    # Preserve original created date if present
    if old_meta.get("date") and isinstance(old_meta["date"], str):
        meta["created"] = old_meta["date"] + ("T00:00:00Z" if "T" not in old_meta["date"] else "")
    meta["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_content = (
        render_frontmatter(meta)
        + "\n\n"
        + render_body(kind, title, fields)
    )

    result = {
        "action":    "migrate",
        "kind":      kind,
        "path":      str(path),
        "title":     title,
        "entities":  sum(len(v) for v in entities.values()),
    }

    if dry_run:
        return result

    # Back up the original
    if backup_dir is not None:
        try:
            rel = path.relative_to(vault)
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
        except Exception as e:
            return {"action": "error", "path": str(path), "error": f"backup: {e}"}

    # Write the new content
    try:
        path.write_text(new_content)
    except OSError as e:
        return {"action": "error", "path": str(path), "error": f"write: {e}"}

    # Update entity index
    try:
        from memory.entity_index import index_note
        index_note(doc_name=path.stem, entities=entities, path=str(path))
    except Exception as e:
        result["entity_index_warning"] = str(e)

    # Re-ingest into Qdrant so the new context surfaces semantically
    if reingest:
        try:
            from ingestion.ingest import ingest_file
            ingest_file(str(path))
        except Exception as e:
            result["reingest_warning"] = str(e)

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────────────────────────

def _project_name() -> str:
    try:
        return cfg('project', 'name')
    except Exception:
        return ""


def walk_vault(vault: Path, skip: set[str]) -> list[Path]:
    """Yield every .md file under vault, skipping configured directories +
    the backup folder we create ourselves."""
    out: list[Path] = []
    for p in vault.rglob("*.md"):
        try:
            rel = p.relative_to(vault)
        except ValueError:
            continue
        if any(part in skip or part.startswith("_backup") or part == ".memcon" for part in rel.parts):
            continue
        out.append(p)
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Backfill old vault notes into v3.1 schema.")
    ap.add_argument("--vault", default=None, help="Vault path (default: from memcon.config.yaml)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change; don't write")
    ap.add_argument("--no-llm", action="store_true", help="Skip LLM entity extraction; use regex only")
    ap.add_argument("--limit", type=int, default=0, help="Only migrate the first N files (0 = no limit)")
    ap.add_argument("--no-backup", action="store_true", help="Skip backing up originals (dangerous)")
    ap.add_argument("--reingest", action="store_true", help="Re-ingest migrated notes into Qdrant")
    ap.add_argument("--verbose", "-v", action="store_true", help="Print one line per file")
    args = ap.parse_args(argv)

    vault = Path(args.vault or cfg('vault', 'path')).expanduser().resolve()
    if not vault.exists():
        print(f"✗ Vault not found: {vault}", file=sys.stderr)
        return 2

    skip = set(cfg('vault', 'skip_dirs') or [])
    files = walk_vault(vault, skip)
    if args.limit:
        files = files[: args.limit]

    use_llm = (not args.no_llm) and _llm_available()
    backup_dir: Path | None = None
    if not args.no_backup and not args.dry_run:
        backup_dir = vault / f"_backup_v3.1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)

    print(f"Vault:        {vault}")
    print(f"Files found:  {len(files)}")
    print(f"LLM:          {'enabled' if use_llm else 'disabled (regex-only fallback)'}")
    print(f"Backup dir:   {backup_dir or '(none)'}")
    print(f"Mode:         {'DRY-RUN' if args.dry_run else 'WRITE'}")
    print()

    counts = Counter()
    kind_counts = Counter()
    errors: list[dict] = []

    for i, p in enumerate(files, 1):
        result = migrate_file(
            p, vault,
            dry_run=args.dry_run,
            use_llm=use_llm,
            backup_dir=backup_dir,
            reingest=args.reingest,
        )
        counts[result["action"]] += 1
        if result["action"] == "migrate":
            kind_counts[result["kind"]] += 1
        if result["action"] == "error":
            errors.append(result)
        if args.verbose:
            tag = {"migrate": "→", "skip": "·", "error": "✗"}.get(result["action"], "?")
            sub = ""
            if result["action"] == "migrate":
                sub = f"  [{result['kind']}, {result.get('entities', 0)} entities]"
            elif result["action"] == "skip":
                sub = f"  ({result.get('reason', '')})"
            elif result["action"] == "error":
                sub = f"  {result.get('error', '')}"
            print(f"  {tag} {p.relative_to(vault)}{sub}")

    print()
    print("─" * 60)
    print(f"Migrated:  {counts['migrate']}")
    if kind_counts:
        kinds_str = ", ".join(f"{n} {k}" for k, n in kind_counts.most_common())
        print(f"  by kind: {kinds_str}")
    print(f"Skipped:   {counts['skip']} (already in v3.1)")
    print(f"Errored:   {counts['error']}")
    if errors and not args.verbose:
        print("\nFirst few errors:")
        for e in errors[:5]:
            print(f"  ✗ {e['path']}: {e['error']}")
    if backup_dir and counts['migrate'] > 0:
        print(f"\nOriginals backed up to: {backup_dir}")
        print("If anything looks wrong, restore with:")
        print(f"  cp -r {backup_dir}/* {vault}/ && rm -rf {backup_dir}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
