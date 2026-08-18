"""NFL Hall of Fame -- reusable knowledge relationships (Knowledge
Expansion Batch 2).

Built on `nfl_hof_inductees` (tools/data_refresh/nfl_hof_import.py) --
387 real inductees, 1963-2026, with a real player/non-player split
already applied at ingestion time. Every function here only ever
operates on `is_player=1` rows for PLAYER-shaped relationships; non-player
inductees (coaches, owners, executives) are exposed separately via
`non_player_inductees()`, never merged into the player-facing functions.
"""
from __future__ import annotations


def player_hof_status(c, *, player_id: str) -> dict:
    """PLAYER -> HALL_OF_FAME / HOF_CLASS_YEAR."""
    row = c.execute(
        "SELECT hof_id, class_year, position_raw FROM nfl_hof_inductees WHERE player_id=? AND is_player=1",
        (player_id,),
    ).fetchone()
    if row is None:
        return {"player_id": player_id, "is_hall_of_famer": False}
    return {"player_id": player_id, "is_hall_of_famer": True, "class_year": row["class_year"],
             "position_raw": row["position_raw"], "hof_id": row["hof_id"]}


def hof_class(c, *, class_year: int) -> list[dict]:
    """HOF_CLASS_YEAR -> PLAYERS (+ non-players, kept in a separate key)."""
    players = c.execute(
        "SELECT hof_id, inductee_name_raw, player_id, position_raw FROM nfl_hof_inductees "
        "WHERE class_year=? AND is_player=1", (class_year,),
    ).fetchall()
    non_players = c.execute(
        "SELECT hof_id, inductee_name_raw, position_raw FROM nfl_hof_inductees "
        "WHERE class_year=? AND is_player=0", (class_year,),
    ).fetchall()
    return {"class_year": class_year, "players": [dict(r) for r in players],
            "non_players": [dict(r) for r in non_players]}


def player_teams(c, *, hof_id: str) -> list[dict]:
    """HOF_PLAYER -> NFL_TEAMS (career team history, as listed on the real inductee page)."""
    rows = c.execute(
        "SELECT team_name_raw, years_raw, team_order FROM nfl_hof_inductee_teams "
        "WHERE hof_id=? ORDER BY team_order", (hof_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def college_hof_players(c, *, cfb_player_id: str) -> list[dict]:
    """COLLEGE -> HOF_PLAYERS, via the certified NFL<->CFB identity bridge
    -- only ever returns a real bridged match, never a name guess."""
    rows = c.execute(
        "SELECT h.hof_id, h.inductee_name_raw, h.class_year, h.position_raw FROM nfl_hof_inductees h "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.nfl_player_key = h.player_id "
        "WHERE b.cfb_player_id = ? AND h.is_player=1", (cfb_player_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def non_player_inductees(c, *, class_year: int | None = None) -> list[dict]:
    """Coaches/owners/executives/founders -- explicitly kept separate from
    the PLAYER relationships per the scoping decision in nfl_hof_import.py."""
    if class_year is not None:
        rows = c.execute(
            "SELECT hof_id, inductee_name_raw, class_year, position_raw FROM nfl_hof_inductees "
            "WHERE is_player=0 AND class_year=?", (class_year,),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT hof_id, inductee_name_raw, class_year, position_raw FROM nfl_hof_inductees WHERE is_player=0",
        ).fetchall()
    return [dict(r) for r in rows]


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM nfl_hof_inductees").fetchone()[0]
    players = c.execute("SELECT COUNT(*) FROM nfl_hof_inductees WHERE is_player=1").fetchone()[0]
    non_players = total - players
    resolved = c.execute("SELECT COUNT(*) FROM nfl_hof_inductees WHERE is_player=1 AND player_id IS NOT NULL").fetchone()[0]
    years = c.execute("SELECT MIN(class_year), MAX(class_year) FROM nfl_hof_inductees").fetchone()
    return {
        "total_inductees": total, "player_inductees": players, "non_player_inductees": non_players,
        "player_identity_resolved": resolved,
        "player_usable_percentage": round(100.0 * resolved / players, 1) if players else 0.0,
        "class_year_range": [years[0], years[1]],
    }
