#!/usr/bin/env python3
"""
scripts/load_sample_data.py — one-click demo dataset for memcon.

Drops a small, realistic project memory (a fictional backend service, "Relay")
into your vault and indexes it, so you can immediately try semantic / temporal /
entity / recall search. Dates are computed relative to TODAY, so the demo always
looks current, and file mtimes are backdated so temporal queries work too.

    python3 scripts/load_sample_data.py            # load the sample notes
    python3 scripts/load_sample_data.py --clean    # remove them again

Every sample note carries `sample: true` in its frontmatter, so --clean removes
exactly what this script added and nothing else.
"""
from __future__ import annotations
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import cfg
from memory.templates import _slug, FOLDER_FOR

# (kind, age_days, subsystem, [tags], title, tldr, body_markdown)
SAMPLE_NOTES = [
    ("debug", 1, "database", ["postgres", "deadlock", "concurrency"],
     "Postgres deadlock on concurrent job upserts",
     "Two workers upserting the same jobs row deadlocked under load; fixed by a consistent lock order.",
     "## Symptom\nUnder load, two workers upserting the same `jobs` row hit `deadlock detected` (SQLSTATE 40P01) and one transaction was rolled back.\n\n## Cause\nThe transactions locked rows in different orders, forming a cycle.\n\n## Fix\nOrder every upsert by `job_id` and use `INSERT ... ON CONFLICT (job_id) DO UPDATE`. Consistent lock order, no more cycles.\n\n## Status\nfixed"),

    ("debug", 2, "cache", ["redis", "connection-pool", "latency"],
     "Redis connection pool exhausted under burst load",
     "p99 hit 4s and requests failed with max-connections; raising the pool to 50 fixed it.",
     "## Symptom\nDuring traffic spikes, requests failed with `ConnectionError: max number of clients reached` and p99 latency climbed to ~4s.\n\n## Cause\nPool size was 10 and each request held a connection for the duration of a slow Lua script.\n\n## Fix\nRaised the pool to 50 and moved the Lua script off the request hot path. p99 dropped to ~220ms.\n\n## Status\nfixed"),

    ("debug", 9, "auth", ["jwt", "clock-skew", "ntp"],
     "JWT tokens rejected as expired right after issue",
     "Valid tokens 401'd within seconds — the auth server clock was 90s ahead; NTP + leeway fixed it.",
     "## Symptom\nFreshly issued JWTs were rejected as expired within seconds of login (401).\n\n## Cause\nThe auth server's clock was ~90s ahead of the API servers; `exp` was validated against the skewed time.\n\n## Fix\nEnabled NTP sync across the fleet and added 120s of leeway on `exp` validation.\n\n## Status\nfixed"),

    ("debug", 16, "api", ["n+1", "latency", "orm"],
     "p99 latency spike on /jobs traced to N+1 queries",
     "Adding tags to the jobs list caused an N+1; eager-loading brought p99 from 2.5s back to 80ms.",
     "## Symptom\nAfter adding tags to the `/jobs` list response, p99 latency jumped to ~2.5s.\n\n## Cause\nThe ORM lazy-loaded each row's tags separately — a classic N+1.\n\n## Fix\nEager-load tags with a single join. p99 back to ~80ms.\n\n## Status\nfixed"),

    ("decision", 4, "database", ["postgres", "mongodb", "architecture"],
     "Use Postgres over MongoDB for the job store",
     "Picked Postgres because jobs are relational and we need transactional upserts + advisory locks.",
     "## Decision\nThe job store lives in Postgres.\n\n## Reasoning\nJobs are relational, we need transactional upserts and advisory locks, and ops already runs Postgres. MongoDB bought us nothing here and added a second datastore to operate."),

    ("decision", 6, "events", ["redis-streams", "kafka", "event-bus"],
     "Adopt Redis Streams for the event bus (not Kafka yet)",
     "Redis Streams now; revisit Kafka at ~10k events/s. The ops overhead isn't justified at our scale.",
     "## Decision\nUse Redis Streams as the event bus for now.\n\n## Reasoning\nThroughput needs are modest and we already run Redis. Kafka's operational overhead isn't justified yet. Revisit at ~10k events/s.\n\n## Alternatives\nKafka (deferred), SNS/SQS (ties us to a cloud)."),

    ("decision", 11, "api", ["rate-limit", "gateway"],
     "Rate-limit at the gateway, not per-service",
     "Centralized rate limiting at the API gateway so limits live in one place.",
     "## Decision\nRate limiting happens at the API gateway, centrally.\n\n## Reasoning\nOne place to reason about limits; avoids duplicated token-bucket logic in every service. Services still validate auth independently."),

    ("experiment", 3, "cache", ["redis", "connection-pool", "benchmark"],
     "Benchmarked Redis pool sizes: 10 vs 50 vs 100",
     "50 cut p99 from 4s to 220ms; 100 gave no further gain at 2x memory. 50 is the sweet spot.",
     "## Hypothesis\nA bigger Redis connection pool reduces p99 under burst load.\n\n## Result\n- pool=10 → p99 ~4s (the incident)\n- pool=50 → p99 ~220ms\n- pool=100 → p99 ~210ms, but ~2x memory\n\n## Conclusion\nPool size 50 is the sweet spot. See the connection-pool-exhausted debug note."),

    ("concept", 8, "events", ["outbox", "reliability", "messaging"],
     "The outbox pattern for reliable event publishing",
     "Write the event to an outbox table in the same DB transaction as the state change; a relay publishes it.",
     "## Definition\nInstead of writing to the DB and publishing to the bus separately (a dual write that can't be atomic), write the event into an `outbox` table inside the same transaction as the state change. A background relay reads the outbox and publishes.\n\n## Why it matters\nKills the dual-write problem: either both the state change and the event happen, or neither does."),

    ("concept", 13, "api", ["idempotency", "payments"],
     "Idempotency keys for the payments endpoint",
     "Client sends an Idempotency-Key header; the server dedupes by storing the key + response.",
     "## Definition\nThe client sends a unique `Idempotency-Key` header. The server stores the key with the response; a repeat with the same key returns the stored response instead of re-executing.\n\n## Why it matters\nNetwork retries on a charge can't double-charge the customer."),

    ("reference", 14, "database", ["postgres", "locks", "docs"],
     "Postgres advisory locks — quick reference",
     "pg_advisory_lock for app-level mutual exclusion; prefer the xact-scoped variant so locks auto-release.",
     "## Summary\n`pg_advisory_lock(key)` gives application-level mutual exclusion that Postgres doesn't otherwise model.\n\n## Key points\n- Session-scoped locks persist until explicitly unlocked or the session ends.\n- Prefer `pg_advisory_xact_lock(key)` — it releases automatically on commit/rollback, so you can't leak a lock.\n\n## Source\nPostgreSQL docs — Advisory Locks."),

    ("breakthrough", 5, "api", ["latency", "profiling", "gc"],
     "Aha: the p99 spikes correlated with GC pauses, not the DB",
     "The latency spikes lined up with major GC pauses, not query time — re-framed the whole investigation.",
     "## Background\nWe'd been chasing the p99 spikes as a database problem for days.\n\n## Insight\nOverlaying the latency graph with GC logs, every spike lined up with a major GC pause — not with slow queries.\n\n## Implication\nTuned the heap and switched to streaming JSON encoding; p99 stabilized. The DB was never the bottleneck."),

    ("meeting", 6, "events", ["architecture", "sync"],
     "Architecture sync — event bus + outbox",
     "Agreed on Redis Streams now and an outbox table per service; spikes assigned.",
     "## Notes\nDebated Kafka vs Redis Streams for the bus. Walked through the dual-write risk and the outbox pattern.\n\n## Decisions\n- Redis Streams for now (revisit at 10k events/s).\n- Outbox table per service.\n\n## Action items\n- @alex: spike the outbox relay.\n- @sam: load-test Redis Streams at 2k events/s."),

    ("session", 0, "api", ["session", "weekly"],
     "Session — shipped the scheduler, fought Redis pools",
     "This week: shipped the job scheduler, fixed the Redis pool exhaustion and the Postgres deadlock, chose Redis Streams.",
     "## Summary\nShipped the job scheduler end-to-end. Put out two fires — the Redis connection-pool exhaustion (pool 10→50) and the Postgres deadlock on concurrent upserts (consistent lock order). Decided on Redis Streams for the event bus.\n\n## Open\nThe deadlock fix holds in testing, but watch it under higher production load."),
]


