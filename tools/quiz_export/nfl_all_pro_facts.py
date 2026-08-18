"""NFL AP All-Pro -- reusable knowledge relationships (Knowledge
Expansion Batch 2).

Built on `nfl_all_pro_selections` (tools/data_refresh/nfl_all_pro_import.py)
-- 4,965 real rows, 1932-2025 (real, disclosed gaps at 1954-1968).
Every function defaults to `ap_only=True`, meaning it only considers rows
where a real AP-specific selector tag was found (`is_ap=1`) -- the
canonical distinction the project standardizes on -- while still exposing
the full raw selector text on every row for callers that want the wider,
non-AP-exclusive picture.
"""
from __future__ import annotations


def player_all_pro_seasons(c, *, player_id: str, ap_only: bool = True) -> list[dict]:
    """PLAYER -> ALL_PRO (+ SEASON, ALL_PRO_TEAM/honor_level, POSITION)."""
    q = "SELECT season, position_raw, honor_level, selectors_raw, team_name_raw FROM nfl_all_pro_selections WHERE player_id=?"
    params = [player_id]
    if ap_only:
        q += " AND is_ap=1"
    q += " ORDER BY season"
    rows = c.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def player_all_pro_count(c, *, player_id: str, honor_level: str | None = None, ap_only: bool = True) -> int:
    """PLAYER -> ALL_PRO_COUNT."""
    q = "SELECT COUNT(*) FROM nfl_all_pro_selections WHERE player_id=?"
    params = [player_id]
    if ap_only:
        q += " AND is_ap=1"
    if honor_level:
        q += " AND honor_level=?"
        params.append(honor_level)
    return c.execute(q, params).fetchone()[0]


def season_all_pro_players(c, *, season: int, position_raw: str | None = None,
                            honor_level: str | None = None, ap_only: bool = True) -> list[dict]:
    """SEASON (+ POSITION, honor_level) -> ALL_PRO_PLAYERS."""
    q = "SELECT player_id, player_name_raw, position_raw, honor_level, team_name_raw, selectors_raw FROM nfl_all_pro_selections WHERE season=?"
    params = [season]
    if ap_only:
        q += " AND is_ap=1"
    if position_raw:
        q += " AND position_raw=?"
        params.append(position_raw)
    if honor_level:
        q += " AND honor_level=?"
        params.append(honor_level)
    rows = c.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def team_season_all_pro_players(c, *, team_code: str, season: int, ap_only: bool = True) -> list[dict]:
    """TEAM+SEASON -> ALL_PRO_PLAYERS -- requires the row's own real,
    resolved `team_code` (season >= 2002, per team_aliases coverage);
    older seasons are honestly unresolvable via team_code and return empty."""
    q = "SELECT player_id, player_name_raw, position_raw, honor_level FROM nfl_all_pro_selections WHERE team_code=? AND season=?"
    params = [team_code, season]
    if ap_only:
        q += " AND is_ap=1"
    rows = c.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM nfl_all_pro_selections").fetchone()[0]
    ap_rows = c.execute("SELECT COUNT(*) FROM nfl_all_pro_selections WHERE is_ap=1").fetchone()[0]
    resolved = c.execute("SELECT COUNT(*) FROM nfl_all_pro_selections WHERE is_ap=1 AND player_id IS NOT NULL").fetchone()[0]
    seasons = c.execute("SELECT MIN(season), MAX(season) FROM nfl_all_pro_selections").fetchone()
    first_team = c.execute("SELECT COUNT(*) FROM nfl_all_pro_selections WHERE is_ap=1 AND honor_level='FIRST_TEAM'").fetchone()[0]
    second_team = c.execute("SELECT COUNT(*) FROM nfl_all_pro_selections WHERE is_ap=1 AND honor_level='SECOND_TEAM'").fetchone()[0]
    return {
        "total_rows": total, "ap_confirmed_rows": ap_rows,
        "ap_identity_resolved": resolved,
        "ap_usable_percentage": round(100.0 * resolved / ap_rows, 1) if ap_rows else 0.0,
        "season_range": [seasons[0], seasons[1]],
        "first_team_ap_rows": first_team, "second_team_ap_rows": second_team,
    }
