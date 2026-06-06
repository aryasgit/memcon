"""
Proof tests for memcon's launch differentiators.

These are deliberately end-to-end against the LIVE stack (real embedder, real
Qdrant collection, real SQLite entity index) so they prove the CLAIMS, not a
mock. They run in the FULL ISOLATION provided by conftest.py — a throwaway temp
vault (MEMCON_VAULT) + a dedicated Qdrant collection (memcon_pytest) — so they
never touch the real memory.

Each test cleans up after itself (Qdrant points + entity rows + the .md files)
so the suite leaves no residue and tests don't cross-contaminate.

Differentiators proven:
  (a) EXACT-ENTITY retrieval — a literal filename / error-string surfaces its
      note via the SQLite inverted index, contributing an entity hit even when
      the query shares no prose with the note.
  (b) RECIPROCAL BACK-LINKS — writing a related note B reaches BACK into the
      already-written neighbour A's markdown and adds a [[B]] link, so the
      connection is symmetric on disk (not just in Obsidian's backlinks panel).
  (c) HYBRID FUSION — a single query() returns one deduplicated result set in
      which the entity index AND the semantic index both contribute (a doc on
      both paths is fused into one via="both" row).
"""
import os
import time
import urllib.request
from pathlib import Path

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Live-stack gate (same pattern as test_search_and_stress.py)
# ──────────────────────────────────────────────────────────────────────────────

def _qdrant_up() -> bool:
    try:
        urllib.request.urlopen("http://localhost:6333/healthz", timeout=2)
        return True
    except Exception:
        return False


requires_qdrant = pytest.mark.skipif(not _qdrant_up(), reason="Qdrant not running on :6333")


def _drain():
    """Block until the bounded background worker has finished every queued job
    (ingest + entity index + reciprocal links), so the assertions see the
    settled state. Mirrors the drain pattern in test_search_and_stress.py."""
    from memory import worker
    worker._q.join()
    time.sleep(0.6)


def _purge(*stems: str):
    """Remove a note's footprint from BOTH indexes + disk so tests are isolated
    and rerunnable. Best-effort — never raises."""
    from memory.qdrant_store import delete_by_doc
    from memory.entity_index import clear_doc
    import ingestion.ingest as ing
    import json
    from config import cfg
    vault = Path(cfg("vault", "path"))
    for stem in stems:
        try:
            delete_by_doc(stem)
        except Exception:
            pass
        try:
            clear_doc(stem)
        except Exception:
            pass
        for p in vault.rglob(f"{stem}.md"):
            try:
                p.unlink()
            except OSError:
                pass
        try:
            m = ing._manifest_read()
            if m.pop(stem, None) is not None:
                ing._atomic_write_text(ing._manifest_path(), json.dumps(m))
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# (a) EXACT-ENTITY RETRIEVAL
# ──────────────────────────────────────────────────────────────────────────────

@requires_qdrant
def test_exact_entity_retrieval_surfaces_literal_token():
    """Ingest a note carrying two unique literal tokens — a filename (jwt.ts)
    and an error string (EADDRINUSE) — passed as explicit entities (the real
    lean-mode write path: Claude/extractor hands writer.log_* an `entities`
    dict, which writer._finalize_note feeds to entity_index.index_note).

    Then query each literal token and assert:
      - the note surfaces, and
      - it surfaces *through the entity index* (entity_hits is populated /
        via includes the entity path), i.e. the exact-string recall side of
        the hybrid is doing real work — not coincidental semantic overlap.
    """
    from ingestion.embedder import embed
    embed(["warm"])  # ensure the model is loaded before any retrieval
    from memory.writer import log_debug
    from memory.retrieve import query
    from memory.entity_index import lookup

    # Prose deliberately avoids the literal tokens jwt.ts / EADDRINUSE so the
    # only reliable way to retrieve by those tokens is the entity index.
    path = log_debug(
        title="Auth gateway would not bind on the release host",
        symptom="The service refused to come up; the listener handler aborted during startup.",
        cause="A stale orphaned process from the previous deploy still held the socket.",
        fix="Reaped the orphan and added a readiness probe before traffic shifts.",
        status="fixed",
        subsystem="unknown",
        tags=["differentiator-test"],
        entities={"files": ["jwt.ts"], "errors": ["EADDRINUSE"]},
    )
    stem = Path(path).stem
    try:
        _drain()

        # The inverted index has the literal tokens, keyed to this exact note.
        assert any(h["doc_name"] == stem for h in lookup("EADDRINUSE")), \
            "entity index did not record the literal error string EADDRINUSE"
        assert any(h["doc_name"] == stem for h in lookup("jwt.ts")), \
            "entity index did not record the literal filename jwt.ts"

        # Querying the literal error token surfaces the note AND the entity
        # index is a contributor (entity_hits populated → exact-string recall).
        for token, expected in (("EADDRINUSE", "EADDRINUSE"), ("jwt.ts", "jwt.ts")):
            hits = query(token, top_k=5)
            hit = next((h for h in hits if h.get("doc_name") == stem), None)
            assert hit is not None, f"query({token!r}) did not surface the note: {[h.get('doc_name') for h in hits]}"
            assert hit.get("via") in ("entity", "both"), \
                f"query({token!r}) surfaced the note but NOT via the entity index (via={hit.get('via')})"
            matched = [m["entity"] for m in hit.get("entity_hits", [])]
            assert any(expected.lower() in m.lower() or m.lower() in expected.lower() for m in matched), \
                f"query({token!r}) entity_hits did not include {expected!r}: {matched}"
    finally:
        _purge(stem)


