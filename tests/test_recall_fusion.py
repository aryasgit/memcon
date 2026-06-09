"""
Stack-free unit tests for the recall fusion core (memory/recall.py) — the
recency + outcome ranking the "knows what you fixed LAST time" promise rests on.
Pure functions: no Qdrant, no embedder, no vault, so these ALWAYS run in CI.
"""
import pytest
from memory.recall import (
    recency_factor, fused_score, normalize_outcome, fuse, summarize,
    RECENCY_HALF_LIFE_DAYS,
)


def test_recency_factor_decays_monotonically():
    assert recency_factor(0) == 1.0
    assert recency_factor(RECENCY_HALF_LIFE_DAYS) == pytest.approx(0.5)
    ages = [1, 5, 15, 30, 60, 120, 365]
    vals = [recency_factor(a) for a in ages]
    assert all(earlier > later for earlier, later in zip(vals, vals[1:]))
    assert vals[-1] < 0.05  # a year-old note keeps almost no recency lift


def test_recency_factor_handles_none_and_zero_age():
    # Unknown age must NOT be treated as "today" — that conflation was the
    # phantom-recall bug (a fileless candidate ranked as a fresh hit).
    assert recency_factor(None) == 0.0
    assert recency_factor(0) == 1.0      # written today
    assert recency_factor(-5) == 1.0     # clock skew / future-dated → capped


@pytest.mark.parametrize("status,expected", [
    ("fixed", "resolved"), ("resolved", "resolved"), ("closed", "resolved"),
    ("done", "resolved"), ("verified", "resolved"),
    ("open", "open"), ("investigating", "open"), ("wip", "open"), ("in-progress", "open"),
    ("failed", "failed"), ("abandoned", "failed"), ("reverted", "failed"), ("wontfix", "failed"),
    ("FIXED", "resolved"), ("  Open ", "open"),   # case- and whitespace-insensitive
    ("", "unknown"), (None, "unknown"), ("banana", "unknown"),
])
def test_normalize_outcome_maps_statuses(status, expected):
    assert normalize_outcome(status) == expected


def test_fused_score_semantic_dominates_recency():
    # An OLD but very similar note must outrank a RECENT but barely-similar one...
    assert fused_score(0.90, age_days=365) > fused_score(0.40, age_days=0)
    # ...while among comparable similarities, the more recent wins.
    assert fused_score(0.70, age_days=1) > fused_score(0.70, age_days=200)


def test_fuse_ranks_enriches_and_truncates_to_k():
    # recency lifts a note at most ~1.6x (RECENCY_WEIGHT=0.6), so a 0.95-sim note
    # with ~no recency still beats a recent-but-weak 0.40-sim one (0.40*1.6=0.64).
    cands = [
        {"doc_name": "old-strong",  "similarity": 0.95, "age_days": 400, "status": "fixed"},
        {"doc_name": "recent-weak", "similarity": 0.40, "age_days": 1,   "status": "open"},
        {"doc_name": "mid",         "similarity": 0.50, "age_days": 30,  "status": "failed"},
    ]
    ranked = fuse(cands, k=2)
    assert len(ranked) == 2                           # truncated to k
    assert ranked[0]["score"] >= ranked[1]["score"]   # descending score order
    assert ranked[0]["doc_name"] == "old-strong"      # semantic dominates a weak-but-recent hit
    assert ranked[0]["outcome"] == "resolved"         # 'fixed' → resolved
    for row in ranked:                                # every row enriched
        assert {"recency", "score", "outcome"} <= set(row)


def test_fuse_empty_is_empty():
    assert fuse([], k=5) == []


def test_summarize_headline_reflects_top_outcome_and_count():
    assert "Nothing in memory" in summarize("x", [])
    ranked = fuse([
        {"doc_name": "a", "similarity": 0.9, "age_days": 0.2, "status": "fixed",
         "what_was_tried": "raised the pool to 50"},
        {"doc_name": "b", "similarity": 0.6, "age_days": 40, "status": "open"},
    ], k=5)
    s = summarize("redis pool", ranked)
    assert "2 related notes" in s
    assert "today" in s        # top note age < 1 day
    assert "resolved" in s     # top outcome 'fixed' → "was resolved"
