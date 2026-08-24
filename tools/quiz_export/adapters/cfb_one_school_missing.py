"""One School Missing -- Gold Standard concept #32: "Show the set of unique
colleges on a champion with one omitted; infer the missing school." Same
curated SB_CHAMPION source as sb_champion_offense_college.py (60 real
champions, 1967-2026) -- the shown set is the champion's real DISTINCT
colleges minus one; the 3 wrong options are real colleges from
`all_colleges()` that were NOT part of this lineup at all (never a college
already visibly shown, which would make the puzzle ill-posed).
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "One School Missing"
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

    distinct_colleges = sorted(set(board["positions"].values()))
    if len(distinct_colleges) < 2:
        return "INSUFFICIENT_DISTINCT_COLLEGES"
    correct_college = rng.choice(distinct_colleges)
    shown_colleges = [c for c in distinct_colleges if c != correct_college]

    pool = [col for col in common.all_colleges(c) if col not in distinct_colleges]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractors = rng.sample(pool, 3)

    options = [correct_college] + distractors
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    team, season = board["team_display_name"], board["season"]
    question = (
        f"Here are {len(shown_colleges)} of the colleges from the {season} {team}'s Super Bowl-winning "
        f"starting offense: {', '.join(shown_colleges)}. Which real college from that offense is missing?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_one_school_missing:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_college, distractors)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_college:
        return "INVALID_CORRECT_INDEX"

    notes = f"{correct_college} was the missing college from the {season} {team}'s starting offense."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": correct_college,
            "team": team, "season": season, "difficulty_band": diff_label,
            "shown_colleges": shown_colleges, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real curated Super Bowl champion boards passed "
        f"every validation rule; exported the maximum available ({accepted_count}) rather than loosen any "
        f"rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_one_school_missing.py -- One School Missing.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Champion:** {a['season']} {a['team']}",
        f"- **Shown colleges:** {', '.join(a['shown_colleges'])}",
        f"- **Missing (correct) college:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
