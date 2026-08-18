"""NFL coordinators -- reusable knowledge relationships (Knowledge
Expansion Batch 2).

Built on `nfl_coordinators` (tools/data_refresh/nfl_coordinators_import.py)
-- a real, CURRENT-SEASON-ONLY snapshot (64 rows: 32 offensive + 32
defensive coordinators). No special-teams coordinator source was found
(disclosed in the import module); callers asking for that role honestly
get an empty list, never a guess.
"""
from __future__ import annotations


def team_season_coordinator(c, *, team_code: str, season: int, role: str) -> dict:
    """TEAM+SEASON -> OFFENSIVE_COORDINATOR / DEFENSIVE_COORDINATOR."""
    row = c.execute(
        "SELECT coach_id, coach_name_raw, since_year, previous_position_raw FROM nfl_coordinators "
        "WHERE team_code=? AND season=? AND role=?", (team_code, season, role),
    ).fetchone()
    if row is None:
        return {"team_code": team_code, "season": season, "role": role, "found": False}
    return {"team_code": team_code, "season": season, "role": role, "found": True, **dict(row)}


def coach_team_seasons(c, *, coach_id: str) -> list[dict]:
    """COACH -> TEAM+SEASON (+ROLE) -- every real coordinator assignment on record."""
    rows = c.execute(
        "SELECT season, team_code, team_name_raw, role FROM nfl_coordinators WHERE coach_id=? ORDER BY season",
        (coach_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def head_coach_coordinators(c, *, team_code: str, season: int) -> dict:
    """HEAD_COACH+SEASON -> COORDINATORS -- joins the real existing
    `coach_team_seasons` head-coach table with this batch's new
    coordinator rows for the same team+season; head coach and
    coordinators are reported separately, never merged into one row."""
    hc = c.execute(
        "SELECT coach_id, coach_name FROM coach_team_seasons WHERE team_code=? AND season=?",
        (team_code, season),
    ).fetchone()
    coords = c.execute(
        "SELECT role, coach_id, coach_name_raw FROM nfl_coordinators WHERE team_code=? AND season=?",
        (team_code, season),
    ).fetchall()
    return {
        "team_code": team_code, "season": season,
        "head_coach": dict(hc) if hc else None,
        "coordinators": [dict(r) for r in coords],
    }


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM nfl_coordinators").fetchone()[0]
    seasons = c.execute("SELECT DISTINCT season FROM nfl_coordinators").fetchall()
    role_counts = {r["role"]: r["n"] for r in c.execute(
        "SELECT role, COUNT(*) n FROM nfl_coordinators GROUP BY role"
    ).fetchall()}
    teams_covered = c.execute("SELECT COUNT(DISTINCT team_code) FROM nfl_coordinators WHERE team_code IS NOT NULL").fetchone()[0]
    return {
        "total_rows": total, "seasons_covered": [s["season"] for s in seasons],
        "role_counts": role_counts, "teams_covered": teams_covered,
        "special_teams_coordinator_source_found": False,
    }
