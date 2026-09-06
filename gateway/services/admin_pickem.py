"""Reads Engine Gateway -- admin-only POSTPONED/CANCELED game-status
override (Dynamic Weekly Pick'em pass).

Confirmed directly against both real upstream schedule sources
(nflverse's games.csv, cfbfastR's schedules CSV) that neither ever
carries a postponed/canceled signal -- a canceled game is simply absent
as a row, never flagged. So this is the ONLY way a game's `status` column
ever becomes POSTPONED/CANCELED -- a real, disclosed manual override, not
automated detection. Every call is audit-logged (oplog.record_event) with
the human-supplied `reason`, so an override is always traceable to a real
decision, never a silent mutation.

Small, single-row UPDATE on an already-existing game_id -- no backup step
(unlike tools/data_refresh/*.py's bulk refreshes, this never risks more
than one row, and the row's prior value is always recoverable by another
admin call)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

from ..errors import GatewayError
from . import oplog

_TABLE_FOR_LEAGUE = {"NFL": "games", "CFB": "cfb_games_canonical"}


def _refresh_freshness(run: dict | None) -> dict:
    """Real staleness derived from admin_refresh.py's own last-run record
    for the games dataset -- never a separate tracking mechanism, just a
    read of what already exists. `age_hours` is None when no successful
    run has ever completed (a real, honest "never" state, not a fabricated
    0)."""
    if not run:
        return {"last_success_at": None, "age_hours": None, "last_status": None}
    finished_at = run.get("finished_at")
    age_hours = None
    if finished_at and run.get("status") == "SUCCESS":
        try:
            finished_dt = datetime.fromisoformat(finished_at)
            if finished_dt.tzinfo is None:
                finished_dt = finished_dt.replace(tzinfo=timezone.utc)
            age_hours = round((datetime.now(timezone.utc) - finished_dt).total_seconds() / 3600, 1)
        except ValueError:
            age_hours = None
    return {
        "last_success_at": finished_at if run.get("status") == "SUCCESS" else None,
        "age_hours": age_hours,
        "last_status": run.get("status"),
    }


def _league_pickem_health(league: str) -> dict:
    """Pick'em Automation pass: a real gap the audit for that pass found --
    /v1/admin/refresh/status already tracks per-dataset run freshness, and
    resolve_current_week() already derives the real current week, but
    nothing combined them into a single, Pick'em-aware view (current week,
    real upcoming/final game counts for that week, and whether the
    underlying schedule data is stale) -- an operator previously had to
    manually cross-reference two unrelated admin routes and a live game
    fetch to answer "is Pick'em actually healthy right now?". Every number
    here is a live read of already-existing real state, never a new
    tracking mechanism of its own."""
    from tools.director_v04 import nl_schedule_bridge, weekly_pickem
    from . import admin_refresh

    variant = "NFL_WEEKLY_PICKEM" if league == "NFL" else "CFB_WEEKLY_PICKEM"
    season = datetime.now(timezone.utc).year

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, league, season)
    finally:
        c.close()

    result = {
        "league": league, "season": season, "current_week": week,
        "refresh": _refresh_freshness(admin_refresh.refresh_status()[league.lower()]["games"]),
    }
    if week is None:
        result["upcoming_count"] = None
        result["final_count"] = None
        result["voided_count"] = None
        result["shortfall_reason"] = f"No real schedule exists yet for {league} {season}."
        return result

    package = weekly_pickem.build_package(f"pickem-health|{variant}|{season}|{week}", variant, season, week)
    game_ids = [g["game_id"] for g in package["games"]]
    statuses = weekly_pickem.live_game_statuses(variant, game_ids)
    counts = {"FINAL": 0, "VOID": 0, "UPCOMING": 0}
    for gid in game_ids:
        live_status = (statuses.get(gid) or {}).get("status")
        if live_status == "FINAL":
            counts["FINAL"] += 1
        elif live_status in ("POSTPONED", "CANCELED"):
            counts["VOID"] += 1
        else:
            counts["UPCOMING"] += 1

    result["upcoming_count"] = counts["UPCOMING"]
    result["final_count"] = counts["FINAL"]
    result["voided_count"] = counts["VOID"]
    result["total_games_this_week"] = len(game_ids)
    result["shortfall_reason"] = package.get("shortfall_reason")
    return result


def pickem_health() -> dict:
    """GET /v1/admin/pickem/health -- see _league_pickem_health()'s own
    docstring for what this combines and why. A refresh whose age_hours
    exceeds a real gameday-window multiple (roughly 2x the longest gap
    between scheduled triggers -- see netlify.toml's own gameday-trigger
    comments) or whose last_status isn't SUCCESS is the honest signal an
    operator should treat as "Pick'em data may be stale," reported here
    as plain fields rather than a single opaque health/unhealthy verdict,
    since what counts as "too stale" legitimately differs by day of week
    (a Tuesday morning gap is normal; a gap spanning a real Sunday is not)."""
    return {"nfl": _league_pickem_health("NFL"), "cfb": _league_pickem_health("CFB")}


def set_game_status(*, league: str, game_id: str, status: str, reason: str) -> dict:
    table = _TABLE_FOR_LEAGUE.get(league)
    if table is None:
        raise GatewayError("INVALID_MODE", f"league must be one of {sorted(_TABLE_FOR_LEAGUE)}.")

    c = engine_bootstrap.connect()
    try:
        row = c.execute(f"SELECT game_id, status FROM {table} WHERE game_id=?", (game_id,)).fetchone()
        if row is None:
            raise GatewayError("NOT_FOUND", f"No such {league} game_id: {game_id!r}.")
        previous_status = row["status"]
        now = datetime.now(timezone.utc).isoformat()
        c.execute(f"UPDATE {table} SET status=?, updated_at=? WHERE game_id=?", (status, now, game_id))
        c.commit()
    finally:
        c.close()

    oplog.record_event(
        "admin_pickem_status_override", league=league, game_id=game_id,
        previous_status=previous_status, new_status=status, reason=reason,
    )
    return {"league": league, "game_id": game_id, "previous_status": previous_status, "status": status}