# ──────────────────────────────────────────────────────────────────────────────
# (b) RECIPROCAL BACK-LINKS
# ──────────────────────────────────────────────────────────────────────────────

@requires_qdrant
def test_reciprocal_backlink_written_into_existing_neighbour():
    """Write note A. Then write a semantically-close note B. Assert that A's
    *own markdown file* gains a [[B]] link in its ## Related section.

    This is the non-obvious half of memcon's linking: B's write reaches BACK
    into the already-on-disk neighbour A and edits it (writer._add_reciprocal_link
    under a per-note lock), making the connection symmetric on disk. A plain
    "new note links to its neighbours" system would only give the forward edge
    (B → A); here we prove the reverse edge (A → B) was materialised after the
    fact.
    """
    from ingestion.embedder import embed
    embed(["warm"])  # _find_related is a NO-OP unless the model is already warm
    from memory.writer import log_decision

    pA = log_decision(
        title="Adopt a bounded connection pool for the Postgres database layer",
        decision="Put a single bounded pgbouncer pool in front of every service.",
        reasoning=("Under burst traffic we exhausted Postgres connections and saw "
                   "cascading request timeouts; a shared bounded pool removes the "
                   "contention and caps total server connections."),
        subsystem="unknown",
        tags=["differentiator-test"],
    )
    _drain()
    stemA = Path(pA).stem

    pB = log_decision(
        title="Size the pgbouncer pool and acquire timeout for the Postgres backend",
        decision="Cap the pgbouncer pool at 80 server connections with a 5s acquire timeout.",
        reasoning=("Building on the decision to put a bounded Postgres connection pool "
                   "in front of services, we sized it from the burst-traffic connection "
                   "exhaustion and request-timeout numbers we measured."),
        subsystem="unknown",
        tags=["differentiator-test"],
    )
    _drain()
    stemB = Path(pB).stem

    try:
        assert stemA != stemB, "the two notes collided onto one file"
        text_a = Path(pA).read_text()
        # The reverse edge: A (written FIRST) now points at B (written SECOND).
        assert f"[[{stemB}]]" in text_a, (
            "reciprocal back-link missing: A's markdown did not gain [[B]] after B "
            f"was written. A's body tail:\n{text_a[-400:]}"
        )
        # Sanity: a ## Related section actually exists in A and holds the link.
        assert "## Related" in text_a, "A has no ## Related section"
    finally:
        _purge(stemA, stemB)


# ──────────────────────────────────────────────────────────────────────────────
# (c) HYBRID FUSION
# ──────────────────────────────────────────────────────────────────────────────