def _vault() -> Path:
    return Path(cfg('vault', 'path'))


def _render(note):
    kind, age, subsystem, tags, title, tldr, body = note
    created = datetime.now(timezone.utc) - timedelta(days=age, hours=age)
    date = created.strftime('%Y-%m-%d')
    note_id = f"{date}_{_slug(title)}"
    iso = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    import re
    sm = re.search(r'^##\s*Status\s*\n+\s*([A-Za-z]+)', body, re.MULTILINE)
    status_line = f"status: {sm.group(1).lower()}\n" if sm else ""
    fm = (
        "---\n"
        f"id: {note_id}\n"
        f"type: {kind}\n"
        "memory_type: episodic\n"
        f'created: "{iso}"\n'
        f'updated: "{iso}"\n'
        f"subsystem: {subsystem}\n"
        f"tags: [{', '.join(tags)}]\n"
        f"{status_line}"
        "sample: true\n"
        "---\n"
    )
    content = f"{fm}\n# {title}\n\n## TL;DR\n\n{tldr}\n\n{body}\n"
    folder = FOLDER_FOR.get(kind, "debugging")
    return folder, note_id, content, created


def load(reindex: bool = True) -> list[str]:
    from ingestion.ingest import ingest_file
    vault = _vault()
    paths = []
    for note in SAMPLE_NOTES:
        folder, note_id, content, created = _render(note)
        d = vault / folder
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{note_id}.md"
        p.write_text(content)
        ts = created.timestamp()
        os.utime(p, (ts, ts))   # backdate mtime so temporal/timeline reflects the spread
        paths.append(str(p))
    if reindex:
        for p in paths:
            try:
                ingest_file(p, force=True)
            except Exception as e:
                print(f"   (index failed for {p}: {e})", file=sys.stderr)
    return paths


