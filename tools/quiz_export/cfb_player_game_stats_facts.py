"""CFB player-GAME stats -- reusable knowledge relationships (Knowledge
Expansion Batch 3).

Built on `cfb_player_game_stats_real` (tools/data_refresh/
cfb_player_game_stats_refresh.py) -- the same real, SPORTSDATAVERSE_CFB
per-play source as the existing `cfb_player_season_stats_real`, re-
aggregated at game granularity instead of collapsed to a season total.
`tackles`/`tackles_for_loss`/`extra_points_made` are real schema columns
that are always NULL this batch -- the source has no such fields (see the
refresh module's docstring) -- never fabricated as zero.
"""
from __future__ import annotations


def player_game_stat_line(c, *, cfb_player_id: str, game_id: str) -> dict:
    """PLAYER + GAME -> STAT_LINE."""
    row = c.execute("SELECT * FROM cfb_player_game_stats_real WHERE cfb_player_id=? AND game_id=?",
                     (cfb_player_id, game_id)).fetchone()
    if row is None:
        return {"cfb_player_id": cfb_player_id, "game_id": game_id, "found": False}
    return {"found": True, **dict(row)}


def player_weekly_stat_line(c, *, cfb_player_id: str, season: int, week: int) -> dict:
    """PLAYER + SEASON + WEEK -> STAT_LINE (+ TEAM)."""
    row = c.execute(
        "SELECT * FROM cfb_player_game_stats_real WHERE cfb_player_id=? AND season=? AND week=?",
        (cfb_player_id, season, week),
    ).fetchone()
    if row is None:
        return {"cfb_player_id": cfb_player_id, "season": season, "week": week, "found": False}
    return {"found": True, **dict(row)}


def game_players(c, *, game_id: str) -> list[dict]:
    """GAME -> PLAYERS (every player with a real recorded stat line in this game)."""
    rows = c.execute(
        "SELECT cfb_player_id, player_name, school_id, pass_attempts, completions, passing_yards, passing_tds, "
        "rush_attempts, rushing_yards, rushing_tds, receptions, receiving_yards, receiving_tds, "
        "defensive_interceptions, sacks, field_goals_made FROM cfb_player_game_stats_real WHERE game_id=?",
        (game_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def team_game_participants(c, *, school_id: str, game_id: str) -> list[dict]:
    """TEAM + GAME -> PARTICIPATING_PLAYERS."""
    rows = c.execute(
        "SELECT cfb_player_id, player_name FROM cfb_player_game_stats_real WHERE school_id=? AND game_id=?",
        (school_id, game_id),
    ).fetchall()
    return [dict(r) for r in rows]


def team_week_top_performer(c, *, school_id: str, game_id: str, category: str) -> dict:
    """TEAM + GAME -> top performer in a real stat category."""
    if category not in ("passing_yards", "rushing_yards", "receiving_yards", "sacks", "defensive_interceptions"):
        raise ValueError("unsupported category")
    row = c.execute(
        f"SELECT cfb_player_id, player_name, {category} AS value FROM cfb_player_game_stats_real "
        f"WHERE school_id=? AND game_id=? AND {category} IS NOT NULL ORDER BY {category} DESC LIMIT 1",
        (school_id, game_id),
    ).fetchone()
    if row is None:
        return {"school_id": school_id, "game_id": game_id, "category": category, "found": False}
    return {"found": True, "category": category, **dict(row)}


def compare_players_in_game(c, *, cfb_player_id_a: str, cfb_player_id_b: str, game_id: str, category: str) -> dict:
    """PLAYER vs PLAYER in one game -- e.g. 'who rushed for more yards.'"""
    a = player_game_stat_line(c, cfb_player_id=cfb_player_id_a, game_id=game_id)
    b = player_game_stat_line(c, cfb_player_id=cfb_player_id_b, game_id=game_id)
    va = a.get(category) if a["found"] else None
    vb = b.get(category) if b["found"] else None
    if va is None or vb is None:
        return {"category": category, "found": False, "reason": "one or both players have no real stat line for this game"}
    winner = cfb_player_id_a if va > vb else (cfb_player_id_b if vb > va else "TIE")
    return {"category": category, "found": True, "value_a": va, "value_b": vb, "higher": winner}


def played_in_game(c, *, cfb_player_id: str, game_id: str) -> bool:
    """PLAYER -> PLAYED_IN_GAME (confirmed real participation, not roster inference)."""
    row = c.execute(
        "SELECT 1 FROM cfb_player_game_stats_real WHERE cfb_player_id=? AND game_id=?", (cfb_player_id, game_id),
    ).fetchone()
    return row is not None


def team_confirmed_participants_for_week(c, *, school_id: str, season: int, week: int) -> list[dict]:
    """TEAM + SEASON + WEEK -> confirmed real participants (used by the
    fantasy-draft eligibility upgrade -- see live_weekly_fantasy_draft.py)."""
    rows = c.execute(
        "SELECT DISTINCT cfb_player_id, player_name FROM cfb_player_game_stats_real "
        "WHERE school_id=? AND season=? AND week=?", (school_id, season, week),
    ).fetchall()
    return [dict(r) for r in rows]


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_player_game_stats_real").fetchone()[0]
    games = c.execute("SELECT COUNT(DISTINCT game_id) FROM cfb_player_game_stats_real").fetchone()[0]
    seasons = c.execute("SELECT MIN(season), MAX(season) FROM cfb_player_game_stats_real").fetchone()
    weeks = c.execute("SELECT COUNT(DISTINCT season || '-' || week) FROM cfb_player_game_stats_real WHERE week IS NOT NULL").fetchone()[0]
    with_passing = c.execute("SELECT COUNT(*) FROM cfb_player_game_stats_real WHERE pass_attempts > 0").fetchone()[0]
    with_rushing = c.execute("SELECT COUNT(*) FROM cfb_player_game_stats_real WHERE rush_attempts > 0").fetchone()[0]
    with_receiving = c.execute("SELECT COUNT(*) FROM cfb_player_game_stats_real WHERE receptions > 0").fetchone()[0]
    with_defense = c.execute(
        "SELECT COUNT(*) FROM cfb_player_game_stats_real WHERE defensive_interceptions > 0 OR sacks > 0 OR forced_fumbles > 0"
    ).fetchone()[0]
    with_kicking = c.execute("SELECT COUNT(*) FROM cfb_player_game_stats_real WHERE field_goals_attempted > 0").fetchone()[0]
    return {
        "total_rows": total, "distinct_games": games, "season_range": [seasons[0], seasons[1]],
        "distinct_season_week_pairs": weeks,
        "rows_with_passing": with_passing, "rows_with_rushing": with_rushing,
        "rows_with_receiving": with_receiving, "rows_with_defense": with_defense, "rows_with_kicking": with_kicking,
        "tackles_available": False, "tackles_for_loss_available": False, "extra_points_made_available": False,
    }
