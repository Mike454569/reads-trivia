"""NFL variant of _game_leader_common.py's shared logic -- kept as its own
small module (rather than forcing a join through the generic table-name-
substitution helper) because `player_game_stats` has no display-name
column of its own (only `player_key`), unlike CFB's
`cfb_player_game_stats_real`, which already carries `player_name` directly
-- a real, structural difference between the two tables' safe queries, not
duplicated logic for its own sake. See _game_leader_common.py for the full
"objective top-performer" rationale this mirrors.
"""
from __future__ import annotations

from .. import engine, safety, difficulty as difficulty_mod, serializer

REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
MIN_SEASON = 1999
MAX_SEASON = 2025

# Real, measured N+1 fix (Creator Capability Completion pass) -- same defect,
# same fix as _game_leader_common.py's own (its CFB twin): evaluate()'s
# distractor pool query re-joined the full player_game_stats/canonical_players
# tables per candidate. Cached per stat_column for the duration of one
# generation call only -- reset at the top of fetch_ordered_candidates().
_pool_cache: dict[str, list[str]] = {}

# Same real, already-established safeguard as compiler.py's own
# RelationshipSpec.max_fetched_candidates -- player_game_stats is smaller
# than CFB's equivalent, but capping here too keeps every hand-written
# large-table adapter in this pass consistent and future-proof.
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c, *, attempt_column: str) -> dict:
    return safety.check_table_wide_safety(c, "player_game_stats", REQUIRED_SOURCE_ID, where_extra=f"{attempt_column} > 0")


def fetch_ordered_candidates(c, seed: str, *, stat_column: str, attempt_column: str):
    _pool_cache.clear()
    rows = c.execute(
        f"""
        SELECT g.game_id, g.team_code AS team, g.season, cp.display_name AS player_name,
               g.{stat_column} AS stat_value, g.source_id, g.verification_status
        FROM player_game_stats g
        JOIN canonical_players cp ON cp.player_id = g.player_key
        JOIN (
            SELECT game_id, team_code, MAX({stat_column}) AS max_val
            FROM player_game_stats WHERE {attempt_column} > 0 AND {stat_column} IS NOT NULL
            GROUP BY game_id, team_code
        ) leader ON leader.game_id = g.game_id AND leader.team_code = g.team_code AND leader.max_val = g.{stat_column}
        WHERE g.{attempt_column} > 0 AND g.{stat_column} IS NOT NULL
        ORDER BY g.game_id, g.team_code
        """
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard, *, stat_column: str, stat_label: str, category: str, entity_prefix: str):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if not row["player_name"]:
        return "MISSING_FIELD"

    tie_check = c.execute(
        f"SELECT COUNT(*) AS n FROM player_game_stats WHERE game_id=? AND team_code=? AND {stat_column}=?",
        (row["game_id"], row["team"], row["stat_value"]),
    ).fetchone()
    if tie_check["n"] > 1:
        return "TIE_FOR_TEAM_LEAD"

    correct_name = row["player_name"]
    season = row["season"]

    from .draft import resolve_franchise
    franchise, err = resolve_franchise(c, row["team"], season)
    if err or not franchise:
        return "TEAM_UNRESOLVED"
    team_display = franchise["full_name"]

    cached_pool = _pool_cache.get(stat_column)
    if cached_pool is None:
        pool_rows = c.execute(
            f"SELECT DISTINCT cp.display_name FROM player_game_stats g "
            f"JOIN canonical_players cp ON cp.player_id = g.player_key "
            f"WHERE g.{stat_column} IS NOT NULL "
            f"AND g.source_id=? AND g.verification_status=?",
            (REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS),
        ).fetchall()
        cached_pool = [r[0] for r in pool_rows if r[0]]
        _pool_cache[stat_column] = cached_pool
    pool = [n for n in cached_pool if n != correct_name]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"In this real {season} NFL game, who led the {team_display} in {stat_label}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"{entity_prefix}:{row['game_id']}:{row['team']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_TEAM_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_name} led the {team_display} with {row['stat_value']} {stat_label} in this real {season} game."

    return {
        "category": category, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "game_id": row["game_id"], "team": row["team"], "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, stat_label: str) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real candidate team-game {stat_label} leaders on file "
        f"({MIN_SEASON}-{MAX_SEASON}); exported the maximum available ({accepted_count}) rather than "
        f"loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def human_review_context(record: dict, *, stat_label: str) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game/team:** `{a['game_id']}` / {a['team']}, {a['season']} ({stat_label})",
        f"- **Leader:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `player_game_stats`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
