"""NFL defensive play-by-play identity + real drives -- reusable
knowledge relationships (Knowledge Expansion Batch 4).

Built on `nfl_plays_defense_ext` (237,350 rows, 1999-2025, real GSIS-
resolved defensive identity) and `nfl_drives_real` (167,880 rows, real
`fixed_drive`-keyed summaries) -- both sourced from nflverse's own full
play-by-play release, the same NFLVERSE_DATA source `nfl_plays` already
uses. See tools/data_refresh/nfl_pbp_defense_drive_refresh.py for full
provenance and the real, measured identity-resolution methodology.
"""
from __future__ import annotations


def play_defensive_events(c, *, game_id: str, play_id: str) -> dict:
    """PLAY -> SACK_PLAYER / INTERCEPTOR / FORCED_FUMBLE_PLAYER /
    FUMBLE_RECOVERY_PLAYER (+ kicker/returner)."""
    row = c.execute(
        "SELECT * FROM nfl_plays_defense_ext WHERE game_id=? AND play_id=?", (game_id, play_id),
    ).fetchone()
    if row is None:
        return {"game_id": game_id, "play_id": play_id, "found": False}
    return {"found": True, **dict(row)}


def game_defensive_events(c, *, game_id: str) -> list[dict]:
    """GAME -> every real defensive-identity-bearing play."""
    rows = c.execute("SELECT * FROM nfl_plays_defense_ext WHERE game_id=?", (game_id,)).fetchall()
    return [dict(r) for r in rows]


def player_game_sacks(c, *, player_id: str, game_id: str) -> int:
    """PLAYER + GAME -> SACKS (full sacks + half-sacks counted as 0.5 each, matching real box-score convention)."""
    full = c.execute(
        "SELECT COUNT(*) FROM nfl_plays_defense_ext WHERE game_id=? AND sack_player_id=?", (game_id, player_id),
    ).fetchone()[0]
    half1 = c.execute(
        "SELECT COUNT(*) FROM nfl_plays_defense_ext WHERE game_id=? AND half_sack_1_player_id=?", (game_id, player_id),
    ).fetchone()[0]
    half2 = c.execute(
        "SELECT COUNT(*) FROM nfl_plays_defense_ext WHERE game_id=? AND half_sack_2_player_id=?", (game_id, player_id),
    ).fetchone()[0]
    return full + 0.5 * (half1 + half2)


def player_game_interceptions(c, *, player_id: str, game_id: str) -> int:
    """PLAYER + GAME -> INTERCEPTIONS (made)."""
    return c.execute(
        "SELECT COUNT(*) FROM nfl_plays_defense_ext WHERE game_id=? AND interception_player_id=?", (game_id, player_id),
    ).fetchone()[0]


def player_game_forced_fumbles(c, *, player_id: str, game_id: str) -> int:
    """PLAYER + GAME -> FORCED_FUMBLES."""
    return c.execute(
        "SELECT COUNT(*) FROM nfl_plays_defense_ext WHERE game_id=? AND "
        "(forced_fumble_player_1_id=? OR forced_fumble_player_2_id=?)", (game_id, player_id, player_id),
    ).fetchone()[0]


def player_game_fumble_recoveries(c, *, player_id: str, game_id: str) -> int:
    """PLAYER + GAME -> RECOVERIES."""
    return c.execute(
        "SELECT COUNT(*) FROM nfl_plays_defense_ext WHERE game_id=? AND "
        "(fumble_recovery_1_player_id=? OR fumble_recovery_2_player_id=?)", (game_id, player_id, player_id),
    ).fetchone()[0]


def player_sacked_qb_in_game(c, *, player_id: str, game_id: str) -> bool:
    """PLAYER -> SACKED_QB_IN_GAME."""
    return player_game_sacks(c, player_id=player_id, game_id=game_id) > 0


def player_intercepted_pass_in_game(c, *, player_id: str, game_id: str) -> bool:
    """PLAYER -> INTERCEPTED_PASS_IN_GAME."""
    return player_game_interceptions(c, player_id=player_id, game_id=game_id) > 0


# --- Drives ----------------------------------------------------------------------

