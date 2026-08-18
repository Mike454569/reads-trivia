"""CFB betting lines -- reusable knowledge relationships (Knowledge
Expansion Batch 1).

`cfb_betting_lines` (37,015 rows) joins 100% cleanly to `cfb_games_canonical`
by `game_id` (verified directly this batch -- every single betting-line row
has a matching real game row). Cover/over-under RESULTS are never stored --
they are computed here, on demand, directly from the game's real final
score, so they can never silently go stale or disagree with the real
scoreboard. A result is only ever computed when BOTH a real line AND a real
final score exist; a missing line or an unplayed game yields an honest
`None`, never a guessed outcome. Provider identity is always preserved
(never averaged across sportsbooks) -- `provider` is a required grouping
key everywhere a specific line matters.

Sign convention (matches the raw data as stored): `spread` is relative to
the HOME team -- negative means the home team is favored by that many
points (e.g. spread=-3.5 means home favored by 3.5), matching the real
sample row inspected this batch (Pittsburgh home spread=-3.5, Pittsburgh
won by 2 -- favorite won, did not cover).
"""
from __future__ import annotations


def real_providers(c) -> list[str]:
    return [r[0] for r in c.execute("SELECT DISTINCT provider FROM cfb_betting_lines ORDER BY provider")]


def game_line(c, *, game_id: str, provider: str | None = None) -> list[dict]:
    """GAME -> SPREAD / TOTAL / PROVIDER (one entry per real provider row
    for this game, never merged into a single "the" line unless the
    caller explicitly names one provider)."""
    if provider:
        rows = c.execute(
            "SELECT provider, spread, spread_open, over_under, over_under_open, home_moneyline, away_moneyline "
            "FROM cfb_betting_lines WHERE game_id=? AND provider=?", (game_id, provider),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT provider, spread, spread_open, over_under, over_under_open, home_moneyline, away_moneyline "
            "FROM cfb_betting_lines WHERE game_id=?", (game_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def spread_result(c, *, game_id: str, provider: str) -> dict:
    """GAME RESULT + LINE -> FAVORITE / UNDERDOG / FAVORITE_WON /
    COVER_RESULT. Only ever computed when both a real spread and a real
    final score exist -- otherwise every result field is honestly None."""
    game = c.execute(
        "SELECT home_school_id, away_school_id, home_score, away_score FROM cfb_games_canonical WHERE game_id=?",
        (game_id,),
    ).fetchone()
    line = c.execute(
        "SELECT spread FROM cfb_betting_lines WHERE game_id=? AND provider=?", (game_id, provider),
    ).fetchone()

    result = {"game_id": game_id, "provider": provider, "has_line": line is not None and line["spread"] is not None,
               "has_final_score": game is not None and game["home_score"] is not None and game["away_score"] is not None,
               "spread": None, "favorite": None, "underdog": None, "favorite_won": None, "cover_result": None}
    if game is None or line is None or line["spread"] is None:
        return result
    result["spread"] = line["spread"]
    result["favorite"] = game["home_school_id"] if line["spread"] < 0 else game["away_school_id"]
    result["underdog"] = game["away_school_id"] if line["spread"] < 0 else game["home_school_id"]
    if game["home_score"] is None or game["away_score"] is None:
        return result  # game not final -- no result to derive, honestly incomplete

    home_margin = game["home_score"] - game["away_score"]
    result["favorite_won"] = (home_margin > 0) if line["spread"] < 0 else (home_margin < 0)
    # ATS margin, relative to the favorite: how many points the favorite
    # won by, minus the points it was expected to win by.
    ats_margin_for_home = home_margin + line["spread"]
    if ats_margin_for_home == 0:
        result["cover_result"] = "PUSH"
    elif line["spread"] < 0:  # home favored
        result["cover_result"] = "FAVORITE_COVERED" if ats_margin_for_home > 0 else "UNDERDOG_COVERED"
    else:  # away favored
        result["cover_result"] = "FAVORITE_COVERED" if ats_margin_for_home < 0 else "UNDERDOG_COVERED"
    return result


def total_result(c, *, game_id: str, provider: str) -> dict:
    """GAME RESULT + TOTAL -> OVER_UNDER_RESULT."""
    game = c.execute(
        "SELECT home_score, away_score FROM cfb_games_canonical WHERE game_id=?", (game_id,),
    ).fetchone()
    line = c.execute(
        "SELECT over_under FROM cfb_betting_lines WHERE game_id=? AND provider=?", (game_id, provider),
    ).fetchone()

    result = {"game_id": game_id, "provider": provider, "total_line": None, "actual_total": None,
               "over_under_result": None}
    if line is None or line["over_under"] is None:
        return result
    result["total_line"] = line["over_under"]
    if game is None or game["home_score"] is None or game["away_score"] is None:
        return result
    actual = game["home_score"] + game["away_score"]
    result["actual_total"] = actual
    if actual == line["over_under"]:
        result["over_under_result"] = "PUSH"
    else:
        result["over_under_result"] = "OVER" if actual > line["over_under"] else "UNDER"
    return result


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_betting_lines").fetchone()[0]
    matched_games = c.execute(
        "SELECT COUNT(*) FROM cfb_betting_lines b WHERE EXISTS "
        "(SELECT 1 FROM cfb_games_canonical g WHERE g.game_id = b.game_id)"
    ).fetchone()[0]
    with_spread = c.execute("SELECT COUNT(*) FROM cfb_betting_lines WHERE spread IS NOT NULL").fetchone()[0]
    with_total = c.execute("SELECT COUNT(*) FROM cfb_betting_lines WHERE over_under IS NOT NULL").fetchone()[0]
    providers = real_providers(c)
    multi_provider_games = c.execute(
        "SELECT COUNT(*) FROM (SELECT game_id FROM cfb_betting_lines GROUP BY game_id HAVING COUNT(DISTINCT provider) > 1)"
    ).fetchone()[0]
    final_score_games = c.execute(
        "SELECT COUNT(*) FROM cfb_betting_lines b JOIN cfb_games_canonical g ON g.game_id = b.game_id "
        "WHERE g.home_score IS NOT NULL AND g.away_score IS NOT NULL"
    ).fetchone()[0]
    return {
        "total_rows": total, "matched_to_real_game": matched_games,
        "unresolved_games": total - matched_games,
        "rows_with_spread": with_spread, "rows_with_total": with_total,
        "distinct_providers": providers, "games_with_multiple_providers": multi_provider_games,
        "rows_with_a_final_score_available": final_score_games,
    }
