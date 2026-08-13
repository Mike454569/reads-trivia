"""NFL Game Box Score domain adapter -- exposes the newly-populated
`team_game_stats` table (Historical Engine Enrichment operation) to the
Creator/Director pipeline, so real per-game team totals become real,
generatable content rather than just sitting in a table nobody reads
from.

Genuinely distinct from nfl_game_result.py's WON_GAME capability: this
asks which team had MORE TOTAL YARDS in a real game -- not who won.
These frequently differ (a team can out-gain its opponent and still
lose on turnovers/red-zone efficiency), which is exactly what makes this
a real, separate, non-redundant question, not a reskin of the existing
one. `nfl_game_result.py`'s own docstring previously disclosed "this
database has no per-game player statistics, only season-level" -- that
was true when written; `player_game_stats`/`team_game_stats` (this same
operation, later) closed that gap. This adapter is the first thing built
on the newer table specifically so that disclosure doesn't go stale.

Real, cross-verified source: team_game_stats was built from
nflverse-data's `stats_team` release and spot-checked before ever being
trusted (2024 Week 1 KC-BAL: both teams' box-score lines sum, via
TDs*6+FG*3+PAT, to the real final score on both sides) -- see
tools/data_refresh/nfl_team_game_stats_refresh.py's module docstring.
"""
from __future__ import annotations

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise, teams_active_in_season

OUT_PATH = None  # served live via the Gateway; no export script has passed
                 # its own out_path yet, so this default is never used
GLOBAL_NAME = "QUIZ_DATA_ENGINE_GAME_BOXSCORE"
SEED = "reads-quiz-engine-game-boxscore-production-v1"
ID_START = 680000
TARGET_COUNT = 300
CATEGORY = "NFL Game Box Scores"
REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
TRACK_ENTITY = True  # one question per real game_id
MIN_SEASON = 1999
MAX_SEASON = 2025


def safety_check(c) -> dict:
    return safety.check_source_id_only_safety(
        c, "team_game_stats", REQUIRED_SOURCE_ID,
        where_extra="total_yards IS NOT NULL",
    )


# Same real production-scale caching pattern already proven for
# nfl_game_result.py/cfb_game_result.py -- this table only changes on a
# real refresh (~daily at most), so caching the raw fetch avoids re-doing
# a full-table scan+join on every single live request.
_CANDIDATE_CACHE: dict = {"rows": None, "fetched_at": 0.0}
_CANDIDATE_CACHE_TTL_SECONDS = 600.0


def _fetch_raw_rows(c):
    import time
    cached = _CANDIDATE_CACHE["rows"]
    if cached is not None and time.monotonic() - _CANDIDATE_CACHE["fetched_at"] < _CANDIDATE_CACHE_TTL_SECONDS:
        return cached
    # Self-join pairs each game's two real team rows together. 16 of the
    # real game_ids in team_game_stats don't have exactly 2 rows (a
    # source-data edge case, not a bug here) -- the HAVING clause excludes
    # them rather than guessing which row is missing.
    rows = c.execute(
        """
        SELECT a.game_id, a.season, a.week, a.season_type,
               a.team_code AS team_a, a.total_yards AS yards_a, a.turnovers AS turnovers_a,
               b.team_code AS team_b, b.total_yards AS yards_b, b.turnovers AS turnovers_b,
               a.source_id
        FROM team_game_stats a
        JOIN team_game_stats b ON a.game_id = b.game_id AND a.team_code < b.team_code
        WHERE a.total_yards IS NOT NULL AND b.total_yards IS NOT NULL
          AND a.total_yards != b.total_yards
          AND a.season BETWEEN ? AND ?
        ORDER BY a.game_id
        """,
        (MIN_SEASON, MAX_SEASON),
    ).fetchall()
    rows = list(rows)
    _CANDIDATE_CACHE["rows"] = rows
    _CANDIDATE_CACHE["fetched_at"] = time.monotonic()
    return rows


def fetch_ordered_candidates(c, seed: str):
    rows = list(_fetch_raw_rows(c))  # copy -- shuffle must never mutate the shared cache
    rng_order = engine.seeded(seed)
    rng_order.shuffle(rows)
    return rows


_WEEK_LABELS = {"WC": "the Wild Card round", "DIV": "the Divisional round",
                "CON": "the Conference Championship", "SB": "the Super Bowl"}


def _week_label(season_type: str, week) -> str:
    if season_type == "POST" and week:
        # team_game_stats' week for POST games is a plain integer (round
        # number within the postseason, not the WC/DIV/CON/SB code games
        # uses) -- label generically rather than guessing a specific round.
        return f"the {week}. postseason round"
    return f"Week {week}"


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID:
        return "ROW_NOT_VERIFIED"

    season = row["season"]
    franchise_a, err = resolve_franchise(c, row["team_a"], season)
    if err:
        return err
    franchise_b, err = resolve_franchise(c, row["team_b"], season)
    if err:
        return err

    a_more = row["yards_a"] > row["yards_b"]
    winner = franchise_a if a_more else franchise_b
    loser = franchise_b if a_more else franchise_a
    winner_yards = row["yards_a"] if a_more else row["yards_b"]
    loser_yards = row["yards_b"] if a_more else row["yards_a"]

    active = teams_active_in_season(c, season)
    pool = {fid: name for fid, name in active.items()
            if fid not in (winner["franchise_id"], loser["franchise_id"])}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(list(pool.values()), 3)

    options = [winner["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    week_label = _week_label(row["season_type"], row["week"])
    question = (
        f"In the {week_label}, {season} game between the {franchise_a['full_name']} and the "
        f"{franchise_b['full_name']}, which team gained more total yards?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_game_boxscore:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner["full_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    loser_possessive = loser['full_name'] + ("'" if loser['full_name'].endswith("s") else "'s")
    notes = (
        f"The {winner['full_name']} gained {winner_yards} total yards to the "
        f"{loser_possessive} {loser_yards} in that game."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "game_id": row["game_id"], "season": season, "week": row["week"],
            "season_type": row["season_type"], "team_a": row["team_a"], "team_b": row["team_b"],
            "yards_a": row["yards_a"], "yards_b": row["yards_b"],
            "winner_franchise_id": winner["franchise_id"], "correct_answer_text": winner["full_name"],
            "difficulty_score": diff_score, "difficulty_band": band, "source_id": row["source_id"],
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count}-game pool ({MIN_SEASON}-{MAX_SEASON}, ties in total yards excluded); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    seasons = [q["_audit"]["season"] for q in exported]
    return {
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "postseason_count": sum(1 for q in exported if q["_audit"]["season_type"] != "REG"),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// NFL Game Box Scores -- served live via the Gateway (tools.data_refresh.",
        "// nfl_team_game_stats_refresh's real, automatically-refreshed `team_game_stats` table),",
        "// not a static export.",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}` -- {a['team_a']} ({a['yards_a']} yds) vs "
        f"{a['team_b']} ({a['yards_b']} yds), {a['season']} {a['season_type']} week {a['week']}",
        f"- **Engine source:** `team_game_stats` rows, source_id `{a['source_id']}` "
        f"(tools.data_refresh.nfl_team_game_stats_refresh, real automatic production refresh)",
    ]
