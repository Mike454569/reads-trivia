"""NFL Drive Result domain adapter (Creator Capability Completion pass).

Built on `nfl_drives_real` (167,880 rows, SOURCE_BACKED/NFLVERSE_DATA,
real per-drive outcome data). "How did this real drive end" -- entity is
one real drive, answer is the real `result_raw` category as recorded by
the source (Punt/Touchdown/Field goal/Turnover/Turnover on downs/Missed
field goal/Opp touchdown/Safety/End of half -- 142 rows with an empty
string excluded, never guessed at).

No CFB equivalent exists this pass: this Engine has no `cfb_drives`-shaped
table at all (confirmed directly -- `cfb_plays` carries a `drive_id`
column but no separate drive-level result/summary table), a real,
disclosed data gap, not an unwritten adapter.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise

OUT_PATH = None
CATEGORY = "NFL Drive Result"
REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
TRACK_ENTITY = True
MIN_SEASON = 1999
MAX_SEASON = 2025

_REAL_RESULT_CATEGORIES = [
    "Punt", "Touchdown", "Field goal", "Turnover", "End of half",
    "Turnover on downs", "Missed field goal", "Opp touchdown", "Safety",
]


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(
        c, "nfl_drives_real", REQUIRED_SOURCE_ID, where_extra="result_raw != ''",
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT game_id, drive_number, season, offense_team, result_raw, play_count, source_id, verification_status "
        "FROM nfl_drives_real WHERE result_raw != '' ORDER BY game_id, drive_number"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if row["result_raw"] not in _REAL_RESULT_CATEGORIES:
        return "UNRECOGNIZED_RESULT_CATEGORY"
    if not row["play_count"] or row["play_count"] < 1:
        return "EMPTY_DRIVE"

    season = row["season"]
    franchise, err = resolve_franchise(c, row["offense_team"], season)
    if err or not franchise:
        return "TEAM_UNRESOLVED"

    correct_result = row["result_raw"]
    pool = [r for r in _REAL_RESULT_CATEGORIES if r != correct_result]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_result] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = (
        f"In the {season} NFL season, the {franchise['full_name']} had a real "
        f"{row['play_count']}-play drive. How did that drive end?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_drive:{row['game_id']}:{row['drive_number']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_DRIVE"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_result, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_result:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"This {franchise['full_name']} drive in {season} ended in a {correct_result.lower()}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "game_id": row["game_id"], "drive_number": row["drive_number"],
            "correct_answer_text": correct_result,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real drive records on file ({MIN_SEASON}-{MAX_SEASON}); exported the "
        f"maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_drive_result.py -- NFL Drive Result.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Drive:** `{a['game_id']}`:`{a['drive_number']}`, {a['season']}",
        f"- **Result:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `nfl_drives_real`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
