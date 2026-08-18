"""NFL player hometown/high-school background -- reusable knowledge
relationships (Knowledge Expansion Batch 2).

Built on `nfl_player_background` (tools/data_refresh/
nfl_hometown_highschool_import.py) -- a real, disclosed sample scoped to
the 107 identity-resolved `nfl_hof_inductees` players, not the full NFL
player population. `birthplace_*` is exactly what Wikipedia's infobox
"Born" field says; there is deliberately no separate `hometown_*` --
see the import module's docstring for why that equivalence is disclosed,
not invented.
"""
from __future__ import annotations


def player_background(c, *, player_id: str) -> dict:
    """PLAYER -> BIRTHPLACE (city/state/country) + HIGH_SCHOOL (+city/state)."""
    row = c.execute("SELECT * FROM nfl_player_background WHERE player_id=?", (player_id,)).fetchone()
    if row is None:
        return {"player_id": player_id, "found": False}
    return {"found": True, **dict(row)}


def high_school_players(c, *, high_school_name: str) -> list[dict]:
    """HIGH_SCHOOL -> NFL_PLAYERS."""
    rows = c.execute(
        "SELECT player_id, display_name_raw, high_school_city, high_school_state FROM nfl_player_background "
        "WHERE high_school_name=?", (high_school_name,),
    ).fetchall()
    return [dict(r) for r in rows]


def city_players(c, *, city: str, kind: str = "birthplace") -> list[dict]:
    """CITY -> NFL_PLAYERS. `kind` is 'birthplace' or 'high_school' -- the
    two real, distinct location concepts this module tracks; never merged."""
    if kind not in ("birthplace", "high_school"):
        raise ValueError("kind must be 'birthplace' or 'high_school'")
    col = "birthplace_city" if kind == "birthplace" else "high_school_city"
    rows = c.execute(
        f"SELECT player_id, display_name_raw FROM nfl_player_background WHERE {col}=?", (city,),
    ).fetchall()
    return [dict(r) for r in rows]


def state_players(c, *, state: str, kind: str = "birthplace") -> list[dict]:
    """STATE -> NFL_PLAYERS."""
    if kind not in ("birthplace", "high_school"):
        raise ValueError("kind must be 'birthplace' or 'high_school'")
    col = "birthplace_state" if kind == "birthplace" else "high_school_state"
    rows = c.execute(
        f"SELECT player_id, display_name_raw FROM nfl_player_background WHERE {col}=?", (state,),
    ).fetchall()
    return [dict(r) for r in rows]


def college_and_high_school(c, *, player_id: str) -> dict:
    """COLLEGE + HIGH_SCHOOL -> PLAYER -- joins this batch's high-school
    data with the existing `nfl_players_draft.college` field for the same
    real player_id."""
    bg = player_background(c, player_id=player_id)
    college_row = c.execute(
        "SELECT DISTINCT college FROM nfl_players_draft WHERE pfr_id=(SELECT pfr_id FROM canonical_players WHERE player_id=?) "
        "AND college IS NOT NULL LIMIT 1", (player_id,),
    ).fetchone()
    return {"player_id": player_id, "college": college_row["college"] if college_row else None,
            "high_school_name": bg.get("high_school_name"), "high_school_city": bg.get("high_school_city"),
            "high_school_state": bg.get("high_school_state")}


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM nfl_player_background").fetchone()[0]
    with_birthplace = c.execute("SELECT COUNT(*) FROM nfl_player_background WHERE birthplace_city IS NOT NULL").fetchone()[0]
    with_hs = c.execute("SELECT COUNT(*) FROM nfl_player_background WHERE high_school_name IS NOT NULL").fetchone()[0]
    with_both = c.execute(
        "SELECT COUNT(*) FROM nfl_player_background WHERE birthplace_city IS NOT NULL AND high_school_name IS NOT NULL"
    ).fetchone()[0]
    return {
        "total_players_attempted": total, "birthplace_resolved": with_birthplace, "high_school_resolved": with_hs,
        "both_resolved": with_both,
        "sample_disclosure": "107 identity-resolved HOF players -- not the full NFL player population",
        "hometown_equals_birthplace_source_limitation": True,
    }
