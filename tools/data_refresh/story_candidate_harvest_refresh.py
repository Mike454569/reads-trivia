"""Admin-triggerable bulk football-story candidate harvest.

This refresh runs the complete safe funnel: bulk candidate harvest, triage,
strict article/identity/evidence promotion, and immediate question generation.
Sensitive candidates remain review-only and are never auto-promoted.
"""
from __future__ import annotations

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.story_candidate_harvest import harvest_story_candidates
from tools.director_v05.story_candidate_triage import triage_candidates
from tools.director_v05.story_to_trivia_factory import run_story_to_trivia_factory
from . import safety

LEAGUE = "MIXED"
DATASET = "story_candidate_harvest"
SOURCE_ID = "GDELT_DOC_INDEX"


def run_story_candidate_harvest():
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    try:
        harvested = harvest_story_candidates()
        triaged = triage_candidates()
        factory = run_story_to_trivia_factory(limit=100)
        accepted = int(harvested.get("metrics",{}).get("accepted_candidates",0))
        c = engine_bootstrap.connect()
        safety.finish_run(
            c, run_id, status="SUCCESS",
            rows_downloaded=int(harvested.get("metrics",{}).get("raw_articles",0)),
            rows_imported=accepted,
            rows_rejected=int(harvested.get("metrics",{}).get("missing_url_or_title",0))
                          + int(harvested.get("metrics",{}).get("domain_mismatch",0)),
            no_op=(accepted == 0),
            detail={
                "queue_totals": harvested.get("queue_totals",{}),
                "family_totals": harvested.get("family_totals",{}),
                "triage_status_counts": triaged.get("status_counts",{}),
                "query_failures": harvested.get("metrics",{}).get("query_failures",0),
                "story_factory": {
                    "processed_candidates": factory.get("processed_candidates",0),
                    "decisions": factory.get("decisions",{}),
                    "generated_questions_this_run": factory.get("generated_questions_this_run",0),
                    "ready_question_total": factory.get("ready_question_total",0),
                },
            },
        )
        c.close()
        return {
            "status":"SUCCESS",
            "run_id":run_id,
            "harvest":harvested,
            "triage":triaged,
            "story_factory":factory,
        }
    except Exception as exc:
        c = engine_bootstrap.connect()
        safety.finish_run(
            c, run_id, status="FAILED",
            failure_reason=repr(exc),
        )
        c.close()
        return {"status":"FAILED","run_id":run_id,"reason":repr(exc)}


def last_run_status():
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    row = c.execute(
        "SELECT * FROM refresh_runs WHERE league=? AND dataset_name=? ORDER BY started_at DESC LIMIT 1",
        (LEAGUE,DATASET),
    ).fetchone()
    c.close()
    return dict(row) if row else None
