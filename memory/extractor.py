"""
memory/extractor.py
Multi-pass local-LLM extraction pipeline.

Single public entry point:
    extract(text, hint="auto", run_critique=False) → dict

Internally runs four passes against the configured local LLM:

    1. classify_type(text)       → picks one of ALL_KINDS
    2. extract_structure(text)   → fills type-specific fields + TL;DR
    3. extract_entities(text)    → files / symbols / errors / packages / urls / concepts
    4. (optional) self_critique  → "what did you miss?" pass

Each pass uses Ollama JSON mode (response_format={"type":"json_object"}) so the
output is reliably parseable even from small models like qwen-coder-7b.

The result dict is shaped to feed directly into writer.log_universal().
"""
from __future__ import annotations
import os, sys, json, re
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg
from memory.templates import ALL_KINDS, SECTIONS_FOR


# ──────────────────────────────────────────────────────────────────────────────
# LLM client (lazy, shared across passes)
# ──────────────────────────────────────────────────────────────────────────────

_client = None


def _get_llm():
    """The shared OPTIONAL local-LLM client (see memory.llm). Callers gate on
    memory.llm.is_available() first — without a local LLM, extraction is skipped
    and the raw captured note stands."""
    from memory.llm import get_client
    return get_client()


def _ask_json(prompt: str, *, max_tokens: int | None = None, temperature: float = 0.1) -> dict:
    """Run one LLM call and return the parsed JSON dict.

    Tries JSON mode first (most reliable on models that support it — qwen2.5-coder,
    llama3.x). If that errors (older Ollama, a model without JSON-mode support,
    or any transport hiccup) OR returns unparseable output, it retries WITHOUT
    `response_format`, relying on _safe_json()'s brace-extraction to recover a
    JSON object from a plain completion.

    On total failure returns {} so the caller can fall back gracefully — the
    extractor must never raise into a write path.
    """
    mt = max_tokens or cfg('llm', 'max_tokens')
    model = cfg('llm', 'model')

    for use_json_mode in (True, False):
        try:
            llm = _get_llm()
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": mt,
                "temperature": temperature,
                # Hard ceiling per call so a hung/overloaded local model can't
                # wedge a background extraction thread forever.
                "timeout": 120,
            }
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = llm.chat.completions.create(**kwargs)
            parsed = _safe_json(resp.choices[0].message.content)
            if parsed:
                return parsed
            # Empty parse in JSON mode → fall through and retry in plain mode.
        except Exception as e:
            mode = "json" if use_json_mode else "plain"
            print(f"[extractor] LLM call failed (mode={mode}): {e}", file=sys.stderr)
            continue
    return {}


def _safe_json(raw: str) -> dict:
    """Parse a JSON object from the LLM's response, tolerating leading/trailing
    text and code fences. Returns {} on failure."""
    if not raw:
        return {}
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.IGNORECASE | re.MULTILINE).strip()
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        # Trim trailing junk a model sometimes appends after the closing brace
        snippet = m.group(0)
        for end in range(len(snippet), 0, -1):
            try:
                return json.loads(snippet[:end])
            except json.JSONDecodeError:
                continue
        return {}


# ──────────────────────────────────────────────────────────────────────────────
# Pass 1 — classify kind
# ──────────────────────────────────────────────────────────────────────────────

_CLASSIFY_CHEAT_SHEET = """\
  debug         — something broke and we (mostly) fixed it. has symptom + cause + fix.
  decision      — we made a non-obvious choice. has rationale + alternatives.
  experiment    — we tried something to learn. has hypothesis + result.
  concept       — a definition / mental model / "what is X".
  reference     — captured docs / API / external resource for later.
  meeting       — sync / discussion. has attendees + decisions + actions.
  breakthrough  — an "aha" insight that unlocks future work.
  session       — end-of-day or end-of-session roll-up of multiple things.
"""


def classify_type(text: str) -> tuple[str, str]:
    """Pick the best note kind for this input. Returns (kind, reason)."""
    prompt = f"""Pick the single best note KIND for this content. Choose from:

{_CLASSIFY_CHEAT_SHEET}

Reply with JSON only:
{{"kind": "<one of: {', '.join(ALL_KINDS)}>", "reason": "one short sentence"}}

CONTENT:
\"\"\"{text}\"\"\"
"""
    data = _ask_json(prompt, max_tokens=120, temperature=0.0)
    kind = (data.get("kind") or "").strip().lower()
    if kind not in ALL_KINDS:
        kind = "debug"
    return kind, data.get("reason", "")


# ──────────────────────────────────────────────────────────────────────────────
# Pass 2 — extract structure (per-kind schema)
# ──────────────────────────────────────────────────────────────────────────────

