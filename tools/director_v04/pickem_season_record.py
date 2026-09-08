"""Pick'em Season Record -- real, verified win/loss tracking across every
real week of a season, computed the same way Pick'em has always graded a
single week (mechanic_engine.client_safe_view("WEEKLY_PICKEM", ...)),
just summed across every real week that has already concluded.

Why this needs its own module rather than reusing get_pickem_view()
directly: that function (and every existing Pick'em route) is scoped to
ONE (season, week) -- exactly right for "what do I pick this week," wrong
for "how have I done all season." This module iterates
nl_schedule_bridge.weeks_concluded_so_far() (the same real week-enumeration
logic resolve_current_week() is itself built from -- see that module's own
docstring) and, for each real concluded week, builds the FULL slate (never
a filtered CFB slate like FEATURED/TOP25 -- a real pick made while viewing
any slate must still count, and the full slate is a strict superset of
every other slate) plus that week's real stored picks, then reuses the
EXACT SAME grading function every single-week Pick'em view already calls.
No new grading logic exists here -- this is purely aggregation across
real, already-graded weeks.

Real, honest caveat this module states explicitly rather than hiding:
weeks_concluded_so_far() only returns weeks whose OWN last real game has
already been played -- a week currently in progress (some games final,
some not) is intentionally excluded from the season total (it will be
picked up automatically once it concludes), the same "never grade off a
partial week" discipline the single-week view already applies per-game.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

_LEAGUE_TO_VARIANT = {"NFL": "NFL_WEEKLY_PICKEM", "CFB": "CFB_WEEKLY_PICKEM"}


def compute_season_record(*, client_id: str, league: str, season: int) -> dict:
    """Real, live-computed season record for one real (client_id, league,
    season) -- never cached, never precomputed off a snapshot, so it's
    always as current as the underlying games/cfb_games_canonical tables
    (the same real freshness guarantee every other Pick'em view already
    makes). Returns per_week detail plus season totals; a week with zero
    real picks made still appears (picks_made=0) so a caller can
    distinguish "you played and went 0-3" from "you never played this
    week" -- never silently dropped."""
    from tools.director_v02 import mechanic_engine
    from tools.director_v04 import nl_schedule_bridge, pickem_store, weekly_pickem

    league_upper = league.upper()
    if league_upper not in _LEAGUE_TO_VARIANT:
        raise ValueError(f"league must be one of {sorted(_LEAGUE_TO_VARIANT)}, got {league!r}")
    variant = _LEAGUE_TO_VARIANT[league_upper]

    c = engine_bootstrap.connect()
    try:
        weeks = nl_schedule_bridge.weeks_concluded_so_far(c, league_upper, season)
    finally:
        c.close()

    per_week = []
    total_correct = total_graded = total_voided = total_picks_made = 0
    weeks_played = 0
    for week in weeks:
        seed = f"public-pickem|{variant}|{season}|{week}"
        if variant == "CFB_WEEKLY_PICKEM":
            package = weekly_pickem.build_cfb_slate_package(seed, variant, season, week, slate="FULL", conference=None)
        else:
            package = weekly_pickem.build_package(seed, variant, season, week)
        if package.get("qa_status") != "PASSED":
            # A real, disclosed gap in this specific week's own schedule
            # data (not a season-record bug) -- skip it honestly rather
            # than crash the whole season aggregation over one bad week.
            per_week.append({"week": week, "error": package.get("shortfall_reason") or "no real games found"})
            continue
        picks = pickem_store.picks_for(client_id=client_id, league=league_upper, season=season, week=week)
        view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", package, {"picks": picks})
        if picks:
            weeks_played += 1
        total_correct += view["correct_count"]
        total_graded += view["graded_count"]
        total_voided += view["voided_count"]
        total_picks_made += view["picks_made"]
        per_week.append({
            "week": week, "picks_made": view["picks_made"], "graded_count": view["graded_count"],
            "correct_count": view["correct_count"], "voided_count": view["voided_count"],
        })

    win_pct = round(total_correct / total_graded, 4) if total_graded else None
    return {
        "client_id": client_id, "league": league_upper, "season": season,
        "weeks_concluded": len(weeks), "weeks_played": weeks_played,
        "total_picks_made": total_picks_made, "total_graded": total_graded,
        "total_correct": total_correct, "total_voided": total_voided,
        "win_pct": win_pct, "per_week": per_week,
    }
