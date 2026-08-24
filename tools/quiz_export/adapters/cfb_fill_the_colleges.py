"""Fill the Colleges -- Gold Standard concept #6: "Give champion team +
season; type the colleges for the lineup." (reverse direction of College
Offense / NFL_SB_CHAMPION_OFFENSE_COLLEGE). Adapted to this pipeline's
4-option MCQ contract as: name the team+season AND one specific position,
ask which college that position's starter attended -- same curated
SB_CHAMPION source (60 real champions, 1967-2026), see
sb_champion_offense_college.py's own module docstring for the full audit
trail.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Fill the Colleges"
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
    candidates = [(b, p) for b in boards for p in common.POSITIONS]
    rng_order = engine.seeded(seed)
    rng_order.shuffle(candidates)
    return candidates


def evaluate(c, raw, rng, guard):
    board, position = raw
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    correct_college = board["positions"][position]
    pool = [col for col in common.all_colleges(c) if col != correct_college]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractors = rng.sample(pool, 3)

    options = [correct_college] + distractors
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    team, season = board["team_display_name"], board["season"]
    question = f"In the {season} {team}'s Super Bowl-winning starting offense, which college did the {position} attend?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_fill_the_colleges:{board['board_id']}:{position}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD_POSITION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_college, distractors)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_college:
        return "INVALID_CORRECT_INDEX"

    notes = f"The {team}'s {season} starting {position} attended {correct_college}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "board_id": board["board_id"], "position": position, "correct_answer_text": correct_college,
            "team": team, "season": season, "difficulty_band": diff_label, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real curated (champion, position) pairs passed "
        f"every validation rule; exported the maximum available ({accepted_count}) rather than loosen any "
        f"rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_fill_the_colleges.py -- Fill the Colleges.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Champion/position:** {a['season']} {a['team']}, {a['position']}",
        f"- **Correct college:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
