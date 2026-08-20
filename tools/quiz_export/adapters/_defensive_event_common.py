"""Shared candidate-fetch/evaluate logic for nfl_plays_defense_ext-based
"who recorded this defensive event" capabilities -- same extraction
discipline as _boxscore_stat_common.py/_coordinator_common.py (see those
modules' docstrings): four near-identical adapters (sack/interception/
forced-fumble/fumble-recovery) differing only in which columns they read
and how the question is worded, not four genuinely different real logics.

Built on `nfl_plays_defense_ext` (237,350 rows, SOURCE_BACKED/NFLVERSE_DATA,
1999-2025). Real resolution rates measured directly before building:
sacks 27,420/30,510 (89.9%), interceptions 11,826/13,354 (88.6%), forced
fumbles and fumble recoveries similarly partial -- every adapter using this
module requires BOTH the player_id AND player_name_raw columns non-null for
its event type, excluding the unresolved remainder rather than guessing.

Answers use the real, source-provided `*_name_raw` text directly (same
"raw sourced name is the real answer" discipline nfl_all_pro.py/nfl_hof.py
already use) -- no player_id join needed for display, though the id column
is still required to be present as a resolution-quality gate.
"""
from __future__ import annotations

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise

REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
MIN_SEASON = 1999
MAX_SEASON = 2025

# Real, measured N+1 fix (Creator Capability Completion pass): evaluate()'s
# distractor pool query scans a +/-3-season window of the 237,350-row
# nfl_plays_defense_ext table -- cheap once, but candidates cluster into a
# small number of distinct (name_column, window) combinations, so re-running
# it per candidate (as originally written) cost 200ms+ x every evaluated
# candidate, the same class of defect the POSITION_LINEUP_GRID/COLLEGE audit
# found. Cached per generation call only -- reset at the top of
# fetch_ordered_candidates() (called exactly once per real generation),
# never persisted across separate requests, so a later data refresh is never
# masked by a stale cache.
_pool_cache: dict[tuple, list[str]] = {}

# Same real, already-established safeguard as compiler.py's own
# RelationshipSpec.max_fetched_candidates -- nfl_plays_defense_ext (237,350
# rows) already proved fast after the pool-cache fix above, but capping
# here too keeps every hand-written large-table adapter in this pass
# consistent and future-proof as the table grows.
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(c, "nfl_plays_defense_ext", REQUIRED_SOURCE_ID)


def fetch_ordered_candidates(c, seed: str, *, id_column: str, name_column: str):
    _pool_cache.clear()
    rows = c.execute(
        f"SELECT game_id, play_id, season, posteam, defteam, {id_column} AS event_player_id, "
        f"{name_column} AS event_player_name, source_id, verification_status "
        f"FROM nfl_plays_defense_ext WHERE {id_column} IS NOT NULL AND {name_column} IS NOT NULL "
        f"AND {name_column} != '' ORDER BY game_id, play_id"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard, *, question_fn, notes_fn, category: str, entity_prefix: str,
             name_column: str):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != "SOURCE_BACKED":
        return "ROW_NOT_VERIFIED"
    if not row["event_player_name"]:
        return "MISSING_FIELD"

    season = row["season"]
    # defteam is the team ON DEFENSE for this play -- the defender plays
    # FOR defteam, against posteam's offense.
    franchise_def, err = resolve_franchise(c, row["defteam"], season)
    franchise_off, err2 = resolve_franchise(c, row["posteam"], season)
    if err or err2 or not franchise_def or not franchise_off:
        return "TEAM_UNRESOLVED"

    correct_name = row["event_player_name"]

    # Section 21 fix: a real, measured multi-valid-answer risk -- 5,953 of
    # 6,870 real games with a resolved sack (86.6%) have MORE THAN ONE
    # distinct real sacker, so a same-game co-participant could otherwise
    # appear as a "wrong" distractor while genuinely also being correct
    # ("who recorded a sack in this game" has more than one right answer
    # when this happens). Every real name that recorded this SAME event
    # type in this SAME game is excluded from the distractor pool, not
    # just the exact correct_name.
    same_game_rows = c.execute(
        f"SELECT DISTINCT {name_column} FROM nfl_plays_defense_ext WHERE game_id = ? AND {name_column} IS NOT NULL",
        (row["game_id"],),
    ).fetchall()
    same_game_names = {r[0] for r in same_game_rows}

    window = (name_column, max(season - 3, MIN_SEASON), min(season + 3, MAX_SEASON))
    cached_pool = _pool_cache.get(window)
    if cached_pool is None:
        pool_rows = c.execute(
            f"SELECT DISTINCT {name_column} FROM nfl_plays_defense_ext "
            f"WHERE {name_column} IS NOT NULL AND season BETWEEN ? AND ?",
            window[1:],
        ).fetchall()
        cached_pool = [r[0] for r in pool_rows]
        _pool_cache[window] = cached_pool
    pool = [n for n in cached_pool if n not in same_game_names]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = question_fn(franchise_def, franchise_off, season)
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"{entity_prefix}:{row['game_id']}:{row['play_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAY"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    return {
        "category": category, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index,
        "notes": notes_fn(correct_name, franchise_def, franchise_off, season),
        "_audit": {
            "season": season, "game_id": row["game_id"], "play_id": row["play_id"],
            "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, event_label: str) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real resolved {event_label} records on file ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def human_review_context(record: dict, *, event_label: str) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Play:** `{a['game_id']}`:`{a['play_id']}`, {a['season']} ({event_label})",
        f"- **Player:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `nfl_plays_defense_ext`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
