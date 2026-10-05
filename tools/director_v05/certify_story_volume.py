"""Production-volume certification for the checkpointed Story Factory queue.

Run this only against a disposable/shadow Engine database. It intentionally
executes the real Story batch drain so we can prove queue semantics against
production-shaped data without mutating the live corpus.
"""
from __future__ import annotations

import argparse
import json
import sqlite3

from tools.quiz_export import engine as engine_bootstrap
from .story_batch_drain import drain_story_queue


TERMINAL_STATES = {"DONE", "REVIEW_REQUIRED", "FAILED_RETRYABLE", "FAILED_FINAL"}


def _ledger(conn):
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='story_candidate_processing'"
    ).fetchone():
        return {}
    return {
        str(r[0]): int(r[1])
        for r in conn.execute(
            "SELECT state,COUNT(*) FROM story_candidate_processing GROUP BY state"
        ).fetchall()
    }


def _generated_total(conn):
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='story_candidate_processing'"
    ).fetchone():
        return 0
    return int(conn.execute(
        "SELECT COALESCE(SUM(generated_question_count),0) FROM story_candidate_processing"
    ).fetchone()[0])


def evaluate_volume_result(*, before_ledger, after_ledger, before_generated, after_generated,
                           drain, processed_rows, min_claimed):
    claimed = int(drain.get("claimed_total") or 0)
    errors = []

    if claimed < int(min_claimed):
        errors.append(f"INSUFFICIENT_CLAIMED:{claimed}<{int(min_claimed)}")
    if int(after_generated) < int(before_generated):
        errors.append("GENERATED_COUNT_REGRESSED")
    if int(after_ledger.get("PROCESSING", 0)) > int(before_ledger.get("PROCESSING", 0)):
        errors.append("STRANDED_PROCESSING_ROWS")

    seen = set()
    for row in processed_rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            errors.append("MISSING_CANDIDATE_ID")
            continue
        if cid in seen:
            errors.append(f"DUPLICATE_CANDIDATE:{cid}")
        seen.add(cid)
        state = str(row.get("state") or "")
        if state not in TERMINAL_STATES:
            errors.append(f"NON_TERMINAL_STATE:{cid}:{state}")
        attempts = int(row.get("attempts") or 0)
        if attempts < 1 or attempts > 3:
            errors.append(f"ATTEMPT_BOUNDS:{cid}:{attempts}")

    return {
        "status": "PASSED" if not errors else "FAILED",
        "promotion_ready": not errors,
        "errors": errors,
        "claimed_total": claimed,
        "processed_unique": len(seen),
        "generated_delta": int(after_generated) - int(before_generated),
        "before_ledger": dict(before_ledger),
        "after_ledger": dict(after_ledger),
        "stop_reason": drain.get("stop_reason"),
        "micro_batches_run": int(drain.get("micro_batches_run") or 0),
    }


def certify_story_volume(*, batch_size=5, max_batches=20, time_budget_seconds=1200,
                         min_claimed=25):
    readiness = engine_bootstrap.check_engine_readiness()
    if not readiness.get("ready"):
        return {
            "certification": "STORY_PRODUCTION_VOLUME",
            "status": "BLOCKED",
            "promotion_ready": False,
            "errors": [readiness.get("reason_code") or "ENGINE_NOT_READY"],
        }

    conn = engine_bootstrap.connect()
    try:
        before_ledger = _ledger(conn)
        before_generated = _generated_total(conn)
    finally:
        conn.close()

    drain = drain_story_queue(
        batch_size=batch_size,
        max_batches=max_batches,
        time_budget_seconds=time_budget_seconds,
        include_deep_chains=False,
    )

    ids = []
    for run in drain.get("runs") or []:
        for example in run.get("examples") or []:
            cid = example.get("candidate_id")
            if cid:
                ids.append(str(cid))

    conn = engine_bootstrap.connect()
    conn.row_factory = sqlite3.Row
    try:
        after_ledger = _ledger(conn)
        after_generated = _generated_total(conn)
        processed_rows = []
        if ids:
            marks = ",".join("?" for _ in ids)
            processed_rows = [
                dict(r) for r in conn.execute(
                    f"""SELECT candidate_id,state,attempts,generated_question_count
                        FROM story_candidate_processing
                        WHERE candidate_id IN ({marks})""",
                    ids,
                ).fetchall()
            ]
    finally:
        conn.close()

    verdict = evaluate_volume_result(
        before_ledger=before_ledger,
        after_ledger=after_ledger,
        before_generated=before_generated,
        after_generated=after_generated,
        drain=drain,
        processed_rows=processed_rows,
        min_claimed=min_claimed,
    )
    verdict.update({
        "certification": "STORY_PRODUCTION_VOLUME",
        "database_version": readiness.get("database_version"),
        "database_size_bytes": readiness.get("db_size_bytes"),
        "batch_size": int(batch_size),
        "max_batches": int(max_batches),
        "time_budget_seconds": int(time_budget_seconds),
        "drain_counts": drain.get("counts") or {},
    })
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=5)
    ap.add_argument("--max-batches", type=int, default=20)
    ap.add_argument("--time-budget-seconds", type=int, default=1200)
    ap.add_argument("--min-claimed", type=int, default=25)
    args = ap.parse_args()
    result = certify_story_volume(
        batch_size=args.batch_size,
        max_batches=args.max_batches,
        time_budget_seconds=args.time_budget_seconds,
        min_claimed=args.min_claimed,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result.get("promotion_ready") else 1)


if __name__ == "__main__":
    main()
