"""Shared candidate-fetch/evaluate logic for "who led this team in this
real game in [stat category]" capabilities -- an objective, disclosed
definition of "top offensive performer" (Section 10's own explicit
instruction: never a fabricated cross-position subjective score, always
a single, stated, measurable category the question itself names).

Works for both NFL (`player_game_stats`) and CFB (`cfb_player_game_stats_real`)
via table-name parameters -- same shared-module discipline as every other
`_*_common.py` adapter helper in this package.

Entity is the row with the MAX real value of `stat_column` among a real
team's real roster in one real game (ties excluded -- no single "the"
leader exists for a tie, never arbitrarily broken). The compared value is
never shown in the question text before answering, only in `notes` after.
"""
from __future__ import annotations

from .. import engine, difficulty as difficulty_mod, serializer

# Real, measured N+1 fix (Creator Capability Completion pass): evaluate()'s
# distractor pool query scanned the ENTIRE table (no season/week filter at
# all) per candidate -- the same class of defect found and fixed in the
# other new _*_common.py adapters this pass, here with no bound at all.
# Cached per (table, name_column, stat_column, source_id, verification_status)
# for the duration of one generation call only -- reset at the top of
# fetch_ordered_candidates() (called exactly once per real request).
_pool_cache: dict[tuple, list[str]] = {}

# Same real, already-established safeguard as compiler.py's own
# RelationshipSpec.max_fetched_candidates (see that module's docstring) --
# CFB's cfb_player_game_stats_real is large enough (322,137 rows) that an
# uncapped per-call evaluate() workload is a real risk for a hand-written
# adapter like this one. Truncates the already-shuffled list only.
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c, *, safety_mod, table: str, source_id: str, verification_status: str, attempt_column: str):
    return safety_mod.check_verification_status_safety(
        c, table, source_id, verification_status, where_extra=f"{attempt_column} > 0",
    )


def fetch_ordered_candidates(c, seed: str, *, table: str, game_id_column: str, team_column: str,
                              name_column: str, stat_column: str, attempt_column: str,
                              source_id: str, verification_status: str):
    _pool_cache.clear()
    rows = c.execute(
        f"""
        SELECT t.{game_id_column} AS game_id, t.{team_column} AS team, t.{name_column} AS player_name,
               t.{stat_column} AS stat_value, t.season AS season, t.source_id, t.verification_status
        FROM {table} t
        JOIN (
            SELECT {game_id_column} AS gid, {team_column} AS tm, MAX({stat_column}) AS max_val
            FROM {table} WHERE {attempt_column} > 0 AND {stat_column} IS NOT NULL
            GROUP BY {game_id_column}, {team_column}
        ) leader ON leader.gid = t.{game_id_column} AND leader.tm = t.{team_column} AND leader.max_val = t.{stat_column}
        WHERE t.{attempt_column} > 0 AND t.{stat_column} IS NOT NULL
        ORDER BY t.{game_id_column}, t.{team_column}
        """
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard, *, table: str, game_id_column: str, team_column: str, name_column: str,
             stat_column: str, source_id: str, verification_status: str, stat_label: str, category: str,
             entity_prefix: str, min_season: int, max_season: int):
    if row["source_id"] != source_id or row["verification_status"] != verification_status:
        return "ROW_NOT_VERIFIED"
    if not row["player_name"]:
        return "MISSING_FIELD"

    # Exclude a real tie for the team lead -- no single correct "the" leader exists.
    tie_check = c.execute(
        f"SELECT COUNT(*) AS n FROM {table} WHERE {game_id_column}=? AND {team_column}=? AND {stat_column}=?",
        (row["game_id"], row["team"], row["stat_value"]),
    ).fetchone()
    if tie_check["n"] > 1:
        return "TIE_FOR_TEAM_LEAD"

    season = row["season"]
    correct_name = row["player_name"]

    school_row = c.execute("SELECT school_name FROM schools WHERE school_id=?", (row["team"],)).fetchone()
    if not school_row or not school_row["school_name"]:
        return "UNRESOLVED_SCHOOL_NAME"
    team_display = school_row["school_name"]

    cache_key = (table, name_column, stat_column, source_id, verification_status)
    cached_pool = _pool_cache.get(cache_key)
    if cached_pool is None:
        pool_rows = c.execute(
            f"SELECT DISTINCT {name_column} FROM {table} WHERE {stat_column} IS NOT NULL "
            f"AND source_id=? AND verification_status=?",
            (source_id, verification_status),
        ).fetchall()
        cached_pool = [r[0] for r in pool_rows if r[0]]
        _pool_cache[cache_key] = cached_pool
    pool = [n for n in cached_pool if n != correct_name]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"In a real {season} college football game, who led {team_display} in {stat_label}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"{entity_prefix}:{row['game_id']}:{row['team']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_TEAM_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (max_season - season) / max(max_season - min_season, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_name} led {team_display} with {row['stat_value']} {stat_label} in this real {season} game."

    return {
        "category": category, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "game_id": row["game_id"], "team": row["team"], "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": verification_status, "source_id": source_id,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, stat_label: str, min_season: int, max_season: int) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real candidate team-game {stat_label} leaders on file "
        f"({min_season}-{max_season}); exported the maximum available ({accepted_count}) rather than "
        f"loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def human_review_context(record: dict, *, stat_label: str, table: str) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game/team:** `{a['game_id']}` / {a['team']}, {a['season']} ({stat_label})",
        f"- **Leader:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `{table}`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