def clean() -> int:
    from memory.qdrant_store import delete_by_doc
    vault = _vault()
    removed = 0
    for p in list(vault.rglob("*.md")):
        try:
            head = p.read_text(errors="ignore")[:400]
        except OSError:
            continue
        if "sample: true" in head:
            stem = p.stem
            p.unlink(missing_ok=True)
            try:
                delete_by_doc(stem)
            except Exception:
                pass
            removed += 1
    return removed


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Load (or remove) memcon's sample dataset.")
    ap.add_argument("--clean", action="store_true", help="remove the sample notes")
    args = ap.parse_args()
    if args.clean:
        print(f"🧹 Removed {clean()} sample notes.")
    else:
        paths = load()
        print(f"✅ Loaded {len(paths)} sample notes into {_vault()} and indexed them.\n")
        print("Try these (in Claude, or the dashboard at http://localhost:8000/ui):")
        print('   • recall    →  "redis connection pool problems again"')
        print('   • semantic  →  "database rows locking each other under load"')
        print('   • temporal  →  "what did I work on this week?"   (timeline, last 7 days)')
        print('   • entity    →  "JWT clock skew"')
        print('   • digest    →  "summarize the last two weeks"')
        print("\nRemove them later with:  python3 scripts/load_sample_data.py --clean")
