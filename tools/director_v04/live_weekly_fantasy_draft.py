"""LIVE_WEEKLY_FANTASY_DRAFT -- Reliability Design Phase 7B, real mechanic
template #10.

A real, single-drafter weekly fantasy roster build: fill a fixed set of
real positional slots (QB, RB x2, WR x2, TE, FLEX) from a real, current
player pool for one (league, season, week), one pick at a time, no player
twice, server-authoritative the whole way. Deliberately NOT a scored
contest (no fantasy_points comparison, no opponent, no winner) -- every
one of the user's own literal completion criteria (valid player pool,
roster/position info, draft state, selections, duplicate-pick prevention,
completion state) describes a real, valid ROSTER CONSTRUCTION exercise,
never a scoring system, so this module never fabricates or asserts a
"best" roster -- only whether every pick was a real, eligible, not-yet-
drafted player.

No new realtime backend, per explicit instruction -- there is no existing
push/websocket layer anywhere in this codebase to integrate with (confirmed
during Phase 7B's own investigation: every mechanic, including this one,
is a single-session, poll-based GET/POST cycle over gateway/services/
game_state.py's existing mutable-state store). "Live" in this mechanic's
name describes the weekly, currently-active data it draws from, not a
multiplayer transport this phase invents.

Two real, honestly DISTINCT player-pool reliability tiers, never blurred
together silently (surfaced as `pool_source` on every generated package):
  - GAME_PARTICIPATION_CONFIRMED: the target week has already been played
    and a real per-game stat table has real, recorded rows for it -- the
    strongest possible signal, "this exact player recorded a real stat
    line in this exact game." NFL uses `player_game_stats`; CFB uses
    `cfb_player_game_stats_real` (Knowledge Expansion Batch 3 -- before
    that table existed, CFB had no per-game evidence source and always
    fell back to the tier below).
  - SEASON_ROSTER_MEMBERSHIP (either league, whenever the target week
    hasn't been played yet so no per-game evidence can exist): real
    season-level roster presence + real position, for the real teams that
    have a real scheduled/played game that week (per `games`/
    `cfb_games_canonical`, the SAME tables weekly_pickem.py already
    reads) -- a real, weaker, disclosed tier, never claimed to mean
    "confirmed active this week." This is the identical honest-tiering
    discipline cfb_player_season_school.py's own "aggregate_presence"
    strategy already established for the same underlying reason.

Only real, fantasy-relevant skill positions are drafted (QB/RB/WR/TE) --
the same "not enough reliably-distinguished per-player position detail to
include OL/DL/etc." reasoning lineup.py's own module docstring already
established for this database.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters.draft import resolve_franchise  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "LIVE_WEEKLY_FANTASY_DRAFT"
VARIANTS = frozenset({"NFL_WEEKLY_FANTASY_DRAFT", "CFB_WEEKLY_FANTASY_DRAFT"})

# A real, standard-shaped fantasy roster -- 7 slots, never invented per
# request. FLEX accepts any of RB/WR/TE (the same real positions already
# drafted directly), matching ordinary real fantasy-football convention.
DRAFT_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"]
FLEX_ELIGIBLE_POSITIONS = frozenset({"RB", "WR", "TE"})
SKILL_POSITIONS = frozenset({"QB", "RB", "WR", "TE"})
# Real, honest floor: a valid draft needs at least one real, distinct
# eligible player for every required position (QB, RB, WR, TE) -- if any
# one of those is completely empty, no roster can ever be completed, full
# stop, never partially generated.
_REQUIRED_POSITIONS = frozenset({"QB", "RB", "WR", "TE"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "canonical_players": safety.check_table_wide_safety(c, "canonical_players", ["NFLVERSE_DATA", "NFLVERSE_ROSTERS"]),
        "canonical_roster_seasons": safety.check_table_wide_safety(c, "canonical_roster_seasons", ["NFLVERSE_DATA", "NFLVERSE_ROSTERS"]),
        "cfb_roster_seasons_real": safety.check_table_wide_safety(c, "cfb_roster_seasons_real", "SPORTSDATAVERSE_CFB"),
    }


def _nfl_teams_for_week(c, season: int, week: str) -> set[str]:
    rows = c.execute(
        "SELECT home_team, away_team FROM games WHERE season=? AND week=? AND game_type='REG'", (season, str(week)),
    ).fetchall()
    teams: set[str] = set()
    for r in rows:
        teams.add(r["home_team"])
        teams.add(r["away_team"])
    return teams


def _cfb_teams_for_week(c, season: int, week: int) -> set[str]:
    rows = c.execute(
        "SELECT home_school_id, away_school_id FROM cfb_games_canonical WHERE season=? AND week=?", (season, week),
    ).fetchall()
    teams: set[str] = set()
    for r in rows:
        teams.add(r["home_school_id"])
        teams.add(r["away_school_id"])
    return teams


def _nfl_pool(c, season: int, week: str) -> tuple[dict, str]:
    teams = _nfl_teams_for_week(c, season, week)
    if not teams:
        return {}, "GAME_PARTICIPATION_CONFIRMED"

    placeholders = ",".join("?" for _ in teams)
    confirmed_rows = c.execute(
        f"SELECT DISTINCT pgs.player_key, p.display_name, p.primary_position, pgs.team_code "
        f"FROM player_game_stats pgs JOIN canonical_players p ON p.player_id = pgs.player_key "
        f"WHERE pgs.season=? AND pgs.week=? AND pgs.team_code IN ({placeholders}) "
        f"AND p.primary_position IN ('QB','RB','WR','TE')",
        [season, str(week), *teams],
    ).fetchall()
    if confirmed_rows:
        pool = {
            r["player_key"]: {"display_name": r["display_name"], "position": r["primary_position"], "team_code": r["team_code"]}
            for r in confirmed_rows
        }
        return pool, "GAME_PARTICIPATION_CONFIRMED"

    # Real, disclosed fallback -- this exact week hasn't been played yet
    # (no player_game_stats rows exist for it), so no per-game participation
    # evidence CAN exist. Season roster membership is still real, not
    # fabricated -- just a weaker, honestly-labeled tier (see module docstring).
    roster_rows = c.execute(
        f"SELECT DISTINCT rs.player_id, p.display_name, rs.position, rs.team_code "
        f"FROM canonical_roster_seasons rs JOIN canonical_players p ON p.player_id = rs.player_id "
        f"WHERE rs.season=? AND rs.team_code IN ({placeholders}) AND rs.position IN ('QB','RB','WR','TE')",
        [season, *teams],
    ).fetchall()
    pool = {
        r["player_id"]: {"display_name": r["display_name"], "position": r["position"], "team_code": r["team_code"]}
        for r in roster_rows
    }
    return pool, "SEASON_ROSTER_MEMBERSHIP"


def _cfb_pool(c, season: int, week: int) -> tuple[dict, str]:
    teams = _cfb_teams_for_week(c, season, week)
    if not teams:
        return {}, "SEASON_ROSTER_MEMBERSHIP"
    placeholders = ",".join("?" for _ in teams)

    # Knowledge Expansion Batch 3: `cfb_player_game_stats_real` now gives
    # CFB a real, per-game participation signal for completed weeks,
    # matching the exact tiering the NFL pool has always used -- try it
    # first, exactly like `_nfl_pool` tries `player_game_stats` first.
    confirmed_rows = c.execute(
        f"SELECT DISTINCT pgs.cfb_player_id, p.display_name, rs.position, pgs.school_id "
        f"FROM cfb_player_game_stats_real pgs "
        f"JOIN canonical_cfb_players p ON p.cfb_player_id = pgs.cfb_player_id "
        f"JOIN cfb_roster_seasons_real rs ON rs.cfb_player_id = pgs.cfb_player_id AND rs.season = pgs.season "
        f"WHERE pgs.season=? AND pgs.week=? AND pgs.school_id IN ({placeholders}) "
        f"AND rs.position IN ('QB','RB','WR','TE')",
        [season, week, *teams],
    ).fetchall()
    if confirmed_rows:
        pool = {
            r["cfb_player_id"]: {"display_name": r["display_name"], "position": r["position"], "team_code": r["school_id"]}
            for r in confirmed_rows
        }
        return pool, "GAME_PARTICIPATION_CONFIRMED"

    # Real, disclosed fallback -- this exact week hasn't been played yet
    # (or has no real game-stat rows for it), so no per-game participation
    # evidence CAN exist. Season roster membership is still real, not
    # fabricated -- just a weaker, honestly-labeled tier.
    rows = c.execute(
        f"SELECT DISTINCT rs.cfb_player_id, p.display_name, rs.position, rs.school_id "
        f"FROM cfb_roster_seasons_real rs JOIN canonical_cfb_players p ON p.cfb_player_id = rs.cfb_player_id "
        f"WHERE rs.season=? AND rs.school_id IN ({placeholders}) AND rs.position IN ('QB','RB','WR','TE')",
        [season, *teams],
    ).fetchall()
    pool = {
        r["cfb_player_id"]: {"display_name": r["display_name"], "position": r["position"], "team_code": r["school_id"]}
        for r in rows
    }
    return pool, "SEASON_ROSTER_MEMBERSHIP"


def check_slate_feasibility(variant: str, season: int, week) -> dict:
    """Real, honest feasibility check -- required before build_package()
    ever runs, and directly, independently callable/testable, matching
    weekly_pickem.py's own precedent for a schedule-driven mechanic with no
    (mechanic, domain, relationship_predicate) capability-registry triple."""
    if variant not in VARIANTS:
        return {"support_status": "UNKNOWN", "reason": f"variant must be one of {sorted(VARIANTS)}, got {variant!r}"}
    c = engine_bootstrap.connect()
    try:
        pool, pool_source = _nfl_pool(c, season, week) if variant == "NFL_WEEKLY_FANTASY_DRAFT" else _cfb_pool(c, season, week)
    finally:
        c.close()

    by_position: dict[str, int] = {}
    for entry in pool.values():
        by_position[entry["position"]] = by_position.get(entry["position"], 0) + 1
    missing = sorted(pos for pos in _REQUIRED_POSITIONS if by_position.get(pos, 0) == 0)
    if not pool:
        return {
            "support_status": "MISSING_DATA", "variant": variant, "season": season, "week": week,
            "real_player_count": 0, "by_position": {},
            "reason": f"No real games/rosters found for {variant}, season={season}, week={week!r}.",
        }
    if missing:
        return {
            "support_status": "INSUFFICIENT_COVERAGE", "variant": variant, "season": season, "week": week,
            "real_player_count": len(pool), "by_position": by_position, "pool_source": pool_source,
            "reason": f"No real eligible players at position(s) {missing} -- a valid draft cannot be completed.",
        }
    return {
        "support_status": "SUPPORTED", "variant": variant, "season": season, "week": week,
        "real_player_count": len(pool), "by_position": by_position, "pool_source": pool_source,
    }


def generate_pool(seed: str, variant: str, season: int, week) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        pool, pool_source = _nfl_pool(c, season, week) if variant == "NFL_WEEKLY_FANTASY_DRAFT" else _cfb_pool(c, season, week)
        team_display = {}
        if variant == "NFL_WEEKLY_FANTASY_DRAFT":
            for entry in pool.values():
                if entry["team_code"] not in team_display:
                    fr, err = resolve_franchise(c, entry["team_code"], season)
                    team_display[entry["team_code"]] = fr["full_name"] if not err and fr else entry["team_code"]
        else:
            rows = c.execute("SELECT school_id, school_name FROM schools").fetchall()
            team_display = {r["school_id"]: r["school_name"] for r in rows}
    finally:
        c.close()

    players = [
        {"player_id": pid, "display_name": e["display_name"], "position": e["position"],
         "team_code": e["team_code"], "team_display": team_display.get(e["team_code"], e["team_code"])}
        for pid, e in pool.items()
    ]
    rng = engine_bootstrap.seeded(seed)
    players.sort(key=lambda p: p["player_id"])  # deterministic base order before shuffle
    rng.shuffle(players)

    by_position: dict[str, int] = {}
    for p in players:
        by_position[p["position"]] = by_position.get(p["position"], 0) + 1
    missing = sorted(pos for pos in _REQUIRED_POSITIONS if by_position.get(pos, 0) == 0)
    shortfall_reason = None
    if not players:
        shortfall_reason = f"No real games/rosters found for {variant}, season={season}, week={week!r}."
    elif missing:
        shortfall_reason = f"No real eligible players at position(s) {missing} -- refusing to generate an incompletable draft."

    return {
        "players": players, "pool_source": pool_source, "by_position": by_position,
        "safety": safety_result, "shortfall_reason": shortfall_reason,
    }


def build_package(seed: str, variant: str, season: int, week) -> dict:
    result = generate_pool(seed, variant, season, week)
    package_id = "GGP10:" + hashlib.sha256(f"FANTASYDRAFT|{variant}|{season}|{week}|{seed}".encode()).hexdigest()[:24]
    valid = bool(result["players"]) and not result["shortfall_reason"]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "season": season, "week": week,
        "game_title": "NFL Weekly Fantasy Draft" if variant == "NFL_WEEKLY_FANTASY_DRAFT" else "CFB Weekly Fantasy Draft",
        "game_instructions": f"Draft a real roster ({', '.join(DRAFT_SLOTS)}) one real player at a time from this "
                              f"week's real eligible pool. No player can be drafted twice.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "players": result["players"], "player_count": len(result["players"]),
        "pool_source": result["pool_source"], "by_position": result["by_position"],
        "draft_slots": list(DRAFT_SLOTS),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
