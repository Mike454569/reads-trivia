"""Shared candidate-fetch/evaluate logic for cfb_player_game_stats_real
same-week player comparisons (rushing/passing/receiving yards) -- same
extraction discipline as _boxscore_stat_common.py/_defensive_event_common.py:
three near-identical adapters differing only in which stat column and
attempt-floor they use.

Answers the real manual-failure prompt directly: "two college running
backs from the same week... who rushed for more yards" -- entity is a real
PAIR of (player, game) rows in the same (season, week) with the same real
stat column recorded and a different value (no tie -- excluded, never
resolved either way). Both players' real per-game stat lines come from
`cfb_player_game_stats_real` (322,137 rows, SOURCE_BACKED_DERIVED/
SPORTSDATAVERSE_CFB, 2014-2025) -- the raw value being compared is NEVER
shown in the question text before answering (see each adapter's own
_question()), only in `notes` after the fact, matching Section 20's
answer-leakage requirement.
"""
from __future__ import annotations

from .. import engine, safety, difficulty as difficulty_mod, serializer

REQUIRED_SOURCE_ID = "SPORTSDATAVERSE_CFB"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_DERIVED"
MIN_SEASON = 2014
MAX_SEASON = 2025

# Real, measured N+1 fix (Creator Capability Completion pass): evaluate()'s
# distractor pool query scans the full season's worth of
# cfb_player_game_stats_real (322,137 rows total across 2014-2025) --
# cheap once, expensive re-run per candidate (same class of defect found
# and fixed in _defensive_event_common.py and nfl_first_touchdown.py this
# same pass). Cached per (stat_column, season) for the duration of one
# generation call only -- reset at the top of fetch_ordered_candidates()
# (called exactly once per real request), never persisted across requests.
_pool_cache: dict[tuple, list[str]] = {}

# Same real, already-established safeguard compiler.py's own
# RelationshipSpec.max_fetched_candidates uses (see that module's docstring:
# a real, measured 116s single request at CFB's ~270K-row scale before this
# cap existed there). This table is comparably large (322,137 rows) and this
# is a hand-written adapter, so it needs the same cap applied directly --
# the already-shuffled candidate list is truncated AFTER fetch, so this only
# bounds per-call evaluate() workload, never the real eligible-pool count
# reported elsewhere.
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c, *, stat_column: str, attempt_column: str) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_player_game_stats_real", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra=f"{attempt_column} > 0",
    )


def fetch_ordered_candidates(c, seed: str, *, stat_column: str, attempt_column: str):
    _pool_cache.clear()
    rows = c.execute(
        f"SELECT game_id, season, week, cfb_player_id, player_name, {stat_column} AS stat_value, "
        f"source_id, verification_status "
        f"FROM cfb_player_game_stats_real WHERE {attempt_column} > 0 AND {stat_column} IS NOT NULL "
        f"ORDER BY season, week, cfb_player_id"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard, *, stat_column: str, attempt_column: str, stat_label: str,
             category: str, entity_prefix: str):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"

    season, week = row["season"], row["week"]
    partner_rows = c.execute(
        f"SELECT cfb_player_id, player_name, {stat_column} AS stat_value FROM cfb_player_game_stats_real "
        f"WHERE season=? AND week=? AND {attempt_column} > 0 AND {stat_column} IS NOT NULL "
        f"AND cfb_player_id != ? AND {stat_column} != ? "
        f"AND source_id=? AND verification_status=?",
        (season, week, row["cfb_player_id"], row["stat_value"], REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS),
    ).fetchall()
    if not partner_rows:
        return "NO_SAME_WEEK_PARTNER"
    partner = partner_rows[rng.randrange(len(partner_rows))]

    player_a_name, player_a_value = row["player_name"], row["stat_value"]
    player_b_name, player_b_value = partner["player_name"], partner["stat_value"]
    if not player_a_name or not player_b_name:
        return "MISSING_FIELD"
    if player_a_name == player_b_name:
        return "SAME_DISPLAY_NAME_AMBIGUOUS"  # two distinct real players who happen to share a display name -- excluded, never guessed at

    winner_name = player_a_name if player_a_value > player_b_value else player_b_name

    cache_key = (stat_column, season)
    cached_pool = _pool_cache.get(cache_key)
    if cached_pool is None:
        pool_rows = c.execute(
            f"SELECT DISTINCT player_name FROM cfb_player_game_stats_real "
            f"WHERE season=? AND {attempt_column} > 0 AND {stat_column} IS NOT NULL",
            (season,),
        ).fetchall()
        cached_pool = [r["player_name"] for r in pool_rows]
        _pool_cache[cache_key] = cached_pool
    pool = [n for n in cached_pool if n not in (player_a_name, player_b_name)]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [winner_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = (
        f"In Week {week} of the {season} college football season, {player_a_name} and {player_b_name} "
        f"both had real {stat_label}. Who had more?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"{entity_prefix}:{season}:{week}:{'|'.join(sorted([row['cfb_player_id'], partner['cfb_player_id']]))}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PAIR"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    hi, lo = max(player_a_value, player_b_value), min(player_a_value, player_b_value)
    notes = f"{winner_name} had {hi} {stat_label} that week, compared to {lo}."

    return {
        "category": category, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "week": week, "correct_answer_text": winner_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, stat_label: str) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real candidate {stat_label} performances on file ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def human_review_context(record: dict, *, stat_label: str) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Week:** {a['season']} Week {a['week']} ({stat_label})",
        f"- **Winner:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_player_game_stats_real`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