@requires_qdrant
def test_hybrid_fusion_merges_semantic_and_entity_deduplicated():
    """One query() must fuse BOTH retrieval paths into one deduplicated result
    set:
      - a SEMANTIC-only doc (matched purely by meaning, no shared literal token),
      - an ENTITY-contributing doc (matched on a unique literal token),
      - with NO doc appearing twice (the merge in retrieve.query dedupes by
        doc_name; a doc found on both paths becomes a single via="both" row).
    """
    from ingestion.embedder import embed
    embed(["warm"])
    from memory.writer import log_debug
    from memory.retrieve import query

    # Doc 1 — carries a unique literal token (the package "zxqwidget") in its
    # entities. The query mentions that exact token, so the ENTITY path fires.
    p_ent = log_debug(
        title="Widget renderer stalls when the third-party charting lib initialises",
        symptom="First paint blocks for several seconds while the chart subsystem warms up.",
        cause="The charting library does a synchronous font scan on first import.",
        fix="Deferred the import behind an idle callback.",
        status="fixed",
        subsystem="unknown",
        tags=["differentiator-test"],
        entities={"packages": ["zxqwidget"]},
    )
    stem_ent = Path(p_ent).stem

    # Doc 2 — NO overlapping literal token with the query at all; it can only be
    # found by MEANING. Describes a database deadlock under contention.
    p_sem = log_debug(
        title="Two transactions wedged each other holding row locks in opposite order",
        symptom="Throughput collapsed; both workers sat waiting forever and one was eventually aborted.",
        cause="Lock acquisition order differed between the two code paths, so under load they formed a cycle.",
        fix="Enforced a single canonical row-locking order across both paths.",
        status="fixed",
        subsystem="unknown",
        tags=["differentiator-test"],
    )
    stem_sem = Path(p_sem).stem

    try:
        _drain()

        # Query mixes a literal entity token (zxqwidget) with prose that is
        # semantically about the deadlock note — wording that shares no literal
        # token with that note's title.
        hits = query(
            "zxqwidget plus two database operations each blocking the other in a waiting cycle under load",
            top_k=8,
        )

        # Dedup invariant: every returned doc_name is unique.
        names = [h.get("doc_name") for h in hits]
        assert len(names) == len(set(names)), f"hybrid result set is NOT deduplicated: {names}"

        # The entity path contributed: the zxqwidget note is present with an
        # entity contribution.
        ent_hit = next((h for h in hits if h.get("doc_name") == stem_ent), None)
        assert ent_hit is not None, f"entity-token doc missing from fused results: {names}"
        assert ent_hit.get("via") in ("entity", "both"), \
            f"entity-token doc not attributed to the entity path (via={ent_hit.get('via')})"
        assert ent_hit.get("entity_hits"), "entity-token doc has no entity_hits"

        # The semantic path contributed: the deadlock note is present purely on
        # meaning (it shares no literal query token), attributed to semantics.
        sem_hit = next((h for h in hits if h.get("doc_name") == stem_sem), None)
        assert sem_hit is not None, f"semantic-only doc missing from fused results: {names}"
        assert sem_hit.get("via") in ("semantic", "both"), \
            f"semantic-only doc not attributed to the semantic path (via={sem_hit.get('via')})"

        # Both paths are represented in ONE merged platter — that's the fusion.
        vias = {h.get("via") for h in hits}
        assert ({"entity"} & vias) or ("both" in vias), f"no entity contribution in fused set: {vias}"
        assert ({"semantic"} & vias) or ("both" in vias), f"no semantic contribution in fused set: {vias}"
    finally:
        _purge(stem_ent, stem_sem)


# ──────────────────────────────────────────────────────────────────────────────
# (d) EXACT-ENTITY in the DEFAULT (lean) mode — the differentiator that was dormant
# ──────────────────────────────────────────────────────────────────────────────

@requires_qdrant
def test_exact_entity_works_in_lean_mode_from_content_only():
    """The shipped default (lean, no Ollama): a note is written with entity tokens
    ONLY in its content — NO `entities=` argument, no LLM extractor in the loop.
    ingest_file's LLM-free regex pass (entity_index.extract_entities_from_text)
    must populate the entity index from that content, so the literal token is
    recallable by exact match.

    This proves the fix for the audit's finding that exact-entity recall was
    dormant by default — it previously only worked when the optional local LLM
    supplied an `entities` dict.
    """
    from ingestion.embedder import embed
    embed(["warm"])
    from memory.writer import log_debug
    from memory.entity_index import lookup
    from memory.retrieve import query
    from memory.recall import recall

    # Unique tokens that appear ONLY in the note body, never passed as entities:
    #   ZQXBINDFAIL          — all-caps → error token
    #   cfg/relay_pool.toml  — slashed path + known extension → file token
    path = log_debug(
        title="Service refused to start after the blue-green cutover",
        symptom="The listener aborted during boot with `ZQXBINDFAIL` while reading `cfg/relay_pool.toml`.",
        cause="A previous instance still held the port; the readiness gate let traffic in too early.",
        fix="Reaped the orphan and gated traffic behind a real health check.",
        status="fixed", subsystem="unknown", tags=["differentiator-test"],
        # deliberately NO entities= — the lean default path must index from content
    )
    stem = Path(path).stem
    try:
        _drain()
        assert any(h["doc_name"] == stem for h in lookup("ZQXBINDFAIL")), \
            "lean ingest did not index the literal error token from content"
        assert any(h["doc_name"] == stem for h in lookup("cfg/relay_pool.toml")), \
            "lean ingest did not index the literal filename from content"

        hit = next((h for h in query("ZQXBINDFAIL", top_k=5) if h.get("doc_name") == stem), None)
        assert hit is not None, "query(literal token) did not surface the note in lean mode"
        assert hit.get("via") in ("entity", "both"), \
            f"surfaced but not via the entity index (via={hit.get('via')})"

        # And the FLAGSHIP recall path (not just query) now uses exact-entity:
        r = recall("ZQXBINDFAIL", k=5)
        assert any(m.get("doc_name") == stem for m in r.get("matches", [])), \
            "memcon_recall did not surface the note by its exact error token"
    finally:
        _purge(stem)
