"""Spot the Fake Lineup -- Gold Standard concept #10: "Show a lineup of
colleges with one altered cell; find the wrong slot."

Gold Standard Modes + Creator Quality follow-up pass: now draws from all 5
real board sources in `_group_board_common.py` (SB_CHAMPION,
CURRENT_TEAM_2026, NFL_TEAM_SEASON_ROSTER, DRAFT_CLASS, HONOR_GROUP), not
the single 60-board SB_CHAMPION dataset alone -- see that module's own
docstring for each source's real coverage/provenance. One real slot's real
college is swapped for a different, real-but-wrong college (drawn from that
SAME source's own real college universe, never mixed across sources, never
fabricated) in the SHOWN board only; the player must spot which slot
doesn't match the real record.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _group_board_common as group_common

CATEGORY = "Spot the Fake Lineup"
OUT_PATH = None
REQUIRED_SOURCE_ID = "READS_GOLD_STANDARD_BLUEPRINT_V1"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_GOLD_STANDARD_BLUEPRINT_V1"
TRACK_ENTITY = True
_DIFF_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}

_GROUP_PHRASE = {
    "SB_CHAMPION": "{group} real Super Bowl-winning starting offense",
    "CURRENT_TEAM_2026": "{group} real projected starting offense",
    "NFL_TEAM_SEASON_ROSTER": "{group} real starting offense",
    "DRAFT_CLASS": "{group}",
    "HONOR_GROUP": "{group}",
}


def _group_label(board: dict) -> str:
    kind = board["pool_kind"]
    if kind in ("SB_CHAMPION", "CURRENT_TEAM_2026", "NFL_TEAM_SEASON_ROSTER"):
        team_poss = group_common.curated_common.possessive(board["team_display_name"])
        return f"{board['season']} {team_poss}"
    return board["team_display_name"]


def safety_check(c) -> dict:
    from .. import safety
    return {
        "curated_boards": safety.check_verification_status_safety(
            c, "curated_nfl_offense_college_board", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        ),
        "nfl_team_season_roster": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED", where_extra="starts > 0",
        ),
        "draft_class": safety.check_source_id_only_safety(
            c, "nfl_players_draft", "NFLVERSE_DATA", where_extra="draft_round = 1",
        ),
        "honor_group": safety.check_verification_status_safety(
            c, "nfl_all_pro_selections", "WIKIPEDIA_STRUCTURED", "WIKIPEDIA_STRUCTURED_SECONDARY",
            where_extra="is_ap = 1 AND honor_level = 'FIRST_TEAM'",
        ),
    }


def fetch_ordered_candidates(c, seed: str):
    from .. import engine
    boards = group_common.fetch_all_boards(c)
    rng_order = engine.seeded(seed)
    rng_order.shuffle(boards)
    return boards


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    positions = board["positions"]
    all_slots = list(positions.keys())
    if len(all_slots) < 4:
        return "INSUFFICIENT_REAL_SLOTS"
    fake_slot = rng.choice(all_slots)
    real_college = positions[fake_slot]
    pool = [col for col in group_common.all_colleges_for_kind(c, board["pool_kind"]) if col != real_college]
    if len(pool) < 1:
        return "INSUFFICIENT_DISTRACTORS"
    fake_college = rng.choice(pool)

    other_slots = [p for p in all_slots if p != fake_slot]
    if len(other_slots) < 3:
        return "INSUFFICIENT_DECOY_SLOTS"
    decoy_slots = rng.sample(other_slots, 3)

    options = [fake_slot] + decoy_slots
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    altered_positions = [
        {"position": p, "college": (fake_college if p == fake_slot else positions[p])} for p in all_slots
    ]

    group_phrase = _GROUP_PHRASE[board["pool_kind"]].format(group=_group_label(board))
    question = (
        f"Below is the {group_phrase} by slot and college -- except one slot's college has been swapped "
        f"for a different, wrong school. Which slot is wrong?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_spot_the_fake_lineup:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, fake_slot, decoy_slots)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != fake_slot:
        return "INVALID_CORRECT_INDEX"

    notes = (
        f"The real {fake_slot} in the {group_phrase} was {real_college}, not {fake_college} -- "
        f"the college shown above at that slot was swapped in for this puzzle."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "visual_payload": {"positions": altered_positions, "season": board["season"]},
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": fake_slot,
            "pool_kind": board["pool_kind"], "group": _group_label(board), "season": board["season"],
            "difficulty_band": diff_label,
            "real_college": real_college, "fake_college": fake_college, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real boards (across all 5 real sources) passed "
        f"every validation rule; exported the maximum available ({accepted_count}) rather than loosen any "
        f"rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    by_pool_kind = Counter(q["_audit"]["pool_kind"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band), "pool_kind_distribution": dict(by_pool_kind)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_spot_the_fake_lineup.py -- Spot the Fake Lineup.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Group:** {a['group']} ({a['pool_kind']})",
        f"- **Fake slot (correct answer):** \"{record['options'][record['correctIndex']]}\"",
        f"- **Real college / shown (fake) college:** {a['real_college']} / {a['fake_college']}",
        f"- **Underlying Engine source:** `_group_board_common.py` ({a['pool_kind']})",
    ]
