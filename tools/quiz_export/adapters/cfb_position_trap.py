"""Position Trap -- Gold Standard concept #29: "Show 11 correct colleges but
swap two positions; identify the swapped pair." Same curated SB_CHAMPION
source as sb_champion_offense_college.py (60 real champions, 1967-2026,
no player names) -- two real positions' colleges are swapped WITH EACH
OTHER in the shown board (never a fabricated college), and the player must
identify which two positions were swapped.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Position Trap"
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


def _pair_label(a: str, b: str) -> str:
    lo, hi = sorted([a, b])
    return f"{lo} & {hi}"


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    positions = board["positions"]
    swappable = [
        (a, b) for i, a in enumerate(common.POSITIONS) for b in common.POSITIONS[i + 1:]
        if positions[a] != positions[b]
    ]
    if not swappable:
        return "NO_SWAPPABLE_PAIR"
    real_pair = swappable[rng.randrange(len(swappable))]
    correct_label = _pair_label(*real_pair)

    other_pairs = [(a, b) for i, a in enumerate(common.POSITIONS) for b in common.POSITIONS[i + 1:] if {a, b} != set(real_pair)]
    decoy_labels = set()
    attempts = 0
    while len(decoy_labels) < 3 and attempts < 50:
        a, b = other_pairs[rng.randrange(len(other_pairs))]
        decoy_labels.add(_pair_label(a, b))
        attempts += 1
    if len(decoy_labels) < 3:
        return "INSUFFICIENT_DECOY_PAIRS"
    decoy_labels = list(decoy_labels)[:3]

    options = [correct_label] + decoy_labels
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    swapped_positions = dict(positions)
    swapped_positions[real_pair[0]], swapped_positions[real_pair[1]] = positions[real_pair[1]], positions[real_pair[0]]
    altered = [{"position": p, "college": swapped_positions[p]} for p in common.POSITIONS]

    team, season = board["team_display_name"], board["season"]
    team_poss = common.possessive(team)
    question = (
        f"Below is the {season} {team_poss} real Super Bowl-winning starting offense by position and "
        f"college -- except two positions' colleges have been swapped with each other. Which two positions?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_position_trap:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_label, decoy_labels)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_label:
        return "INVALID_CORRECT_INDEX"

    notes = (
        f"The real {season} {team} {real_pair[0]} attended {positions[real_pair[0]]} and the real "
        f"{real_pair[1]} attended {positions[real_pair[1]]} -- these two colleges were swapped with each "
        f"other for this puzzle."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "visual_payload": {"positions": altered, "season": season},
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": correct_label,
            "team": team, "season": season, "difficulty_band": diff_label,
            "swapped_pair": list(real_pair), "entity_key": entity_key,
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
        "// tools/quiz_export/adapters/cfb_position_trap.py -- Position Trap.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Champion:** {a['season']} {a['team']}",
        f"- **Swapped pair (correct answer):** {a['swapped_pair'][0]} & {a['swapped_pair'][1]}",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
