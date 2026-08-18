"""CFB rankings/polls -- reusable knowledge relationships (Knowledge
Expansion Batch 1).

`cfb_rankings` (31,801 rows, real, already school_id-resolved) is directly,
reliably queryable as-is -- no identity-resolution ETL needed, unlike
All-America/transfers. This module is the one place that answers
TEAM+SEASON+WEEK+POLL -> RANK (and the reverse) so every future Creator
concept asks the same real question the same way, rather than each
adapter writing its own ad hoc SQL.

--- POLL IDENTITY IS NEVER MERGED (real, disclosed design decision) ---
7 real, distinct polls exist in this table: 'AP Top 25' (9,680 rows),
'Coaches Poll' (9,731), 'Playoff Committee Rankings' (1,825), 'BCS
Standings' (1,350) -- the four genuinely FBS-top-tier polls across
different eras -- plus 'FCS Coaches Poll', 'AFCA Division II Coaches
Poll', 'AFCA Division III Coaches Poll' (real, but a different
competitive tier, never conflated with FBS Top 25 context). Every
function below takes `poll` as a required-or-defaulted parameter and
never averages/merges ranks across polls. DEFAULT_POLL below is a
disclosed convenience default (the most historically continuous FBS
poll), never a silent "pick whichever poll has a row."

--- NEVER INFER A RANK ---
A team with no real row for a given (school, season, week, season_type,
poll) is UNRANKED for that exact query -- returned as `None`, never
guessed, never carried over from an adjacent week.

--- SEASON_TYPE IS A REAL, REQUIRED DIMENSION (bug found and fixed) ---
A naive (season, week, poll, school_id) grouping flags 1,141 false
"conflicts" -- e.g. CFB_SCHOOL_COLORADO shows rank=14 for (2002, week=1,
'postseason') and rank=7 for (2002, week=1, 'regular'), because week
numbering resets between season_type values; these are two genuinely
different real polls, not a data conflict. Including `season_type`
(confirmed real values: 'regular', 'postseason') drops the false-conflict
count to 202 real, disclosed ones. Every function below requires/defaults
`season_type='regular'` and treats it as part of the real key, never
merged with postseason.
"""
from __future__ import annotations

DEFAULT_POLL = "AP Top 25"
DEFAULT_SEASON_TYPE = "regular"
FBS_TOP_TIER_POLLS = frozenset({"AP Top 25", "Coaches Poll", "Playoff Committee Rankings", "BCS Standings"})


def real_polls(c) -> list[str]:
    return [r[0] for r in c.execute("SELECT DISTINCT poll FROM cfb_rankings ORDER BY poll")]


def _dedupe_check(c, season: int, week: int, season_type: str, poll: str, school_id: str) -> list[int]:
    """Real duplicate-row detection -- returns every distinct rank value
    found for this exact (school, season, week, season_type, poll). An
    honest single-element list means no conflict; anything longer is a
    real, disclosed data-conflict the caller must see, never silently
    resolved by picking the first row."""
    rows = c.execute(
        "SELECT DISTINCT rank FROM cfb_rankings WHERE season=? AND week=? AND season_type=? AND poll=? AND school_id=?",
        (season, week, season_type, poll, school_id),
    ).fetchall()
    return sorted(r[0] for r in rows)


def rank_for(c, *, school_id: str, season: int, week: int, season_type: str = DEFAULT_SEASON_TYPE,
             poll: str = DEFAULT_POLL) -> dict:
    """TEAM+SEASON+WEEK+POLL -> RANK. Returns a dict, never a bare int, so
    the caller always sees whether this is a real single rank, a genuine
    conflict, or an honest UNRANKED -- never conflated."""
    ranks = _dedupe_check(c, season, week, season_type, poll, school_id)
    if not ranks:
        return {"school_id": school_id, "season": season, "week": week, "season_type": season_type, "poll": poll,
                "rank": None, "ranked": False, "conflict": False}
    if len(ranks) > 1:
        return {"school_id": school_id, "season": season, "week": week, "season_type": season_type, "poll": poll,
                "rank": None, "ranked": True, "conflict": True, "conflicting_ranks": ranks}
    return {"school_id": school_id, "season": season, "week": week, "season_type": season_type, "poll": poll,
            "rank": ranks[0], "ranked": True, "conflict": False}


def team_for_rank(c, *, rank: int, season: int, week: int, season_type: str = DEFAULT_SEASON_TYPE,
                   poll: str = DEFAULT_POLL) -> dict:
    """RANK+SEASON+WEEK+POLL -> TEAM."""
    rows = c.execute(
        "SELECT DISTINCT school_id, school_name_raw FROM cfb_rankings "
        "WHERE season=? AND week=? AND season_type=? AND poll=? AND rank=?",
        (season, week, season_type, poll, rank),
    ).fetchall()
    if not rows:
        return {"rank": rank, "season": season, "week": week, "season_type": season_type, "poll": poll,
                "school_id": None, "conflict": False}
    if len(rows) > 1:
        return {"rank": rank, "season": season, "week": week, "season_type": season_type, "poll": poll,
                "school_id": None, "conflict": True, "conflicting_schools": [r["school_id"] for r in rows]}
    return {"rank": rank, "season": season, "week": week, "season_type": season_type, "poll": poll,
            "school_id": rows[0]["school_id"], "school_name": rows[0]["school_name_raw"], "conflict": False}


