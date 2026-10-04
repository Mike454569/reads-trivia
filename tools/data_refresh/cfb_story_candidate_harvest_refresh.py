"""Admin-triggerable CFB-specific Story Factory candidate harvest."""
from __future__ import annotations

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.cfb_story_candidate_harvest import harvest_cfb_story_candidates
from tools.director_v05.story_candidate_triage import triage_candidates
from tools.director_v05.story_batch_processor import process_story_batch
from . import safety

LEAGUE = "CFB"
DATASET = "cfb_story_candidate_harvest"
SOURCE_ID = "GDELT_CFB_STORY_INDEX"


def run_cfb_story_candidate_harvest():
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    run_id = safety.start_run(
        c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID
    )
    c.close()

    try:
        harvested = harvest_cfb_story_candidates()
        triaged = triage_candidates()
        factory = process_story_batch(
            batch_size=5,
            max_attempts=3,
            stale_minutes=30,
            include_deep_chains=False,
        )
        accepted = int(
            harvested.get("metrics", {}).get("accepted_candidates", 0)
        )
        c = engine_bootstrap.connect()
        safety.finish_run(
            c,
            run_id,
            status="SUCCESS",
            rows_downloaded=int(
                harvested.get("metrics", {}).get("raw_articles", 0)
            ),
            rows_imported=accepted,
            rows_rejected=int(
                harvested.get("metrics", {}).get("missing_url_or_title", 0)
            )
            + int(
                harvested.get("metrics", {}).get("domain_mismatch", 0)
            ),
            no_op=(accepted == 0),
            detail={
                "cfb_family_totals": harvested.get("cfb_family_totals", {}),
                "school_names_used": harvested.get("school_names_used", 0),
                "query_jobs": harvested.get("query_jobs", 0),
                "triage_status_counts": triaged.get("status_counts", {}),
                "story_factory": factory,
            },
        )
        c.close()
        return {
            "status": "SUCCESS",
            "run_id": run_id,
            "harvest": harvested,
            "triage": triaged,
            "story_factory": factory,
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
