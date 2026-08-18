"""CFB All-America -- reusable knowledge relationships (Knowledge
Expansion Batch 1).

Built entirely on `cfb_all_america_certified` (tools/data_refresh/
cfb_all_america_identity_resolution.py) -- the identity-resolved layer,
never the raw `cfb_all_america` table directly, so every relationship here
is always tied to a real `cfb_player_id`, never a bare name string.

--- HONOR-LEVEL DISTINCTIONS PRESERVED, NOT FLATTENED ---
The source data (`selectors_raw`, `is_consensus`) does not reliably encode
a structured first/second/third-team distinction -- confirmed by direct
inspection (selectors_raw is free text, e.g. "(College Football Hall of
Fame)", not a normalized team-level field). Rather than inventing a
first/second/third split the source doesn't actually support, this module
exposes exactly the two real distinctions the data DOES support --
`is_consensus` (boolean) and the raw `selectors_raw` text -- and nothing
more. This is the "retain raw provenance, normalize only where defensible"
instruction applied honestly.
"""
from __future__ import annotations

CERTIFIED_TABLE = "cfb_all_america_certified"


def player_honor(c, *, cfb_player_id: str, season: int | None = None) -> list[dict]:
    """PLAYER (+ SEASON) -> ALL_AMERICA_STATUS / TEAM / POSITION."""
    if season is not None:
        rows = c.execute(
            f"SELECT * FROM {CERTIFIED_TABLE} WHERE cfb_player_id=? AND season=?", (cfb_player_id, season),
        ).fetchall()
    else:
        rows = c.execute(f"SELECT * FROM {CERTIFIED_TABLE} WHERE cfb_player_id=? ORDER BY season", (cfb_player_id,)).fetchall()
    return [dict(r) for r in rows]


def school_all_americans(c, *, school_id: str, season: int | None = None) -> list[dict]:
    """SCHOOL (+ SEASON) -> ALL_AMERICANS."""
    if season is not None:
        rows = c.execute(
            f"SELECT * FROM {CERTIFIED_TABLE} WHERE school_id=? AND season=?", (school_id, season),
        ).fetchall()
    else:
        rows = c.execute(f"SELECT * FROM {CERTIFIED_TABLE} WHERE school_id=? ORDER BY season", (school_id,)).fetchall()
    return [dict(r) for r in rows]


def position_all_americans(c, *, position: str, season: int) -> list[dict]:
    """POSITION+SEASON -> ALL_AMERICANS."""
    rows = c.execute(
        f"SELECT * FROM {CERTIFIED_TABLE} WHERE position=? AND season=?", (position, season),
    ).fetchall()
    return [dict(r) for r in rows]


def all_america_to_nfl_bridge(c) -> dict:
    """ALL_AMERICAN -> NFL_IDENTITY, via the certified cross-league bridge
    -- direct cfb_player_id join."""
    total = c.execute(f"SELECT COUNT(*) FROM {CERTIFIED_TABLE}").fetchone()[0]
    joined = c.execute(
        f"SELECT COUNT(*) FROM {CERTIFIED_TABLE} a WHERE EXISTS "
        f"(SELECT 1 FROM cfb_nfl_identity_bridge_certified b WHERE b.cfb_player_id = a.cfb_player_id)"
    ).fetchone()[0]
    examples = c.execute(
        f"SELECT a.cfb_player_id, a.season, a.position, a.school_id, "
        f"b.nfl_player_key, b.nfl_draft_team, b.nfl_draft_year "
        f"FROM {CERTIFIED_TABLE} a JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = a.cfb_player_id "
        f"LIMIT 5"
    ).fetchall()
    return {"total_certified_honors": total, "joined_to_nfl_identity": joined,
            "join_percentage": round(100.0 * joined / total, 1) if total else 0.0,
            "examples": [dict(r) for r in examples]}


def eligibility_report(c) -> dict:
    raw_total = c.execute("SELECT COUNT(*) FROM cfb_all_america").fetchone()[0]
    certified_total = c.execute(f"SELECT COUNT(*) FROM {CERTIFIED_TABLE}").fetchone()[0]
    schools_covered = c.execute(f"SELECT COUNT(DISTINCT school_id) FROM {CERTIFIED_TABLE}").fetchone()[0]
    multi_aa_schools = c.execute(
        f"SELECT COUNT(*) FROM (SELECT school_id FROM {CERTIFIED_TABLE} GROUP BY school_id HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    modern_total = c.execute("SELECT COUNT(*) FROM cfb_all_america WHERE season >= 2002").fetchone()[0]
    modern_certified = c.execute(f"SELECT COUNT(*) FROM {CERTIFIED_TABLE} WHERE season >= 2002").fetchone()[0]
    return {
        "raw_rows": raw_total, "certified_rows": certified_total,
        "overall_usable_percentage": round(100.0 * certified_total / raw_total, 1) if raw_total else 0.0,
        "modern_era_2002_plus_rows": modern_total, "modern_era_certified": modern_certified,
        "modern_era_usable_percentage": round(100.0 * modern_certified / modern_total, 1) if modern_total else 0.0,
        "distinct_schools_with_certified_honors": schools_covered,
        "schools_with_multiple_certified_all_americans": multi_aa_schools,
    }
