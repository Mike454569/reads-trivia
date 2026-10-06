"""Story Corpus Growth v2.

One bounded production entry point that grows verified football lore from:
1) already-certified structured Engine sources, and
2) approved-domain story candidates that still pass triage + Story Factory gates.

Sensitive/legal/discipline candidates are harvested for review but never enter
the automatic processing queue.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap

from .populate_existing_lore import populate_existing
from .populate_nfl_trades import populate_nfl_trades
from .story_mining import mine_nfl_games
from .pbp_story_mining import mine_nfl_pbp
from .game_chaos_mining import mine_nfl_game_chaos
from .cfb_pbp_story_mining import mine_cfb_pbp
from .cfb_weather_lore import mine_cfb_weather_lore
from .nfl_contract_lore import mine_nfl_contract_lore
from .cfb_recruiting_lore import mine_cfb_recruiting_lore
from .official_rule_lore import populate_official_rule_lore
from .reviewed_story_corpus import ingest_reviewed_corpus
from .story_candidate_harvest import (
    APPROVED_DOMAINS,
    QUERY_FAMILIES,
    harvest_story_candidates,
)
from .story_candidate_triage import triage_candidates
from .story_batch_drain import drain_story_queue


# Rotate expensive news-index search families across three runs. Structured
# miners still run every time and are idempotent.
FAMILY_GROUPS = {
    "A": (
        "BIZARRE_MOMENT", "DRAFT_BUST", "TRADE_ODDITY",
        "COMEBACK_RETURN", "INFAMOUS_MISTAKE",
    ),
    "B": (
        "SIDELINE_INCIDENT", "COACHING_MELTDOWN", "CELEBRATION_CONTROVERSY",
        "RECORD_ODDITY", "RIVALRY_INCIDENT",
    ),
    "C": (
        "RECRUITING_CHAOS", "TRANSFER_NIL_CHAOS", "PLAYOFF_FORGOTTEN",
        "OFF_FIELD_ODDITY", "DISCIPLINE_LEGAL",
    ),
}


def _event_count(conn):
    return int(conn.execute(
        "SELECT COUNT(*) FROM universal_event WHERE verification_status='VERIFIED'"
    ).fetchone()[0])


def _story_question_count(conn):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='story_generated_questions'"
    ).fetchone()
    if not row:
        return 0
    return int(conn.execute(
        "SELECT COUNT(*) FROM story_generated_questions "
        "WHERE status IN ('READY_FOR_BANK','READY_FOR_FORMAT_BANK')"
    ).fetchone()[0])


def grow_structured_corpus(*, pbp_game_limit=None, row_limit=None):
    c = engine_bootstrap.connect()
    c.execute("PRAGMA busy_timeout=30000")
    before = _event_count(c)
    results = {}
    try:
        results["existing"] = populate_existing(c)
        results["nfl_trades"] = populate_nfl_trades(c)
        results["nfl_game_stories"] = mine_nfl_games(c, limit=pbp_game_limit)
        results["nfl_pbp"] = mine_nfl_pbp(c, limit_games=pbp_game_limit)
        results["nfl_game_chaos"] = mine_nfl_game_chaos(c, limit_games=pbp_game_limit)
        results["cfb_pbp"] = mine_cfb_pbp(c, limit_games=pbp_game_limit)
        results["cfb_weather"] = mine_cfb_weather_lore(c, limit_games=pbp_game_limit)
        results["nfl_contracts"] = mine_nfl_contract_lore(c, limit_rows=row_limit)
        results["cfb_recruiting"] = mine_cfb_recruiting_lore(c, limit_rows=row_limit)
        results["official_rules"] = populate_official_rule_lore(c)
        results["reviewed_corpus"] = ingest_reviewed_corpus(c)
        after = _event_count(c)
    finally:
        c.close()
    return {
        "before_verified_events": before,
        "after_verified_events": after,
        "verified_event_delta": after - before,
        "miners": results,
    }


def grow_external_story_queue(
    *,
    family_group="A",
    max_records_per_query=75,
    timespan="1y",
    domains=APPROVED_DOMAINS,
    drain_batch_size=10,
    drain_max_batches=12,
    drain_time_budget_seconds=1200,
):
    key = str(family_group or "A").upper()
    if key not in FAMILY_GROUPS:
        raise ValueError("family_group must be A, B, or C")
    selected = {
        family: QUERY_FAMILIES[family]
        for family in FAMILY_GROUPS[key]
        if family in QUERY_FAMILIES
    }
    harvest = harvest_story_candidates(
        domains=domains,
        query_families=selected,
        max_records_per_query=max_records_per_query,
        timespan=timespan,
        sleep_seconds=0.35,
    )
    triage = triage_candidates()
    drain = drain_story_queue(
        batch_size=drain_batch_size,
        max_batches=drain_max_batches,
        time_budget_seconds=drain_time_budget_seconds,
        include_deep_chains=False,
    )
    return {
        "family_group": key,
        "families": list(selected),
        "harvest": harvest,
        "triage": triage,
        "drain": drain,
    }


def run_growth(
    *,
    family_group="A",
    structured=True,
    external=True,
    max_records_per_query=75,
    timespan="1y",
    pbp_game_limit=None,
    row_limit=None,
    drain_batch_size=10,
    drain_max_batches=12,
    drain_time_budget_seconds=1200,
):
    before_conn = engine_bootstrap.connect()
    try:
        before = {
            "verified_events": _event_count(before_conn),
            "ready_story_questions": _story_question_count(before_conn),
        }
    finally:
        before_conn.close()

    result = {"before": before}
    if structured:
        result["structured"] = grow_structured_corpus(
            pbp_game_limit=pbp_game_limit,
            row_limit=row_limit,
        )
    if external:
        result["external"] = grow_external_story_queue(
            family_group=family_group,
            max_records_per_query=max_records_per_query,
            timespan=timespan,
            drain_batch_size=drain_batch_size,
            drain_max_batches=drain_max_batches,
            drain_time_budget_seconds=drain_time_budget_seconds,
        )

    after_conn = engine_bootstrap.connect()
    try:
        after = {
            "verified_events": _event_count(after_conn),
            "ready_story_questions": _story_question_count(after_conn),
        }
        family_counts = {
            str(r["event_type"]): int(r["n"])
            for r in after_conn.execute(
                "SELECT event_type,COUNT(*) n FROM universal_event "
                "WHERE verification_status='VERIFIED' GROUP BY event_type ORDER BY n DESC"
            ).fetchall()
        }
    finally:
        after_conn.close()

    result["after"] = after
    result["delta"] = {
        "verified_events": after["verified_events"] - before["verified_events"],
        "ready_story_questions": after["ready_story_questions"] - before["ready_story_questions"],
    }
    result["event_type_totals"] = family_counts
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family-group", choices=sorted(FAMILY_GROUPS), default="A")
    ap.add_argument("--structured-only", action="store_true")
    ap.add_argument("--external-only", action="store_true")
    ap.add_argument("--max-records-per-query", type=int, default=75)
    ap.add_argument("--timespan", default="1y")
    ap.add_argument("--pbp-game-limit", type=int)
    ap.add_argument("--row-limit", type=int)
    ap.add_argument("--drain-batch-size", type=int, default=10)
    ap.add_argument("--drain-max-batches", type=int, default=12)
    ap.add_argument("--drain-time-budget-seconds", type=int, default=1200)
    args = ap.parse_args()

    if args.structured_only and args.external_only:
        raise SystemExit("choose at most one of --structured-only/--external-only")
    result = run_growth(
        family_group=args.family_group,
        structured=not args.external_only,
        external=not args.structured_only,
        max_records_per_query=args.max_records_per_query,
        timespan=args.timespan,
        pbp_game_limit=args.pbp_game_limit,
        row_limit=args.row_limit,
        drain_batch_size=args.drain_batch_size,
        drain_max_batches=args.drain_max_batches,
        drain_time_budget_seconds=args.drain_time_budget_seconds,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
