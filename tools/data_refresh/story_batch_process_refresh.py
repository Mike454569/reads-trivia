"""Admin-triggerable checkpointed Story Factory queue drain."""
from __future__ import annotations

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.story_batch_drain import drain_story_queue
from . import safety

LEAGUE = "MIXED"
DATASET = "story_batch_process"
SOURCE_ID = "STORY_FACTORY_CHECKPOINT_QUEUE"


def run_story_batch_process():
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    run_id = safety.start_run(
        c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID
    )
    c.close()

    try:
        result = drain_story_queue(
            batch_size=5,
            max_batches=10,
            time_budget_seconds=900,
            include_deep_chains=False,
        )
        c = engine_bootstrap.connect()
        safety.finish_run(
            c,
            run_id,
            status="SUCCESS",
            rows_downloaded=0,
            rows_imported=int(result.get("claimed_total") or 0),
            rows_rejected=int(
                (result.get("counts") or {}).get("REVIEW_REQUIRED", 0)
            ),
            no_op=(int(result.get("claimed_total") or 0) == 0),
            detail={"story_factory": result},
        )
        c.close()
        return {
            "status": "SUCCESS",
            "run_id": run_id,
            "story_factory": result,
        }
    except Exception as exc:
        c = engine_bootstrap.connect()
        safety.finish_run(
            c,
            run_id,
            status="FAILED",
            failure_reason=repr(exc),
        )
        c.close()
        return {
            "status": "FAILED",
            "run_id": run_id,
            "reason": repr(exc),
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
