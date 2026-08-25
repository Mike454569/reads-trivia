"""Spot the Fake Lineup -- Gold Standard concept #10: "Show an 11-slot
lineup of colleges with one altered cell; find the wrong position." Same
curated SB_CHAMPION source as sb_champion_offense_college.py (60 real
champions, 1967-2026) -- one position's real college is swapped for a
different, real-but-wrong college (drawn from `all_colleges()`, never
fabricated) in the SHOWN board only; the player must spot which position
doesn't match the real record.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Spot the Fake Lineup"
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

    positions = board["positions"]
    fake_position = rng.choice(common.POSITIONS)
    real_college = positions[fake_position]
    pool = [col for col in common.all_colleges(c) if col != real_college]
    if len(pool) < 1:
        return "INSUFFICIENT_DISTRACTORS"
    fake_college = rng.choice(pool)

    other_positions = [p for p in common.POSITIONS if p != fake_position]
    if len(other_positions) < 3:
        return "INSUFFICIENT_DECOY_POSITIONS"
    decoy_positions = rng.sample(other_positions, 3)

    options = [fake_position] + decoy_positions
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    altered_positions = [{"position": p, "college": (fake_college if p == fake_position else positions[p])} for p in common.POSITIONS]

    team, season = board["team_display_name"], board["season"]
    team_poss = common.possessive(team)
    question = (
        f"Below is the {season} {team_poss} real Super Bowl-winning starting offense by position and "
        f"college -- except one position's college has been swapped for a different, wrong school. "
        f"Which position is wrong?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_spot_the_fake_lineup:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, fake_position, decoy_positions)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != fake_position:
        return "INVALID_CORRECT_INDEX"

    notes = (
        f"The real {season} {team} {fake_position} attended {real_college}, not {fake_college} -- "
        f"the college shown above at that position was swapped in for this puzzle."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "visual_payload": {"positions": altered_positions, "season": season},
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": fake_position,
            "team": team, "season": season, "difficulty_band": diff_label,
            "real_college": real_college, "fake_college": fake_college, "entity_key": entity_key,
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
        "// tools/quiz_export/adapters/cfb_spot_the_fake_lineup.py -- Spot the Fake Lineup.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Champion:** {a['season']} {a['team']}",
        f"- **Fake position (correct answer):** \"{record['options'][record['correctIndex']]}\"",
        f"- **Real college / shown (fake) college:** {a['real_college']} / {a['fake_college']}",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
