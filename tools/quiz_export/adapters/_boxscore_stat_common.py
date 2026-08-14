"""Shared candidate-fetch/evaluate logic for team_game_stats-based "which
team had more/fewer X" capabilities (sacks, turnovers, penalties -- see
nfl_game_boxscore.py's own HAD_MORE_YARDS for the original, first one of
these, kept as its own untouched file since it predates this module and
nothing requires touching it). Extracted here once three near-identical
~150-line adapters would otherwise exist (sacks/turnovers/penalties), each
differing only in which team_game_stats column they compare and which
direction ("more" is good for sacks recorded, "fewer" is good for
turnovers/penalties committed) -- not "three similar lines," genuinely
duplicated real logic, so sharing it here is the right call, not premature
abstraction.

Each real capability adapter (nfl_game_boxscore_sacks.py etc.) is still its
own small file with its own CATEGORY/predicate/question wording -- this
module only owns the parts that are byte-for-byte identical logic across
all of them.
"""
from __future__ import annotations

import time

from .. import engine, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise, teams_active_in_season

REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
MIN_SEASON = 1999
MAX_SEASON = 2025


def make_cache() -> dict:
    return {"rows": None, "fetched_at": 0.0}


def fetch_raw_rows(c, *, stat_column: str, cache: dict, cache_ttl_seconds: float = 600.0):
    cached = cache["rows"]
    if cached is not None and time.monotonic() - cache["fetched_at"] < cache_ttl_seconds:
        return cached
    rows = c.execute(
        f"""
        SELECT a.game_id, a.season, a.week, a.season_type,
               a.team_code AS team_a, a.{stat_column} AS stat_a,
               b.team_code AS team_b, b.{stat_column} AS stat_b,
               a.source_id
        FROM team_game_stats a
        JOIN team_game_stats b ON a.game_id = b.game_id AND a.team_code < b.team_code
        WHERE a.{stat_column} IS NOT NULL AND b.{stat_column} IS NOT NULL
          AND a.{stat_column} != b.{stat_column}
          AND a.season BETWEEN ? AND ?
        ORDER BY a.game_id
        """,
        (MIN_SEASON, MAX_SEASON),
    ).fetchall()
    rows = list(rows)
    cache["rows"] = rows
    cache["fetched_at"] = time.monotonic()
    return rows


def fetch_ordered_candidates(c, seed: str, *, stat_column: str, cache: dict):
    rows = list(fetch_raw_rows(c, stat_column=stat_column, cache=cache))
    rng_order = engine.seeded(seed)
    rng_order.shuffle(rows)
    return rows


_WEEK_LABEL_POST = "the {week}. postseason round"


def _week_label(season_type: str, week) -> str:
    if season_type == "POST" and week:
        return _WEEK_LABEL_POST.format(week=week)
    return f"Week {week}"


def evaluate_stat_comparison(c, row, rng, guard, *, prefer_lower: bool, question_fn, notes_fn, entity_prefix: str):
    """`question_fn(franchise_a, franchise_b, season, week_label) -> str`,
    `notes_fn(winner, loser, winner_stat, loser_stat) -> str` -- the only
    per-capability wording; everything else (franchise resolution,
    distractor sampling, difficulty, QA) is identical across every stat."""
    if row["source_id"] != REQUIRED_SOURCE_ID:
        return "ROW_NOT_VERIFIED"

    season = row["season"]
    franchise_a, err = resolve_franchise(c, row["team_a"], season)
    if err:
        return err
    franchise_b, err = resolve_franchise(c, row["team_b"], season)
    if err:
        return err

    a_wins = (row["stat_a"] < row["stat_b"]) if prefer_lower else (row["stat_a"] > row["stat_b"])
    winner = franchise_a if a_wins else franchise_b
    loser = franchise_b if a_wins else franchise_a
    winner_stat = row["stat_a"] if a_wins else row["stat_b"]
    loser_stat = row["stat_b"] if a_wins else row["stat_a"]

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
    question = question_fn(franchise_a, franchise_b, season, week_label)
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"{entity_prefix}:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner["full_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = notes_fn(winner, loser, winner_stat, loser_stat)

    return {
        "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "game_id": row["game_id"], "season": season, "week": row["week"],
            "season_type": row["season_type"], "team_a": row["team_a"], "team_b": row["team_b"],
            "stat_a": row["stat_a"], "stat_b": row["stat_b"],
            "winner_franchise_id": winner["franchise_id"], "correct_answer_text": winner["full_name"],
            "difficulty_score": diff_score, "difficulty_band": band, "source_id": row["source_id"],
        },
    }


def extra_funnel_fields(exported) -> dict:
    seasons = [q["_audit"]["season"] for q in exported]
    return {
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "postseason_count": sum(1 for q in exported if q["_audit"]["season_type"] != "REG"),
    }


def human_review_context(record: dict, *, stat_label: str) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}` -- {a['team_a']} ({a['stat_a']} {stat_label}) vs "
        f"{a['team_b']} ({a['stat_b']} {stat_label}), {a['season']} {a['season_type']} week {a['week']}",
        f"- **Engine source:** `team_game_stats` rows, source_id `{a['source_id']}` "
        f"(tools.data_refresh.nfl_team_game_stats_refresh, real automatic production refresh)",
    ]
