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


_STALE_LOCKED_REFRESH_AGE_HOURS = 12.0  # roughly 2x the longest real gameday-trigger gap (see netlify.toml)
_FAILED_REFRESH_STATUSES = frozenset({
    "FAILED_RESTORED", "FAILED_STALE", "FAILED_BACKUP", "SOURCE_NOT_YET_PUBLISHED",
})


def _classify_health(week, refresh: dict, slate_game_count: int, stale_locked_count: int) -> str:
    """P0.10/P0.11: a single, honest top-level verdict a player-experience
    check (or a future self-healing job) can act on without re-deriving
    the same logic every caller previously had to. Real priority order --
    a week-resolution failure is worse than a stale refresh, which is
    worse than an empty slate, which is worse than merely-stale-looking
    per-game data:

    1. WEEK_RESOLUTION_ERROR -- resolve_current_week() itself returned
       None; nothing downstream can be trusted.
    2. EMPTY_SLATE -- a week resolved, but build_package() found zero real
       games for it (a real, disclosed shortfall, not a crash).
    3. REFRESH_FAILED -- the underlying games dataset's last recorded
       run is itself a real failure state, not merely old.
    4. STALE -- one or more games are past their own real kickoff (plus
       the disclosed IN_PROGRESS grace window) with NO real score yet
       (derive_pending_status() returning 'UNKNOWN') -- the direct,
       per-game symptom of a refresh not actually reaching this data,
       not a guess from refresh age alone. Also fires on a merely-old
       last-successful-refresh timestamp even with no stuck game yet,
       since that's still a real leading indicator.
    5. SLATE_OUT_OF_SYNC -- reserved for an architecture that caches or
       separately publishes a slate from the live tables; THIS codebase's
       get_pickem_view()/build_package() always re-derive the slate live,
       every request, with no cache or publish step in between (see
       gateway/services/public_pickem.py's own module docstring) -- so
       this status is structurally unreachable here, never returned, kept
       in the vocabulary only so a future architecture change that DID
       add caching would have a real status to report drift with.
    6. HEALTHY -- none of the above.
    """
    if week is None:
        return "WEEK_RESOLUTION_ERROR"
    if slate_game_count == 0:
        return "EMPTY_SLATE"
    if refresh["last_status"] in _FAILED_REFRESH_STATUSES:
        return "REFRESH_FAILED"
    if stale_locked_count > 0:
        return "STALE"
    if refresh["age_hours"] is not None and refresh["age_hours"] > _STALE_LOCKED_REFRESH_AGE_HOURS:
        return "STALE"
    return "HEALTHY"


def _league_pickem_health(league: str) -> dict:
    """Pick'em Automation pass (extended, Priority-Zero Pick'em closeout):
    /v1/admin/refresh/status already tracks per-dataset run freshness, and
    resolve_current_week() already derives the real current week, but
    nothing combined them into a single, Pick'em-aware view of what a real
    PLAYER would actually see right now -- an operator previously had to
    manually cross-reference two unrelated admin routes and a live game
    fetch to answer "is Pick'em actually healthy right now?". Every number
    here is a live read of already-existing real state (the exact same
    build_package()/live_game_statuses() calls the real public route
    uses), never a new tracking mechanism, and never a cached/stale view
    of its own -- this function itself proves there is nothing to
    invalidate: it calls the identical dynamic code path a real player's
    request calls, so "does the health view agree with the public API"
    is true by construction, not by a separate sync step."""
    from tools.director_v04 import nl_schedule_bridge, weekly_pickem
    from . import admin_refresh

    variant = "NFL_WEEKLY_PICKEM" if league == "NFL" else "CFB_WEEKLY_PICKEM"
    season = datetime.now(timezone.utc).year

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, league, season)
    finally:
        c.close()

    refresh = _refresh_freshness(admin_refresh.refresh_status()[league.lower()]["games"])
    result = {
        "league": league, "season": season, "current_week": week, "refresh": refresh,
        # P0.10: explicit, not implied -- there is no separate slate build/
        # publish step to report a timestamp for; the slate is recomputed
        # from the live tables on every single request (see
        # gateway/services/public_pickem.py's get_pickem_view()).
        "slate_build": "dynamic-per-request (no separate publish/cache/build step exists)",
        "player_facing_api_freshness": "identical to `refresh` above -- the public route re-derives from the "
                                        "same live tables on every request, so there is no separate cache to lag.",
    }
    if week is None:
        result.update({
            "slate_game_count": 0, "next_kickoff": None, "last_kickoff": None,
            "open_count": None, "locked_count": None, "final_count": None, "voided_count": None,
            "graded_count": None, "ungraded_final_count": None, "stale_locked_count": None,
            "shortfall_reason": f"No real schedule exists yet for {league} {season}.",
            "status": "WEEK_RESOLUTION_ERROR",
        })
        return result

    package = weekly_pickem.build_package(f"pickem-health|{variant}|{season}|{week}", variant, season, week)
    game_ids = [g["game_id"] for g in package["games"]]
    statuses = weekly_pickem.live_game_statuses(variant, game_ids)

    counts = {"SCHEDULED": 0, "IN_PROGRESS": 0, "UNKNOWN": 0, "FINAL": 0, "POSTPONED": 0, "CANCELED": 0}
    kickoffs = []
    ungraded_finals = 0
    for gid in game_ids:
        s = statuses.get(gid) or {}
        live_status = s.get("status")
        counts[live_status] = counts.get(live_status, 0) + 1
        if s.get("kickoff_utc"):
            kickoffs.append(s["kickoff_utc"])
        if live_status == "FINAL" and s.get("winner_code") is None:
            ungraded_finals += 1

    open_count = counts["SCHEDULED"]
    # IN_PROGRESS = a real game within its own disclosed post-kickoff grace
    # window; UNKNOWN = that window has ALSO elapsed with still no real
    # score -- the precise, per-game "this refresh isn't reaching this
    # game" signal, not a guess from overall refresh age.
    locked_count = counts["IN_PROGRESS"] + counts["UNKNOWN"]
    stale_locked_count = counts["UNKNOWN"]
    final_count = counts["FINAL"]
    voided_count = counts["POSTPONED"] + counts["CANCELED"]

    result.update({
        "slate_game_count": len(game_ids),
        "next_kickoff": min(kickoffs) if kickoffs else None,
        "last_kickoff": max(kickoffs) if kickoffs else None,
        "open_count": open_count, "locked_count": locked_count,
        "final_count": final_count, "voided_count": voided_count,
        "graded_count": final_count - ungraded_finals,
        "ungraded_final_count": ungraded_finals,
        "stale_locked_count": stale_locked_count,
        "shortfall_reason": package.get("shortfall_reason"),
    })
    result["status"] = _classify_health(week, refresh, len(game_ids), stale_locked_count)
    return result


def pickem_health() -> dict:
    """GET /v1/admin/pickem/health -- see _league_pickem_health()'s own
    docstring for what this combines and why."""
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
