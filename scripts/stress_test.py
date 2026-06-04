#!/usr/bin/env python3
"""
scripts/stress_test.py — hammer memcon and prove it holds up.

Fires a burst of concurrent writes (the exact pattern that used to freeze it),
optionally with concurrent reads at the same time, then checks the four things
that must ALWAYS be true:

    • no write blocked / hung          (max return latency stays low)
    • no note lost                     (every write is on disk)
    • no two writes collided           (every write got its own file)
    • every note made it into search   (Qdrant point count per doc > 0)

Runs against an ISOLATED throwaway vault + a `memcon_stresstest` Qdrant
collection by default, so it never touches your real notes, and cleans up after.

Examples:
    python3 scripts/stress_test.py                       # 30 writes, 10 workers
    python3 scripts/stress_test.py --writes 100 --workers 20 --reads
    python3 scripts/stress_test.py --live                # use your REAL vault (then cleans up)
"""
import os
import sys
import time
import json
import shutil
import argparse
import tempfile
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor


def main():
    ap = argparse.ArgumentParser(description="Stress-test memcon's write/read paths.")
    ap.add_argument("--writes", type=int, default=30, help="number of notes to write (default 30)")
    ap.add_argument("--workers", type=int, default=10, help="concurrent writer threads (default 10)")
    ap.add_argument("--reads", action="store_true", help="hammer reads concurrently with the writes")
    ap.add_argument("--live", action="store_true", help="use your REAL vault/collection instead of an isolated one")
    ap.add_argument("--keep", action="store_true", help="don't clean up the stress notes afterward")
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, repo)

    tmp = None
    if not args.live:
        tmp = tempfile.mkdtemp(prefix="memcon_stress_")
        os.environ["MEMCON_VAULT"] = tmp
        os.environ["MEMCON_COLLECTION"] = "memcon_stresstest"

    # Import AFTER env is set so config picks up the isolated vault/collection.
    from pathlib import Path
    from ingestion.embedder import embed
    from memory.writer import log_decision
    from memory import worker
    from memory.retrieve import query
    from memory.qdrant_store import delete_by_doc, _get_client, COLLECTION
    from memory.entity_index import clear_doc
    import ingestion.ingest as ing
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    try:
        _get_client().get_collections()   # is the Qdrant server up? (no specific collection needed)
    except Exception as e:
        print(f"❌ Qdrant isn't reachable ({e}). Start the stack first:  ./start.sh   (or: docker compose up -d)")
        sys.exit(2)

    def doc_indexed(doc_name: str) -> bool:
        r = _get_client().count(
            collection_name=COLLECTION,
            count_filter=Filter(must=[FieldCondition(key="doc_name", match=MatchValue(value=doc_name))]),
            exact=True,
        )
        return r.count > 0

    print(f"⚙️  {args.writes} writes × {args.workers} workers · "
          f"{'LIVE vault' if args.live else 'isolated vault'}"
          f"{' · + concurrent reads' if args.reads else ''}")
    embed(["warm"])   # warm the model so we measure steady state, not a cold load

    lock = threading.Lock()
    latencies, results, errors = [], [], []

    # Optional: readers pounding the index while writes land (two-client-ish).
    stop = threading.Event()
    reads_ok, read_errs = [0], []

    def reader():
        while not stop.is_set():
            try:
                query("widget pipeline scaling under load", top_k=5)
                with lock:
                    reads_ok[0] += 1
            except Exception as e:
                with lock:
                    read_errs.append(str(e))
            time.sleep(0.005)

    readers = [threading.Thread(target=reader, daemon=True) for _ in range(3)] if args.reads else []
    for t in readers:
        t.start()

    def do_write(i):
        t0 = time.time()
        try:
            p = log_decision(
                f"Stress note {i} for the widget pipeline scaling test",
                f"Adopt approach number {i} so the widget pipeline scales under heavy concurrent load.",
                f"Because approach {i} avoided the lock contention we measured in trial {i}.",
                "version_control", ["stresstest"],
            )
            with lock:
                latencies.append(time.time() - t0)
                results.append((i, p))
        except Exception as e:
            with lock:
                errors.append(f"write {i}: {e}")

    t_start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(do_write, range(args.writes)))
    write_wall = time.time() - t_start

    print("   draining the background worker…")
    worker._q.join()
    time.sleep(1.0)
    stop.set()

    paths = [p for (_, p) in results]
    on_disk = sum(1 for p in paths if os.path.exists(p))
    unique = len(set(paths))
    indexed = sum(1 for p in paths if doc_indexed(Path(p).stem))

    print("\n── results ──────────────────────────────────────")
    print(f"   write errors       : {len(errors)}")
    if latencies:
        print(f"   return latency     : max {max(latencies):.3f}s · median {statistics.median(latencies):.3f}s   (instant-return)")
    print(f"   wrote (wall)       : {len(results)}/{args.writes} in {write_wall:.1f}s")
    print(f"   on disk            : {on_disk}/{len(paths)}   ← data-loss check")
    print(f"   unique files       : {unique}/{len(paths)}   ← collision check")
    print(f"   indexed in Qdrant  : {indexed}/{len(paths)}   ← search-integrity check")
    if args.reads:
        print(f"   reads during writes: {reads_ok[0]} ok · {len(read_errs)} failed   ← reads never hang/crash")

    ok = (
        not errors and on_disk == len(paths) == args.writes and unique == len(paths)
        and indexed == len(paths) and (not latencies or max(latencies) < 5.0)
        and not read_errs
    )
    print("\n   " + ("✅ PASS — no hangs, no loss, no collisions, every note searchable."
                     if ok else "❌ FAIL — see the numbers above."))
    for e in errors[:5] + read_errs[:5]:
        print("     !", e)

    if not args.keep:
        for p in paths:
            stem = Path(p).stem
            try:
                if os.path.exists(p):
                    os.remove(p)
                delete_by_doc(stem)
                clear_doc(stem)
                m = ing._manifest_read()
                m.pop(stem, None)
                ing._atomic_write_text(ing._manifest_path(), json.dumps(m))
            except Exception:
                pass
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
            try:
                _get_client().delete_collection(COLLECTION)
            except Exception:
                pass
        print("   (cleaned up)")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
