"""NFL Game Results domain adapter -- App-Wide Engine Migration operation.

The first capability built on `games` (tools/data_refresh/nfl_games_refresh.py's
real, automatically-refreshed table -- 7,548 real NFL games, 1999-2026,
verified live in production: 7,276 with a final score as of this writing).
This is the proof that newly-ingested game data can become real, generatable,
certified content, not just sit in a table -- Section D/E of the mission.

Real, disclosed data shape (audited directly, not assumed): `games` has no
per-row player-level stats (no passing/rushing/receiving lines -- only
`player_season_stats`, season-level, exists in this database) and no
turnover data. "Guess the stat leader" / "guess the player's stat line"
concepts are NOT honestly buildable from this table -- attempting them
would mean fabricating numbers, which this project never does. What IS
real and buildable: the actual, final, source-backed RESULT of a real game
(who won, by how much, in what context) -- exactly what `games` verifiably
contains. Season-level stat concepts already exist via the Quiz engine
pilots; this adapter is deliberately scoped to what `games` itself proves.

Ties are excluded from the candidate pool (a real, rare NFL outcome --
"which team won" has no correct answer for a tie) rather than adding a
fourth "It was a tie" option that would need its own distinct QA path for
a handful of rows; a future pass could add that as its own predicate if
ever worth the complexity.
"""
from __future__ import annotations

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise, teams_active_in_season

OUT_PATH = None  # this domain is served live via the Gateway AND exportable via
                 # tools/generate_quiz_engine_game_result_production.py, which passes its
                 # own out_path explicitly -- this default is never actually used
GLOBAL_NAME = "QUIZ_DATA_ENGINE_GAME_RESULT"
SEED = "reads-quiz-engine-game-result-production-v1"
ID_START = 660000
TARGET_COUNT = 300
CATEGORY = "NFL Game Results"
REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
TRACK_ENTITY = True  # one question per real game_id
MIN_SEASON = 1999
MAX_SEASON = 2025  # the most recent season with real completed games as of this operation


def safety_check(c) -> dict:
    return safety.check_source_id_only_safety(
        c, "games", REQUIRED_SOURCE_ID,
        where_extra="home_score IS NOT NULL AND away_score IS NOT NULL",
    )


# Cached raw-row fetch, same real fix as cfb_game_result.py's -- see that
# module's comment for the full measured-in-production rationale
# (check_engine_readiness()'s /v1/ready latency incident is the proven
# precedent this mirrors). NFL's 7,548 rows are individually cheaper than
# CFB's 36,184, but the same "re-fetch the full table on every request"
# cost is real here too and only gets worse as nfl_games_refresh.py adds
# more seasons over time.
_CANDIDATE_CACHE: dict = {"rows": None, "fetched_at": 0.0}
_CANDIDATE_CACHE_TTL_SECONDS = 600.0  # 10 min -- generous headroom over the ~once-daily real refresh cadence


def _fetch_raw_rows(c):
    import time
    cached = _CANDIDATE_CACHE["rows"]
    if cached is not None and time.monotonic() - _CANDIDATE_CACHE["fetched_at"] < _CANDIDATE_CACHE_TTL_SECONDS:
        return cached
    # Ties (result_margin=0) excluded -- see module docstring. Regular season
    # + postseason both included (game_type covers REG/WC/DIV/CONF/SB) --
    # every one is a real, completed, source-backed game either way.
    rows = c.execute(
        "SELECT game_id, season, game_type, week, game_date, away_team, away_score, "
        "home_team, home_score, result_margin, overtime, source_id FROM games "
        "WHERE home_score IS NOT NULL AND away_score IS NOT NULL AND result_margin != 0 "
        "AND season BETWEEN ? AND ? ORDER BY game_id",
        (MIN_SEASON, MAX_SEASON),
    ).fetchall()
    rows = list(rows)
    _CANDIDATE_CACHE["rows"] = rows
    _CANDIDATE_CACHE["fetched_at"] = time.monotonic()
    return rows


def fetch_ordered_candidates(c, seed: str):
    rows = list(_fetch_raw_rows(c))  # copy -- the shuffle below must never mutate the shared cache
    rng_order = engine.seeded(seed)
    rng_order.shuffle(rows)
    return rows


_WEEK_LABELS = {"WC": "the Wild Card round", "DIV": "the Divisional round",
                "CON": "the Conference Championship", "SB": "the Super Bowl"}


def _week_label(game_type: str, week) -> str:
    if game_type in _WEEK_LABELS:
        return _WEEK_LABELS[game_type]
    return f"Week {week}"


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID:
        return "ROW_NOT_VERIFIED"

    season = row["season"]
    away_franchise, err = resolve_franchise(c, row["away_team"], season)
    if err:
        return err
    home_franchise, err = resolve_franchise(c, row["home_team"], season)
    if err:
        return err

    winner_is_home = row["home_score"] > row["away_score"]
    winner = home_franchise if winner_is_home else away_franchise
    loser = away_franchise if winner_is_home else home_franchise

    active = teams_active_in_season(c, season)
    pool = {fid: name for fid, name in active.items()
            if fid not in (winner["franchise_id"], loser["franchise_id"])}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(list(pool.values()), 3)

    options = [winner["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    week_label = _week_label(row["game_type"], row["week"])
    question = (
        f"Which team won when the {away_franchise['full_name']} played the "
        f"{home_franchise['full_name']} in {week_label}, {season}?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_game:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner["full_name"]:
        return "INVALID_CORRECT_INDEX"

    # No puzzle_catalog row exists for this domain (same real, disclosed gap
    # lineup.py/cfb_heisman.py already document) -- a recency heuristic,
    # not a claim of empirical validation: older games are harder to recall
    # than recent ones. Deliberately NOT margin-based (a close score doesn't
    # make "who won" harder once the options are presented -- it isn't a
    # live prediction).
    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    margin = abs(row["result_margin"])
    ot_note = " in overtime" if row["overtime"] else ""
    notes = (
        f"The {winner['full_name']} beat the {loser['full_name']} "
        f"{max(row['home_score'], row['away_score'])}-{min(row['home_score'], row['away_score'])}"
        f"{ot_note} ({margin}-point margin)."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "game_id": row["game_id"], "season": season, "week": row["week"], "game_type": row["game_type"],
            "away_team": row["away_team"], "home_team": row["home_team"],
            "away_score": row["away_score"], "home_score": row["home_score"], "margin": margin,
            "winner_franchise_id": winner["franchise_id"], "correct_answer_text": winner["full_name"],
            "difficulty_score": diff_score, "difficulty_band": band, "source_id": row["source_id"],
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count}-game pool ({MIN_SEASON}-{MAX_SEASON}, ties excluded); exported the "
        f"maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    seasons = [q["_audit"]["season"] for q in exported]
    return {
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "postseason_count": sum(1 for q in exported if q["_audit"]["game_type"] != "REG"),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// NFL Game Results -- served live via the Gateway (tools.data_refresh.nfl_games_refresh's",
        "// real, automatically-refreshed `games` table), not a static export.",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}` -- {a['away_team']} @ {a['home_team']}, {a['season']} "
        f"({a['game_type']}, week {a['week']}), final {a['away_score']}-{a['home_score']}",
        f"- **Engine source:** `games` row, source_id `{a['source_id']}` "
        f"(tools.data_refresh.nfl_games_refresh, real automatic production refresh)",
    ]
