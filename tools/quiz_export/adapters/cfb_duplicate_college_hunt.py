"""Duplicate College Hunt -- Gold Standard concept #30: "Given a champion,
find every school represented more than once." Same curated SB_CHAMPION
source as sb_champion_offense_college.py (60 real champions, 1967-2026) --
only the 27 of 60 real boards that genuinely have a college repeated across
2+ positions are eligible (measured directly, never padded); the other 33
correctly produce zero candidates for this specific capability rather than
inventing a duplicate that isn't real.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Duplicate College Hunt"
OUT_PATH = None
REQUIRED_SOURCE_ID = "READS_GOLD_STANDARD_BLUEPRINT_V1"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_GOLD_STANDARD_BLUEPRINT_V1"
TRACK_ENTITY = True
_DIFF_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}


def safety_check(c) -> dict:
    from .. import safety
    return safety.check_verification_status_safety(
        c, "curated_nfl_offense_college_board", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra="board_type = 'SB_CHAMPION'",
    )


def fetch_ordered_candidates(c, seed: str):
    from .. import engine
    boards = common.fetch_boards(c, "SB_CHAMPION")
    rng_order = engine.seeded(seed)
    rng_order.shuffle(boards)
    return boards


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    counts = Counter(board["positions"].values())
    dup_colleges = sorted(col for col, n in counts.items() if n > 1)
    if not dup_colleges:
        return "NO_REAL_DUPLICATE"
    correct_college = rng.choice(dup_colleges)

    single_colleges = sorted(col for col, n in counts.items() if n == 1)
    if len(single_colleges) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractors = rng.sample(single_colleges, 3)

    options = [correct_college] + distractors
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    team, season = board["team_display_name"], board["season"]
    question = (
        f"In the {season} {team}'s Super Bowl-winning starting offense, one college is repeated across "
        f"multiple positions. Which one?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_duplicate_college_hunt:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_college, distractors)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_college:
        return "INVALID_CORRECT_INDEX"

    notes = f"{correct_college} appears {counts[correct_college]} times in the {season} {team}'s starting offense."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": correct_college,
            "team": team, "season": season, "difficulty_band": diff_label,
            "occurrence_count": counts[correct_college], "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real curated Super Bowl champion boards have a "
        f"genuine repeated college (27 of 60 measured directly) AND 3+ single-occurrence decoy colleges; "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_duplicate_college_hunt.py -- Duplicate College Hunt.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Champion:** {a['season']} {a['team']}",
        f"- **Duplicated college (correct answer):** \"{record['options'][record['correctIndex']]}\" "
        f"(appears {a['occurrence_count']}x)",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
