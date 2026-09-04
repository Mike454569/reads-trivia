"""Reads Engine Gateway -- public, unauthenticated Weekly Pick'em (Dynamic
Weekly Pick'em pass).

WEEKLY_PICKEM was deliberately left admin-only by an earlier pass
(gateway/services/public_mechanics.py's own module docstring: "genuinely
multi-user/room-shaped... needs real new session/room infrastructure...
exactly the kind of redesign this punch-list explicitly excludes"). This
module is that infrastructure -- built, per explicit project direction, on
a lightweight unauthenticated `client_id` (the same pattern the frontend
already uses for its Firestore leaderboard, app.js's getClientId(), now
also accepted here and trusted by possession -- not real verified auth)
rather than a new account system.

Deliberately does NOT use packages.py/game_state.py the way every other
public mechanic route does. Those exist to make an otherwise-ephemeral
generated round resumable by `round_id` -- Pick'em doesn't need that: the
"round" a player resumes is already fully identified by
`(league, season, week)` (the real schedule itself), which
tools/director_v04/pickem_store.py's real `pickem_picks` table already
keys picks on directly. Re-deriving a fresh, in-memory package on every
request (via weekly_pickem.build_package(), same as the admin route)
avoids a real, otherwise-unavoidable problem content-addressed storage
would hit here: a genuine schedule reschedule changes a package's real
content (kickoff) without changing its package_id (a hash of
variant|season|week|seed only), which packages.save_package() correctly
treats as a PackageCollision -- exactly the kind of collision a
high-frequency public route would hit constantly. Skipping persistence
entirely sidesteps it rather than working around it.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .. import config
from ..errors import GatewayError
from . import oplog

_LEAGUE_TO_VARIANT = {"NFL": "NFL_WEEKLY_PICKEM", "CFB": "CFB_WEEKLY_PICKEM"}


def _current_season() -> int:
    # Same real, non-arbitrary convention nl_schedule_bridge.py/
    # nfl_refresh.py/cfb_refresh.py's own _current_season() already use --
    # a season is named for the calendar year it plays in.
    return datetime.now(timezone.utc).year


def _resolve(league: str, season, week):
    from tools.director_v04 import nl_schedule_bridge
    from tools.quiz_export import engine as engine_bootstrap

    league_upper = (league or "").upper()
    variant = _LEAGUE_TO_VARIANT.get(league_upper)
    if variant is None:
        raise GatewayError("INVALID_MODE", f"league must be one of {sorted(_LEAGUE_TO_VARIANT)}.")

    if season is not None and week is not None:
        return variant, league_upper, int(season), str(week)

    resolved_season = int(season) if season is not None else _current_season()
    resolved_week = str(week) if week is not None else None
    if resolved_week is None:
        c = engine_bootstrap.connect()
        try:
            resolved_week = nl_schedule_bridge.resolve_current_week(c, league_upper, resolved_season)
        finally:
            c.close()
    if resolved_week is None:
        raise GatewayError(
            "NO_ELIGIBLE_GAME",
            f"No real schedule exists yet for {league_upper} {resolved_season} -- nothing to resolve a current week from.",
        )
    return variant, league_upper, resolved_season, resolved_week


def _build_package(variant: str, season: int, week: str, *, slate: str | None = None,
                    conference: str | None = None) -> dict:
    from tools.director_v04 import weekly_pickem

    # Deterministic, shared seed -- the slate itself isn't secret or
    # per-caller (every real player sees the exact same real games for a
    # given week/slate); only which GAMES appear is real, never who's
    # asking. slate/conference are folded in by build_cfb_slate_package
    # itself (see that function's own docstring for why).
    seed = f"public-pickem|{variant}|{season}|{week}"
    if variant == "CFB_WEEKLY_PICKEM":
        try:
            package = weekly_pickem.build_cfb_slate_package(
                seed, variant, season, week, slate=slate, conference=conference)
        except ValueError as e:
            raise GatewayError("INVALID_REQUEST", str(e))
    else:
        if slate and slate.upper() != "FULL":
            raise GatewayError("INVALID_REQUEST", "slate variants are only supported for CFB.")
        package = weekly_pickem.build_package(seed, variant, season, week)
    if package.get("qa_status") != "PASSED":
        raise GatewayError(
            "NO_ELIGIBLE_GAME",
            package.get("shortfall_reason") or f"No real games found for {variant}, season={season}, week={week!r}.",
        )
    return package


def get_pickem_view(*, league: str, season, week, client_id: str | None,
                     slate: str | None = None, conference: str | None = None) -> dict:
    if not config.PUBLIC_GAME_ENABLED:
        oplog.record_event("public_pickem_disabled", mode="pickem", reason="master_switch_off")
        raise GatewayError("SERVICE_UNAVAILABLE", "Public gameplay is temporarily disabled.")

    from tools.director_v02 import mechanic_engine
    from tools.director_v04 import pickem_store

    variant, league_upper, resolved_season, resolved_week = _resolve(league, season, week)
    package = _build_package(variant, resolved_season, resolved_week, slate=slate, conference=conference)

    picks = {}
    if client_id:
        try:
            picks = pickem_store.picks_for(client_id=client_id, league=league_upper, season=resolved_season, week=resolved_week)
        except pickem_store.InvalidClientId as e:
            raise GatewayError("INVALID_REQUEST", str(e))

    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", package, {"picks": picks})
    oplog.record_event("public_pickem_served", mode="pickem", league=league_upper,
                        season=resolved_season, week=resolved_week, game_count=view["game_count"],
                        slate=package.get("slate"))
    return {"league": league_upper, "season": resolved_season, "week": resolved_week,
            "slate": package.get("slate", "FULL"), "view": view}


def submit_pick(*, league: str, season, week, client_id: str, game_id: str, predicted_winner: str) -> dict:
    if not config.PUBLIC_GAME_ENABLED:
        oplog.record_event("public_pickem_disabled", mode="pickem", reason="master_switch_off")
        raise GatewayError("SERVICE_UNAVAILABLE", "Public gameplay is temporarily disabled.")

    from tools.director_v02 import mechanic_engine
    from tools.director_v04 import pickem_store

    variant, league_upper, resolved_season, resolved_week = _resolve(league, season, week)
    # ALWAYS the full real slate here, regardless of which slate the player
    # was looking at (Featured/Top25/.../Full) -- FULL is a strict
    # superset of every filtered slate, so a pick made while viewing a
    # 20-game Featured slate still validates correctly against the real
    # game the player actually clicked. This is the concrete mechanism
    # that keeps pick identity (client_id+league+season+week+game_id)
    # working identically across every slate variant -- never a
    # slate-scoped validation path.
    package = _build_package(variant, resolved_season, resolved_week, slate="FULL")

    try:
        picks = pickem_store.picks_for(client_id=client_id, league=league_upper, season=resolved_season, week=resolved_week)
    except pickem_store.InvalidClientId as e:
        raise GatewayError("INVALID_REQUEST", str(e))

    try:
        result, _ = mechanic_engine.evaluate_submission(
            "WEEKLY_PICKEM", package, {"picks": picks},
            {"game_id": game_id, "predicted_winner": predicted_winner},
        )
    except mechanic_engine.MechanicError as e:
        raise GatewayError("INVALID_REQUEST", str(e))

    pickem_store.upsert_pick(
        client_id=client_id, league=league_upper, season=resolved_season, week=resolved_week,
        game_id=game_id, predicted_winner=predicted_winner,
    )
    oplog.record_event("public_pickem_pick_saved", mode="pickem", league=league_upper,
                        season=resolved_season, week=resolved_week)
    return {"league": league_upper, "season": resolved_season, "week": resolved_week,
            "game_id": game_id, "predicted_winner": predicted_winner, "status": "SAVED"}
