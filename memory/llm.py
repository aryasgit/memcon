"""
memory/llm.py
Optional local-LLM access — the heart of the "lean / Ollama-optional" design.

memcon works WITHOUT a local LLM. The calling assistant (Claude) does the
reasoning; memcon handles storage + embeddings + retrieval, and embeddings use
sentence-transformers (a local Python model), NOT a local LLM. A local LLM
(Ollama) is an OPT-IN power feature for fully-offline auto-structuring and
self-contained answers.

is_available() probes the configured endpoint once (cached, short timeout). When
the LLM is off or unreachable, the LLM-dependent tools degrade cleanly:
  - memcon_capture keeps the instant raw note (already searchable)
  - memcon_ask / memcon_digest return the relevant chunks/notes for the assistant
"""
from __future__ import annotations
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg

_client = None
_available = None      # tri-state cache: None = not yet probed
_probed_at = 0.0
_PROBE_TTL = 30.0      # re-probe at most this often (seconds)


def enabled() -> bool:
    """Is the local-LLM feature switched on in config? Defaults to True so a
    present Ollama is auto-used; the availability probe handles 'not installed'.
    Set `llm.enabled: false` or `llm.provider: none` to force the lean path."""
    try:
        if cfg('llm', 'enabled') is False:
            return False
    except Exception:
        pass
    try:
        if str(cfg('llm', 'provider')).strip().lower() in ('none', 'off', 'disabled', ''):
            return False
    except Exception:
        pass
    return True


def timeout() -> float:
    try:
        return float(cfg('llm', 'timeout'))
    except Exception:
        return 90.0


def base_url() -> str:
    return cfg('llm', 'base_url')


def get_client():
    """Shared OpenAI-compatible client with a hard timeout (lazy). Only construct
    it when you've already confirmed is_available()."""
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            base_url=base_url(),
            api_key=os.getenv("LLM_API_KEY", "ollama"),
            timeout=timeout(),
        )
    return _client


def is_available(force: bool = False) -> bool:
    """True iff a local LLM is enabled AND reachable. Cheap: a cached probe with a
    short TTL and a ~2s connect timeout, so a missing Ollama costs at most one
    quick failed connection, then nothing for `_PROBE_TTL` seconds."""
    global _available, _probed_at
    if not enabled():
        return False
    now = time.monotonic()
    if not force and _available is not None and (now - _probed_at) < _PROBE_TTL:
        return _available
    _available = _probe()
    _probed_at = now
    if not _available:
        print("[llm] no local LLM reachable — running lean (the assistant does the "
              "reasoning; raw notes are still captured and searchable)", file=sys.stderr)
    return _available


def _probe() -> bool:
    import urllib.request
    from urllib.parse import urlparse
    url = base_url().rstrip('/')
    candidates = [url + "/models"]                       # OpenAI-compatible servers
    try:
        u = urlparse(url)
        candidates.append(f"{u.scheme}://{u.netloc}/api/tags")   # Ollama native
    except Exception:
        pass
    for c in candidates:
        try:
            with urllib.request.urlopen(urllib.request.Request(c, method="GET"), timeout=2) as r:
                if getattr(r, "status", 200) < 500:
                    return True
        except Exception:
            continue
    return False
