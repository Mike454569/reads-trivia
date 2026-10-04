"""Drain the Story Factory queue through checkpointed micro-batches.

Each micro-batch is independently committed by story_batch_processor, so an
interruption loses at most the current candidate's uncommitted work. Completed
stories remain DONE and are never reclaimed.
"""
from __future__ import annotations

import json
import time
from collections import Counter

from .story_batch_processor import process_story_batch

DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_BATCHES = 10
DEFAULT_TIME_BUDGET_SECONDS = 900


def drain_story_queue(
    *,
    batch_size=DEFAULT_BATCH_SIZE,
    max_batches=DEFAULT_MAX_BATCHES,
    time_budget_seconds=DEFAULT_TIME_BUDGET_SECONDS,
    include_deep_chains=False,
):
    started = time.monotonic()
    runs = []
    totals = Counter()
    claimed_total = 0
    generated_total = 0

    for batch_number in range(1, max(1, int(max_batches)) + 1):
        if time.monotonic() - started >= max(30, int(time_budget_seconds)):
            break

        result = process_story_batch(
            batch_size=batch_size,
            max_attempts=3,
            stale_minutes=30,
            include_deep_chains=include_deep_chains,
        )
        claimed = int(result.get("claimed") or 0)
        claimed_total += claimed
        generated_total = max(
            generated_total,
            int(result.get("generated_from_checkpointed_batches") or 0),
        )
        totals.update(result.get("counts") or {})
        runs.append({
            "batch": batch_number,
            "claimed": claimed,
            "counts": result.get("counts") or {},
            "reclaimed_stale": int(result.get("reclaimed_stale") or 0),
            "ledger": result.get("ledger") or {},
        })

        # Queue exhausted or no currently claimable work.
        if claimed == 0:
            break

    final_ledger = runs[-1]["ledger"] if runs else {}
    return {
        "micro_batches_run": len(runs),
        "claimed_total": claimed_total,
        "counts": dict(totals),
        "generated_from_checkpointed_batches": generated_total,
        "final_ledger": final_ledger,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "include_deep_chains": bool(include_deep_chains),
        "runs": runs,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    ap.add_argument("--max-batches", type=int, default=DEFAULT_MAX_BATCHES)
    ap.add_argument(
        "--time-budget-seconds",
        type=int,
        default=DEFAULT_TIME_BUDGET_SECONDS,
    )
    ap.add_argument("--deep-chains", action="store_true")
    args = ap.parse_args()
    print(json.dumps(drain_story_queue(
        batch_size=args.batch_size,
        max_batches=args.max_batches,
        time_budget_seconds=args.time_budget_seconds,
        include_deep_chains=args.deep_chains,
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
