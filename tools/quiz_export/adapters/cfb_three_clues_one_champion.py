"""Three Clues, One Champion -- Gold Standard concept #28: "Reveal exactly
three structured clues; name team + season." A distinct, harder sibling of
NFL_SB_CHAMPION_OFFENSE_COLLEGE (which shows all 11 real positions) -- this
capability reveals only 3 of the 11 real position/college pairs, randomly
chosen per candidate, both in the question text and in `visual_payload`
(never the full board). Same curated SB_CHAMPION source, see
sb_champion_offense_college.py's own module docstring for the full audit
trail (60 real champions, 1967-2026, no player names).
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Three Clues, One Champion"
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


def _display(board) -> str:
    return f"{board['season']} {board['team_display_name']}"


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    all_boards = common.fetch_boards(c, "SB_CHAMPION")
    correct_text = _display(board)
    pool = {b["board_id"]: _display(b) for b in all_boards if b["board_id"] != board["board_id"]}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[bid] for bid in distractor_ids]

    options = [correct_text] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    clue_positions = sorted(rng.sample(common.POSITIONS, 3))
    positions = board["positions"]
    clue_text = ", ".join(f"{p} from {positions[p]}" for p in clue_positions)
    question = f"Exactly 3 clues, 1 champion: {clue_text}. Guess the Super Bowl-winning team AND season."
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_three_clues_one_champion:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_text, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_text:
        return "INVALID_CORRECT_INDEX"

    # Never include the real season in visual_payload -- see
    # sb_champion_offense_college.py's own comment for the real gameplay
    # bug this avoids (season is half the answer here).
    visual_payload = {
        "positions": [{"position": p, "college": positions[p]} for p in clue_positions],
    }
    notes = f"The {correct_text} won the Super Bowl -- these 3 clues are real colleges from its starting offense."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "visual_payload": visual_payload,
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": correct_text,
            "season": board["season"], "difficulty_band": diff_label, "clue_positions": clue_positions,
            "entity_key": entity_key,
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
        "// tools/quiz_export/adapters/cfb_three_clues_one_champion.py -- Three Clues, One Champion.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Champion:** \"{record['options'][record['correctIndex']]}\"",
        f"- **3 revealed clue positions:** {', '.join(a['clue_positions'])}",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
