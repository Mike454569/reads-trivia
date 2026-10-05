"""Autonomous checkpointed Story Factory queue drain refresh.

This is intentionally separate from candidate harvest. Harvest can be slow and
network-heavy; this worker simply drains already-triaged, non-sensitive
candidates in small resumable batches throughout the day.

Safety:
- the Gateway's global refresh guard allows only one dataset refresh at a time;
- the processing ledger atomically claims candidates with BEGIN IMMEDIATE;
- each candidate is checkpointed independently;
- stale PROCESSING rows are reclaimed by the processor;
- runtime/cycle caps prevent a single invocation from monopolizing the gateway.
"""
from __future__ import annotations

import time
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.story_batch_processor import process_story_batch
from . import safety

LEAGUE = "MIXED"
DATASET = "story_checkpoint_process"
SOURCE_ID = "STORY_PROCESSING_LEDGER"

DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_CYCLES = 6
DEFAULT_MAX_SECONDS = 20 * 60


def run_story_processing_refresh(
    *,
    batch_size=DEFAULT_BATCH_SIZE,
    max_cycles=DEFAULT_MAX_CYCLES,
    max_seconds=DEFAULT_MAX_SECONDS,
):
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    run_id = safety.start_run(
        c,
        league=LEAGUE,
        dataset=DATASET,
        source_id=SOURCE_ID,
    )
    c.close()

    started = time.monotonic()
    cycles = []
    totals = Counter()
    stop_reason = "MAX_CYCLES"

    try:
        for cycle_index in range(max(1, int(max_cycles))):
            elapsed = time.monotonic() - started
            if elapsed >= max(30, int(max_seconds)):
                stop_reason = "MAX_RUNTIME"
                break

            result = process_story_batch(
                batch_size=max(1, int(batch_size)),
                max_attempts=3,
                stale_minutes=30,
                include_deep_chains=False,
            )
            cycles.append(result)

            claimed = int(result.get("claimed") or 0)
            totals["claimed"] += claimed
            totals["reclaimed_stale"] += int(result.get("reclaimed_stale") or 0)
            for key, value in (result.get("counts") or {}).items():
                totals[str(key)] += int(value or 0)

            # Empty claim means the queue is currently drained (or every
            # remaining candidate is terminal/review-only). Stop immediately.
            if claimed == 0:
                stop_reason = "QUEUE_EMPTY"
                break

            # Small pause releases pressure between transactions and avoids
            # hammering article sources while still making steady progress.
            if cycle_index + 1 < int(max_cycles):
                time.sleep(1.0)
        else:
            stop_reason = "MAX_CYCLES"

        final_ledger = cycles[-1].get("ledger", {}) if cycles else {}
        generated_total = (
            int(cycles[-1].get("generated_from_checkpointed_batches") or 0)
            if cycles else 0
        )
        elapsed_seconds = round(time.monotonic() - started, 3)

        detail = {
            "stop_reason": stop_reason,
            "cycles_completed": len(cycles),
            "batch_size": int(batch_size),
            "totals": dict(totals),
            "final_ledger": final_ledger,
            "generated_from_checkpointed_batches": generated_total,
            "elapsed_seconds": elapsed_seconds,
            "cycle_summaries": [
                {
                    "claimed": int(x.get("claimed") or 0),
                    "reclaimed_stale": int(x.get("reclaimed_stale") or 0),
                    "counts": x.get("counts") or {},
                    "ledger": x.get("ledger") or {},
                }
                for x in cycles
            ],
        }

        c = engine_bootstrap.connect()
        safety.finish_run(
            c,
            run_id,
            status="SUCCESS",
            rows_downloaded=0,
            rows_imported=int(totals.get("DONE", 0)),
            rows_rejected=int(totals.get("REVIEW_REQUIRED", 0))
                          + int(totals.get("FAILED_FINAL", 0)),
            no_op=(int(totals.get("claimed", 0)) == 0),
            detail=detail,
        )
        c.close()
        return {
            "status": "SUCCESS",
            "run_id": run_id,
            **detail,
        }
    except Exception as exc:
        c = engine_bootstrap.connect()
        safety.finish_run(
            c,
            run_id,
            status="FAILED",
            failure_reason=repr(exc),
            detail={
                "cycles_completed": len(cycles),
                "totals": dict(totals),
                "elapsed_seconds": round(time.monotonic() - started, 3),
            },
        )
        c.close()
        return {
            "status": "FAILED",
            "run_id": run_id,
            "reason": repr(exc),
            "cycles_completed": len(cycles),
            "totals": dict(totals),
        }


def last_run_status():
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    row = c.execute(
        """SELECT * FROM refresh_runs
           WHERE league=? AND dataset_name=?
           ORDER BY started_at DESC LIMIT 1""",
        (LEAGUE, DATASET),
    ).fetchone()
    c.close()
    return dict(row) if row else None
