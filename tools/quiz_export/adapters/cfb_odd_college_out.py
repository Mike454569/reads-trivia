"""Odd College Out -- Gold Standard concept #9 from the workbook's own
"10. New Game Modes" backlog: "Show a set of schools where one did not
belong to that champion. 10 true lineup schools + 1 plausible false school;
tap impostor." Built on the same curated `curated_nfl_offense_college_board`
SB_CHAMPION data as sb_champion_offense_college.py -- see that adapter's
own module docstring for the full source audit trail (60 real champions,
1967-2026, no player names).

Shown 4 options: 3 real colleges that WERE part of the champion's starting
offense + 1 plausible college that was NOT -- drawn from `all_colleges()`
(every real college appearing anywhere in this curated dataset), never a
fabricated school name.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Odd College Out"
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

    lineup_colleges = sorted(set(board["positions"].values()))
    if len(lineup_colleges) < 3:
        return "INSUFFICIENT_REAL_COLLEGES"
    real_three = rng.sample(lineup_colleges, 3)

    pool = [col for col in common.all_colleges(c) if col not in board["positions"].values()]
    if len(pool) < 1:
        return "INSUFFICIENT_DISTRACTORS"
    fake_college = rng.choice(pool)

    options = real_three + [fake_college]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    team, season = board["team_display_name"], board["season"]
    question = (
        f"Three of these four colleges were part of the {season} {team}'s Super Bowl-winning starting "
        f"offense. Which one was NOT?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_odd_college_out:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, fake_college, real_three)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != fake_college:
        return "INVALID_CORRECT_INDEX"

    notes = (
        f"{fake_college} was NOT part of the {season} {team}'s Super Bowl-winning starting offense; the "
        f"other three colleges shown were real, curated colleges from that lineup."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": fake_college,
            "team": team, "season": season, "difficulty_band": diff_label,
            "real_three": real_three, "entity_key": entity_key,
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
        "// tools/quiz_export/adapters/cfb_odd_college_out.py -- Odd College Out.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Champion:** {a['season']} {a['team']}",
        f"- **Real colleges shown:** {', '.join(a['real_three'])}",
        f"- **Fake (correct) answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