def game_drives(c, *, game_id: str) -> list[dict]:
    """GAME -> DRIVES (+ OFFENSE, START/END, PLAYS, YARDS, RESULT, POINTS, TURNOVER, SCORING)."""
    rows = c.execute(
        "SELECT * FROM nfl_drives_real WHERE game_id=? ORDER BY drive_number", (game_id,),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        result = d.get("result_raw") or ""
        # Real, confirmed distinct `fixed_drive_result` values (see
        # tools/data_refresh/nfl_pbp_defense_drive_refresh.py docstring):
        # "Touchdown", "Field goal", "Safety", "Turnover", "Turnover on
        # downs", "Opp touchdown" (a turnover that became the OPPONENT's
        # defensive/special-teams score -- this offense scores 0, not 7),
        # "Punt", "Missed field goal", "End of half".
        d["is_turnover"] = result in ("Turnover", "Turnover on downs", "Opp touchdown")
        d["is_scoring"] = bool(d.get("ended_with_score"))
        if result == "Touchdown":
            d["points"] = 7
        elif result == "Field goal":
            d["points"] = 3
        elif result == "Safety":
            d["points"] = -2
        else:
            d["points"] = 0
        out.append(d)
    return out


def drive_result(c, *, game_id: str, drive_number: int) -> dict:
    """DRIVE -> RESULT (+ full drive summary)."""
    row = c.execute(
        "SELECT * FROM nfl_drives_real WHERE game_id=? AND drive_number=?", (game_id, drive_number),
    ).fetchone()
    if row is None:
        return {"game_id": game_id, "drive_number": drive_number, "found": False}
    return {"found": True, **dict(row)}


def game_drive_sequence(c, *, game_id: str) -> list[str]:
    """GAME -> DRIVE_SEQUENCE (real, ordered list of drive results)."""
    rows = c.execute(
        "SELECT result_raw FROM nfl_drives_real WHERE game_id=? ORDER BY drive_number", (game_id,),
    ).fetchall()
    return [r["result_raw"] for r in rows]


def team_season_drives(c, *, team_code: str, season: int) -> list[dict]:
    """TEAM + SEASON -> DRIVES (offense only)."""
    rows = c.execute(
        "SELECT * FROM nfl_drives_real WHERE offense_team=? AND season=? ORDER BY game_id, drive_number",
        (team_code, season),
    ).fetchall()
    return [dict(r) for r in rows]


# --- Coverage / eligibility -------------------------------------------------------

def defensive_identity_coverage(c, *, season: int | None = None) -> dict:
    # Real, disclosed data-hygiene note: the raw `*_gsis` tracking columns
    # hold '' (not NULL) for a row where that specific event didn't occur
    # -- an artifact of csv.DictReader returning '' for empty CSV cells.
    # The resolved `*_player_id` columns are unaffected (resolution always
    # treats '' as falsy before the canonical_players lookup); both real
    # and empty values are filtered out here explicitly.
    where = "WHERE season=?" if season else ""
    params = [season] if season else []
    total = c.execute(f"SELECT COUNT(*) FROM nfl_plays_defense_ext {where}", params).fetchone()[0]
    sack_total = c.execute(f"SELECT COUNT(*) FROM nfl_plays_defense_ext {where}{' AND' if where else 'WHERE'} sack_player_gsis IS NOT NULL AND sack_player_gsis != ''", params).fetchone()[0]
    sack_resolved = c.execute(f"SELECT COUNT(*) FROM nfl_plays_defense_ext {where}{' AND' if where else 'WHERE'} sack_player_id IS NOT NULL", params).fetchone()[0]
    int_total = c.execute(f"SELECT COUNT(*) FROM nfl_plays_defense_ext {where}{' AND' if where else 'WHERE'} interception_player_gsis IS NOT NULL AND interception_player_gsis != ''", params).fetchone()[0]
    int_resolved = c.execute(f"SELECT COUNT(*) FROM nfl_plays_defense_ext {where}{' AND' if where else 'WHERE'} interception_player_id IS NOT NULL", params).fetchone()[0]
    return {
        "total_defense_event_rows": total,
        "sack_events": sack_total, "sack_identity_resolved": sack_resolved,
        "sack_resolution_pct": round(100.0 * sack_resolved / sack_total, 1) if sack_total else 0.0,
        "interception_events": int_total, "interception_identity_resolved": int_resolved,
        "interception_resolution_pct": round(100.0 * int_resolved / int_total, 1) if int_total else 0.0,
    }


def eligibility_report(c) -> dict:
    def_total = c.execute("SELECT COUNT(*) FROM nfl_plays_defense_ext").fetchone()[0]
    drive_total = c.execute("SELECT COUNT(*) FROM nfl_drives_real").fetchone()[0]
    games_with_drives = c.execute("SELECT COUNT(DISTINCT game_id) FROM nfl_drives_real").fetchone()[0]
    seasons = c.execute("SELECT MIN(season), MAX(season) FROM nfl_drives_real").fetchone()
    return {
        "defense_event_rows": def_total, "drive_rows": drive_total,
        "games_with_drives": games_with_drives, "season_range": [seasons[0], seasons[1]],
    }