def _schema_hint_for(kind: str) -> str:
    """Build a per-kind JSON-schema hint for the extractor prompt."""
    specs = SECTIONS_FOR.get(kind, SECTIONS_FOR["debug"])
    field_lines = []
    for section_title, field_name, _fallback in specs:
        field_lines.append(f'  "{field_name}": "...",  // {section_title}')
    return "{\n" + "\n".join(field_lines) + "\n}"


def extract_structure(text: str, kind: str, *, valid_subsystems: list[str] | None = None) -> dict:
    """Fill in type-specific fields + TL;DR + frontmatter meta.

    Returns a dict like:
        {
          "title": "...",
          "tldr": "...",
          "fields": { <per-kind keys> },
          "subsystem": "...",
          "tags": [...],
          "status": "...",
          "confidence": "high|medium|low",
          "context_raw": "..."   # verbatim chunk to preserve under ## Context
        }
    """
    body_schema = _schema_hint_for(kind)
    sub_hint = ""
    if valid_subsystems:
        sub_hint = (
            "\nThe `subsystem` MUST be one of: " +
            ", ".join(valid_subsystems) +
            ' (or "unknown" if none fit).'
        )

    prompt = f"""You are structuring an engineering note. The kind is "{kind}".
Extract a self-contained, well-written note from the content below.

Rules:
- title: a clear short descriptive title (≤ 60 chars, no quotes, sentence case).
- tldr: ONE sentence that captures the takeaway. Write it like a sub-headline.
- Each field below should be 1-4 sentences. Use full prose, not bullets, except
  where the section title implies a list (e.g. "Action items", "Key points").
- For long-form sections like "investigation", "notes", "context": preserve
  technical detail. This is what gets embedded — richer = better recall.
- subsystem: a single lowercase word/snake_case tag describing the area.
- tags: 2-5 lowercase kebab-case tags (no '#').
- status: for debug → "open"|"investigating"|"fixed". Other kinds → "".
- confidence: how sure are you of this extraction? "high"|"medium"|"low".
- context_raw: VERBATIM excerpt(s) from the input that best preserve the
  original wording for future search. Up to ~600 chars.{sub_hint}

Output JSON ONLY, matching this schema:
{{
  "title": "...",
  "tldr": "...",
  "fields": {body_schema},
  "subsystem": "...",
  "tags": ["...", "..."],
  "status": "...",
  "confidence": "high|medium|low",
  "context_raw": "..."
}}

CONTENT:
\"\"\"{text}\"\"\"
"""
    data = _ask_json(prompt, temperature=0.15)
    # Defensive defaults so downstream code never trips on missing keys
    data.setdefault("title", "(untitled)")
    data.setdefault("tldr", "")
    data.setdefault("fields", {})
    data.setdefault("subsystem", "unknown")
    data.setdefault("tags", [])
    data.setdefault("status", "")
    data.setdefault("confidence", "medium")
    data.setdefault("context_raw", "")
    # Normalize tags
    if isinstance(data["tags"], str):
        data["tags"] = [t.strip().lstrip("#") for t in re.split(r"[,\s]+", data["tags"]) if t.strip()]
    data["tags"] = [str(t).strip().lstrip("#").lower() for t in (data["tags"] or [])][:5]
    return data


# ──────────────────────────────────────────────────────────────────────────────
# Pass 3 — extract entities
# ──────────────────────────────────────────────────────────────────────────────

ENTITY_CATEGORIES = (
    "files",     # source files / paths mentioned, e.g. "drivers/servo.cpp"
    "symbols",   # function / class / method names, e.g. "ServoController.set_torque"
    "errors",    # exception types / error codes / error messages
    "packages",  # external libraries / package names
    "urls",      # http(s) links
    "concepts",  # named domain concepts, products, hardware parts, services
)


def extract_entities(text: str) -> dict:
    """Pull structured entities out of arbitrary text. Returns a dict keyed by
    ENTITY_CATEGORIES, each value a list of distinct strings."""
    prompt = f"""Extract named entities that LITERALLY APPEAR in the content below,
grouped into these categories:

  - files     : source file names or paths that appear verbatim in the text
  - symbols   : function / class / method names that appear verbatim
  - errors    : exception types / error codes / error messages that appear verbatim
  - packages  : library or package names that appear verbatim
  - urls      : http or https URLs that appear verbatim
  - concepts  : named products, services, hardware parts, or domain terms named in the text

STRICT RULES:
- Extract ONLY strings that actually occur in the CONTENT below. Do NOT invent,
  infer, guess, or copy anything from these instructions. If you are not certain
  a string literally appears in the content, leave it out.
- If a category has nothing, return an empty array [].
- Dedupe. Output the JSON object only — no commentary, no examples.

Schema:
{{"files":[],"symbols":[],"errors":[],"packages":[],"urls":[],"concepts":[]}}

CONTENT:
\"\"\"{text}\"\"\"
"""
    data = _ask_json(prompt, temperature=0.05)
    out: dict[str, list[str]] = {}
    for cat in ENTITY_CATEGORIES:
        vals = data.get(cat) or []
        if isinstance(vals, str):
            vals = [vals]
        # Normalize: strip whitespace, dedupe in order
        seen, cleaned = set(), []
        for v in vals:
            s = str(v).strip()
            if not s or s in seen:
                continue
            seen.add(s)
            cleaned.append(s)
        out[cat] = cleaned[:25]  # hard cap per category
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Pass 4 — optional self-critique
# ──────────────────────────────────────────────────────────────────────────────

