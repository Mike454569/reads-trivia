"""CFB coordinators -- reusable knowledge relationships (Knowledge
Expansion Batch 2).

Built on `cfb_coordinators` (tools/data_refresh/cfb_coordinators_import.py)
-- a real, disclosed 20-program sample for the 2025 season (21 rows, 5
programs actually resolved a real staff table). `normalized_role`
preserves the real co-coordinator distinction (`CO_OFFENSIVE_COORDINATOR`
is never merged into `OFFENSIVE_COORDINATOR`); `title_raw` keeps the exact
source text for callers that want the full, unnormalized title.
"""
from __future__ import annotations


def school_season_coordinators(c, *, school_id: str, season: int) -> list[dict]:
    """SCHOOL+SEASON -> OFFENSIVE_COORDINATOR / DEFENSIVE_COORDINATOR (+ co-coordinators)."""
    rows = c.execute(
        "SELECT normalized_role, title_raw, coach_id, coach_name_raw FROM cfb_coordinators "
        "WHERE school_id=? AND season=?", (school_id, season),
    ).fetchall()
    return [dict(r) for r in rows]


def coach_school_seasons(c, *, coach_id: str) -> list[dict]:
    """COACH -> SCHOOL+SEASON (+ROLE)."""
    rows = c.execute(
        "SELECT season, school_id, normalized_role, title_raw FROM cfb_coordinators WHERE coach_id=? ORDER BY season",
        (coach_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def head_coach_coordinators(c, *, school_id: str, season: int) -> dict:
    """HEAD_COACH+SEASON -> COORDINATORS -- joins the real existing
    `cfb_coach_school_links` head-coach table with this batch's new
    coordinator rows for the same school; never merges the two into one row."""
    hc = c.execute(
        "SELECT l.cfb_coach_id, cc.coach_name FROM cfb_coach_school_links l "
        "JOIN cfb_coaches cc ON cc.cfb_coach_id = l.cfb_coach_id WHERE l.school_id=?",
        (school_id,),
    ).fetchall()
    coords = c.execute(
        "SELECT normalized_role, coach_id, coach_name_raw FROM cfb_coordinators WHERE school_id=? AND season=?",
        (school_id, season),
    ).fetchall()
    return {
        "school_id": school_id, "season": season,
        "head_coach_candidates": [dict(r) for r in hc],
        "coordinators": [dict(r) for r in coords],
    }


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_coordinators").fetchone()[0]
    schools_covered = c.execute("SELECT COUNT(DISTINCT school_id) FROM cfb_coordinators").fetchone()[0]
    role_counts = {r["normalized_role"]: r["n"] for r in c.execute(
        "SELECT normalized_role, COUNT(*) n FROM cfb_coordinators GROUP BY normalized_role"
    ).fetchall()}
    return {
        "total_rows": total, "schools_covered": schools_covered, "role_counts": role_counts,
        "sample_disclosure": "20 hand-picked major programs, 2025 season only -- not FBS-wide, not multi-year",
    }
