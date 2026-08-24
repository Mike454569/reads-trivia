"""Who Changed? -- Gold Standard concept #27: "Compare two title teams from
the same franchise and identify changed lineup slots." Built directly on 5
real dynasty pairs found in the curated SB_CHAMPION data (same team, two
different Super Bowl-winning seasons): Patriots 2015/2017, Steelers
1970s (4 titles, adjacent pairs), 49ers 1989/1990, Cowboys 1990s (3 titles,
adjacent pairs), and others -- computed directly from real
`curated_nfl_offense_college_board` rows (team_display_name matches, season
ascending, adjacent pairs), never hand-curated. A pair is only used if at
least 1 position's college really changed AND at least 3 stayed the same
(so a fair 4-option MCQ of position names is possible) -- pairs with zero
real change (an identical lineup two years running) or too little overlap
are honestly excluded, never padded.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Who Changed?"
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


def _dynasty_pairs(boards: list[dict]) -> list[tuple[dict, dict]]:
    by_team = defaultdict(list)
    for b in boards:
        by_team[b["team_display_name"]].append(b)
    pairs = []
    for team, group in by_team.items():
        group.sort(key=lambda b: b["season"])
        for i in range(len(group) - 1):
            pairs.append((group[i], group[i + 1]))
    return pairs


def fetch_ordered_candidates(c, seed: str):
    from .. import engine
    boards = common.fetch_boards(c, "SB_CHAMPION")
    pairs = _dynasty_pairs(boards)
    rng_order = engine.seeded(seed)
    rng_order.shuffle(pairs)
    return pairs


def evaluate(c, raw, rng, guard):
    b1, b2 = raw
    diff_label = _DIFF_MAP.get(b2["difficulty"]) or _DIFF_MAP.get(b1["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    changed = [p for p in common.POSITIONS if b1["positions"][p] != b2["positions"][p]]
    unchanged = [p for p in common.POSITIONS if b1["positions"][p] == b2["positions"][p]]
    if len(changed) < 1:
        return "NO_REAL_CHANGE"
    if len(unchanged) < 3:
        return "INSUFFICIENT_DECOY_POSITIONS"

    correct_position = rng.choice(changed)
    decoy_positions = rng.sample(unchanged, 3)
    options = [correct_position] + decoy_positions
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    team = b1["team_display_name"]
    season1, season2 = b1["season"], b2["season"]
    question = (
        f"Between the {team}'s {season1} and {season2} Super Bowl-winning starting offenses, one "
        f"position's starting college changed. Which position?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_who_changed:{b1['board_id']}:{b2['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PAIR"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_position, decoy_positions)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_position:
        return "INVALID_CORRECT_INDEX"

    notes = (
        f"The {team}'s {correct_position} went from {b1['positions'][correct_position]} in {season1} to "
        f"{b2['positions'][correct_position]} in {season2}; the other 3 options' colleges stayed the same "
        f"across both championships."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "board_id_1": b1["board_id"], "board_id_2": b2["board_id"], "correct_answer_text": correct_position,
            "team": team, "season_1": season1, "season_2": season2, "difficulty_band": diff_label,
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real same-franchise adjacent championship pairs "
        f"passed every validation rule (had 1+ real changed position and 3+ unchanged decoy positions); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_who_changed.py -- Who Changed?.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Franchise/seasons:** {a['team']}, {a['season_1']} vs {a['season_2']}",
        f"- **Correct answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position`",
    ]