def self_critique(text: str, draft: dict, kind: str) -> dict:
    """Optional pass: ask the model to flag anything it missed and return a
    patched draft. Skipped unless caller passes run_critique=True — it doubles
    extraction time and only helps on long, complex inputs.
    """
    prompt = f"""Review the structured note draft below against the source content.
What important detail is missing or wrong? Patch the draft and return the
COMPLETE corrected JSON in the same schema (don't return just a diff).

Common things to check for:
- Was anything important from the source dropped?
- Is the title genuinely descriptive?
- Are entities (files, errors, packages) complete?
- Is confidence appropriately set?

DRAFT:
{json.dumps(draft, indent=2)}

SOURCE:
\"\"\"{text}\"\"\"

Output the corrected full JSON only."""
    patched = _ask_json(prompt, temperature=0.1)
    if not patched or not isinstance(patched, dict):
        return draft
    # Merge — patched wins for keys it provides, original kept otherwise
    out = dict(draft)
    for k, v in patched.items():
        if v not in (None, "", [], {}):
            out[k] = v
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Public entry: full pipeline
# ──────────────────────────────────────────────────────────────────────────────

def extract(
    text: str,
    *,
    hint: str = "auto",
    run_critique: bool = False,
    valid_subsystems: list[str] | None = None,
) -> dict:
    """Run the full extraction pipeline on `text` and return a dict ready for
    writer.log_universal().

    Returns:
        {
          "kind": "<one of ALL_KINDS>",
          "title": "...",
          "fields": { <per-kind fields, + tldr, + context_raw> },
          "subsystem": "...",
          "tags": [...],
          "status": "...",
          "confidence": "high|medium|low",
          "entities": { files: [], symbols: [], errors: [], packages: [], urls: [], concepts: [] },
          "meta": { "classify_reason": "...", "passes_run": [...] }
        }
    """
    from memory.llm import is_available
    if not is_available():
        # No local LLM — return an empty structure so the caller keeps the raw
        # note. (capture() also checks is_available() before enqueuing, so this
        # is a defensive fast-path for any other caller.)
        return {
            "kind": hint if (hint and hint in ALL_KINDS) else "session",
            "title": "", "fields": {}, "subsystem": "unknown", "tags": [],
            "status": "", "confidence": "", "entities": {},
            "meta": {"passes_run": [], "llm": "unavailable"},
        }

    passes: list[str] = []

    # ── Pass 1: classify ─────────────────────────────────────────────────────
    if hint and hint != "auto" and hint in ALL_KINDS:
        kind, classify_reason = hint, f"forced by hint=\"{hint}\""
    else:
        kind, classify_reason = classify_type(text)
        passes.append("classify")

    # ── Pass 2: structure ────────────────────────────────────────────────────
    structure = extract_structure(text, kind, valid_subsystems=valid_subsystems)
    passes.append("structure")

    # ── Pass 3: entities ─────────────────────────────────────────────────────
    entities = extract_entities(text)
    passes.append("entities")

    # ── Pass 4: optional critique ────────────────────────────────────────────
    if run_critique:
        structure = self_critique(text, structure, kind)
        passes.append("critique")

    # Merge tldr + context_raw into the fields dict so the writer can splat it
    fields = dict(structure.get("fields") or {})
    fields.setdefault("tldr", structure.get("tldr", ""))
    fields.setdefault("context_raw", structure.get("context_raw", ""))

    return {
        "kind":       kind,
        "title":      structure.get("title", "(untitled)"),
        "fields":     fields,
        "subsystem":  structure.get("subsystem", "unknown"),
        "tags":       structure.get("tags", []),
        "status":     structure.get("status", ""),
        "confidence": structure.get("confidence", "medium"),
        "entities":   entities,
        "meta": {
            "classify_reason": classify_reason,
            "passes_run":      passes,
        },
    }