def team_rank_history(c, *, school_id: str, season: int, season_type: str = DEFAULT_SEASON_TYPE,
                       poll: str = DEFAULT_POLL) -> list[dict]:
    """A team's real rank across every real week it has a row for that
    (season, season_type, poll) -- weeks with no row are simply absent,
    never filled in as an inferred 'still ranked here' guess."""
    rows = c.execute(
        "SELECT DISTINCT week, rank FROM cfb_rankings WHERE season=? AND season_type=? AND poll=? AND school_id=? ORDER BY week",
        (season, season_type, poll, school_id),
    ).fetchall()
    return [{"week": r["week"], "rank": r["rank"]} for r in rows]


def game_ranking_context(c, *, game_id: str, poll: str = DEFAULT_POLL) -> dict:
    """GAME -> HOME_TEAM_RANK / AWAY_TEAM_RANK / RANKED_MATCHUP /
    RANKED_VS_UNRANKED / UPSET_CONTEXT. Uses the game's own real season/week
    to look up each team's real rank for that exact week -- never a
    different week's rank. UPSET_CONTEXT is only ever set when BOTH a real
    rank difference AND a real final score are available; otherwise it is
    honestly None, never guessed."""
    game = c.execute(
        "SELECT season, week, season_type, home_school_id, away_school_id, home_score, away_score "
        "FROM cfb_games_canonical WHERE game_id=?", (game_id,),
    ).fetchone()
    if game is None:
        return {"game_id": game_id, "poll": poll, "found": False}

    # Uses the GAME's own real season_type -- a postseason game must be
    # checked against postseason-week rankings, never regular-season ones
    # that happen to share the same week number (see module docstring).
    season_type = game["season_type"] or DEFAULT_SEASON_TYPE
    home = rank_for(c, school_id=game["home_school_id"], season=game["season"], week=game["week"],
                     season_type=season_type, poll=poll)
    away = rank_for(c, school_id=game["away_school_id"], season=game["season"], week=game["week"],
                     season_type=season_type, poll=poll)

    if home["ranked"] and away["ranked"]:
        matchup = "RANKED_VS_RANKED"
    elif home["ranked"] or away["ranked"]:
        matchup = "RANKED_VS_UNRANKED"
    else:
        matchup = "UNRANKED_VS_UNRANKED"

    upset = None
    if (home["ranked"] and not home["conflict"] and away["ranked"] and not away["conflict"]
            and game["home_score"] is not None and game["away_score"] is not None
            and game["home_score"] != game["away_score"]):
        home_won = game["home_score"] > game["away_score"]
        lower_rank_team_won = (home_won and home["rank"] < away["rank"]) or (not home_won and away["rank"] < home["rank"])
        upset = not lower_rank_team_won  # the worse (higher-numbered/unranked) rank team won
    elif ((home["ranked"] and not away["ranked"]) or (away["ranked"] and not home["ranked"]))\
            and game["home_score"] is not None and game["away_score"] is not None and game["home_score"] != game["away_score"]:
        home_won = game["home_score"] > game["away_score"]
        ranked_team_won = (home_won and home["ranked"]) or (not home_won and away["ranked"])
        upset = not ranked_team_won

    return {
        "game_id": game_id, "poll": poll, "found": True,
        "season": game["season"], "week": game["week"],
        "home_team_rank": home, "away_team_rank": away,
        "matchup_category": matchup, "upset": upset,
    }


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_rankings").fetchone()[0]
    polls = real_polls(c)
    seasons = c.execute("SELECT MIN(season), MAX(season) FROM cfb_rankings").fetchone()
    dup_check = c.execute(
        "SELECT COUNT(*) FROM (SELECT season, week, season_type, poll, school_id FROM cfb_rankings "
        "GROUP BY season, week, season_type, poll, school_id HAVING COUNT(DISTINCT rank) > 1)"
    ).fetchone()[0]
    fbs_rows = c.execute(
        f"SELECT COUNT(*) FROM cfb_rankings WHERE poll IN ({','.join('?' * len(FBS_TOP_TIER_POLLS))})",
        tuple(FBS_TOP_TIER_POLLS),
    ).fetchone()[0]
    weeks_covered = c.execute("SELECT COUNT(DISTINCT season || '-' || week) FROM cfb_rankings").fetchone()[0]
    teams_covered = c.execute("SELECT COUNT(DISTINCT school_id) FROM cfb_rankings").fetchone()[0]
    return {
        "total_rows": total, "distinct_polls": polls, "fbs_top_tier_rows": fbs_rows,
        "season_range": [seasons[0], seasons[1]], "distinct_season_week_pairs": weeks_covered,
        "distinct_teams_ever_ranked": teams_covered,
        "duplicate_conflicting_school_week_poll_groups": dup_check,
    }
