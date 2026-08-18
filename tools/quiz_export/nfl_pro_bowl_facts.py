"""NFL Pro Bowl -- reusable knowledge relationships (Knowledge Expansion
Batch 2).

Built on `nfl_pro_bowl_selections` (tools/data_refresh/nfl_pro_bowl_import.py)
-- 4,217 real rows, 1972-2025 (real, disclosed per-year gaps). `tier` is
always one of the real, source-distinguished values (STARTER / RESERVE /
ALTERNATE / SELECTED-undifferentiated) -- never collapsed into a single
generic "was selected" boolean, since a Reserve and a Starter are
genuinely different honors.
"""
from __future__ import annotations


def player_pro_bowl_seasons(c, *, player_id: str) -> list[dict]:
    """PLAYER+SEASON -> PRO_BOWL."""
    rows = c.execute(
        "SELECT season, position_raw, tier, team_name_raw FROM nfl_pro_bowl_selections "
        "WHERE player_id=? ORDER BY season", (player_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def player_pro_bowl_count(c, *, player_id: str, tier: str | None = None) -> int:
    """PLAYER -> PRO_BOWL_COUNT."""
    q = "SELECT COUNT(*) FROM nfl_pro_bowl_selections WHERE player_id=?"
    params = [player_id]
    if tier:
        q += " AND tier=?"
        params.append(tier)
    return c.execute(q, params).fetchone()[0]


def season_pro_bowl_players(c, *, season: int, position_raw: str | None = None) -> list[dict]:
    """SEASON -> PRO_BOWL_PLAYERS."""
    q = "SELECT player_id, player_name_raw, position_raw, tier, team_name_raw FROM nfl_pro_bowl_selections WHERE season=?"
    params = [season]
    if position_raw:
        q += " AND position_raw=?"
        params.append(position_raw)
    rows = c.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def team_season_pro_bowl_players(c, *, team_code: str, season: int) -> list[dict]:
    """TEAM+SEASON -> PRO_BOWL_PLAYERS."""
    rows = c.execute(
        "SELECT player_id, player_name_raw, position_raw, tier FROM nfl_pro_bowl_selections "
        "WHERE team_code=? AND season=?", (team_code, season),
    ).fetchall()
    return [dict(r) for r in rows]


def position_season_pro_bowl_players(c, *, position_raw: str, season: int) -> list[dict]:
    """POSITION+SEASON -> PRO_BOWL_PLAYERS."""
    rows = c.execute(
        "SELECT player_id, player_name_raw, tier, team_name_raw FROM nfl_pro_bowl_selections "
        "WHERE position_raw=? AND season=?", (position_raw, season),
    ).fetchall()
    return [dict(r) for r in rows]


def compare_pro_bowl_counts(c, *, player_id_a: str, player_id_b: str) -> dict:
    """PLAYER vs PLAYER -> more Pro Bowl selections (real, direct count comparison)."""
    a = player_pro_bowl_count(c, player_id=player_id_a)
    b = player_pro_bowl_count(c, player_id=player_id_b)
    return {"player_id_a": player_id_a, "count_a": a, "player_id_b": player_id_b, "count_b": b,
            "more_selections": player_id_a if a > b else (player_id_b if b > a else "TIE")}


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM nfl_pro_bowl_selections").fetchone()[0]
    resolved = c.execute("SELECT COUNT(*) FROM nfl_pro_bowl_selections WHERE player_id IS NOT NULL").fetchone()[0]
    seasons = c.execute("SELECT MIN(season), MAX(season) FROM nfl_pro_bowl_selections").fetchone()
    tier_counts = {r["tier"]: r["n"] for r in c.execute(
        "SELECT tier, COUNT(*) n FROM nfl_pro_bowl_selections GROUP BY tier"
    ).fetchall()}
    return {
        "total_rows": total, "identity_resolved": resolved,
        "usable_percentage": round(100.0 * resolved / total, 1) if total else 0.0,
        "season_range": [seasons[0], seasons[1]], "tier_counts": tier_counts,
    }
