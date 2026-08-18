"""CFB kicking (field goals + extra points) at player-game granularity --
reusable knowledge relationships (Knowledge Expansion Batch 4).

Built on `cfb_player_game_kicking_ext` (tools/data_refresh/
cfb_kicking_espn_refresh.py) -- a real, disclosed sample from ESPN's
public boxscore API, identity-joined via the same `ESPN_CFB:<id>` space
`canonical_cfb_players` already uses. Extends, never replaces, Batch 3's
`cfb_player_game_stats_real` (which has no XP field at all).
"""
from __future__ import annotations


def player_game_kicking(c, *, cfb_player_id: str, game_id: str) -> dict:
    """KICKER + GAME -> FG_MADE/ATTEMPTED, EXTRA_POINTS made/attempted."""
    row = c.execute(
        "SELECT * FROM cfb_player_game_kicking_ext WHERE cfb_player_id=? AND game_id=?",
        (cfb_player_id, game_id),
    ).fetchone()
    if row is None:
        return {"cfb_player_id": cfb_player_id, "game_id": game_id, "found": False}
    return {"found": True, **dict(row)}


def kicker_perfect_xp_game(c, *, cfb_player_id: str, game_id: str) -> bool | None:
    """KICKER + GAME -> made every real extra point attempted. None (not
    False) when there's no real data for this player+game -- never
    silently treated as a perfect (or imperfect) game with no evidence."""
    line = player_game_kicking(c, cfb_player_id=cfb_player_id, game_id=game_id)
    if not line["found"] or line["xp_attempted"] is None:
        return None
    if line["xp_attempted"] == 0:
        return None  # real, honest: no XP attempts means the question doesn't apply, not a trivial "yes"
    return line["xp_made"] == line["xp_attempted"]


def game_kickers(c, *, game_id: str) -> list[dict]:
    """GAME -> all real kickers with a recorded line."""
    rows = c.execute(
        "SELECT cfb_player_id, player_name_raw, fg_made, fg_attempted, xp_made, xp_attempted "
        "FROM cfb_player_game_kicking_ext WHERE game_id=?", (game_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def cross_validate_field_goals(c, *, game_id: str) -> list[dict]:
    """Cross-checks this batch's ESPN-sourced fg_made against Batch 3's
    independently-sourced (SPORTSDATAVERSE_CFB) field_goals_made for the
    same real player+game -- two different sources, same real fact."""
    espn_rows = c.execute(
        "SELECT cfb_player_id, fg_made, fg_attempted FROM cfb_player_game_kicking_ext WHERE game_id=?", (game_id,),
    ).fetchall()
    out = []
    for r in espn_rows:
        batch3 = c.execute(
            "SELECT field_goals_made, field_goals_attempted FROM cfb_player_game_stats_real "
            "WHERE cfb_player_id=? AND game_id=?", (r["cfb_player_id"], game_id),
        ).fetchone()
        out.append({
            "cfb_player_id": r["cfb_player_id"],
            "espn_fg_made": r["fg_made"], "espn_fg_attempted": r["fg_attempted"],
            "batch3_fg_made": batch3["field_goals_made"] if batch3 else None,
            "batch3_fg_attempted": batch3["field_goals_attempted"] if batch3 else None,
            "agrees": (batch3 is not None and batch3["field_goals_made"] == r["fg_made"]),
        })
    return out


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_player_game_kicking_ext").fetchone()[0]
    games = c.execute("SELECT COUNT(DISTINCT game_id) FROM cfb_player_game_kicking_ext").fetchone()[0]
    seasons = c.execute(
        "SELECT MIN(season), MAX(season) FROM cfb_player_game_stats_real s "
        "WHERE s.game_id IN (SELECT DISTINCT game_id FROM cfb_player_game_kicking_ext)"
    ).fetchone()
    with_xp = c.execute("SELECT COUNT(*) FROM cfb_player_game_kicking_ext WHERE xp_attempted IS NOT NULL").fetchone()[0]
    with_fg = c.execute("SELECT COUNT(*) FROM cfb_player_game_kicking_ext WHERE fg_attempted IS NOT NULL").fetchone()[0]
    return {
        "total_rows": total, "distinct_games": games, "season_range": [seasons[0], seasons[1]],
        "rows_with_xp_data": with_xp, "rows_with_fg_data": with_fg,
        "sample_disclosure": "real ESPN-sourced sample across 2022-2025, not exhaustive across all CFB games",
    }
