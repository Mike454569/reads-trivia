"""Odd College Out -- Gold Standard concept #9 from the workbook's own
"10. New Game Modes" backlog: "Show a set of schools where one did not
belong to that champion. 10 true lineup schools + 1 plausible false school;
tap impostor."

Gold Standard Modes + Creator Quality follow-up pass: no longer built on
the single 60-board SB_CHAMPION dataset alone -- now draws from all 5 real
board sources in `_group_board_common.py` (SB_CHAMPION, CURRENT_TEAM_2026,
NFL_TEAM_SEASON_ROSTER, DRAFT_CLASS, HONOR_GROUP), so a real playthrough
sees a real 2014 team-season roster's colleges one round, a real Round-1
draft class's colleges the next, a real All-Pro class's colleges after
that -- not five rounds of the same 60 Super Bowl boards. See that module's
own docstring for each source's real coverage and provenance.

Shown 4 options: 3 real colleges that WERE part of the shown real group +
1 plausible college that was NOT -- drawn from that SAME source's own real
college universe (`all_colleges_for_kind()`), never mixed across sources
and never a fabricated school name.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _group_board_common as group_common

CATEGORY = "Odd College Out"
OUT_PATH = None
REQUIRED_SOURCE_ID = "READS_GOLD_STANDARD_BLUEPRINT_V1"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_GOLD_STANDARD_BLUEPRINT_V1"
TRACK_ENTITY = True
_DIFF_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}


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


# Real, plain-English phrase for "the group these colleges belong to" per
# real source -- never a fabricated description, each one matches exactly
# what _group_board_common.py's own docstring discloses about that source.
_GROUP_PHRASE = {
    "SB_CHAMPION": "{group} Super Bowl-winning starting offense",
    "CURRENT_TEAM_2026": "{group} projected starting offense",
    "NFL_TEAM_SEASON_ROSTER": "{group} real starting offense",
    "DRAFT_CLASS": "{group}",
    "HONOR_GROUP": "{group}",
}


def _group_label(board: dict) -> str:
    kind = board["pool_kind"]
    if kind in ("SB_CHAMPION", "CURRENT_TEAM_2026", "NFL_TEAM_SEASON_ROSTER"):
        team_poss = group_common.curated_common.possessive(board["team_display_name"])
        return f"{board['season']} {team_poss}"
    return board["team_display_name"]  # DRAFT_CLASS/HONOR_GROUP already carry a full real phrase


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    lineup_colleges = sorted(set(board["positions"].values()))
    if len(lineup_colleges) < 3:
        return "INSUFFICIENT_REAL_COLLEGES"
    real_three = rng.sample(lineup_colleges, 3)

    pool = [col for col in group_common.all_colleges_for_kind(c, board["pool_kind"]) if col not in board["positions"].values()]
    if len(pool) < 1:
        return "INSUFFICIENT_DISTRACTORS"
    fake_college = rng.choice(pool)

    options = real_three + [fake_college]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    group_phrase = _GROUP_PHRASE[board["pool_kind"]].format(group=_group_label(board))
    question = f"Three of these four colleges were part of the {group_phrase}. Which one was NOT?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_odd_college_out:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, fake_college, real_three)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != fake_college:
        return "INVALID_CORRECT_INDEX"

    notes = (
        f"{fake_college} was NOT part of the {group_phrase}; the other three colleges shown were real, "
        f"verified colleges from that real group."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": fake_college,
            "pool_kind": board["pool_kind"], "group": _group_label(board), "season": board["season"],
            "difficulty_band": diff_label, "real_three": real_three, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real boards (across all 5 real sources -- Super "
        f"Bowl champions, current teams, real team-season rosters, real draft classes, real All-Pro "
        f"classes) passed every validation rule; exported the maximum available ({accepted_count}) rather "
        f"than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    by_pool_kind = Counter(q["_audit"]["pool_kind"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band), "pool_kind_distribution": dict(by_pool_kind)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_odd_college_out.py -- Odd College Out.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Group:** {a['group']} ({a['pool_kind']})",
        f"- **Real colleges shown:** {', '.join(a['real_three'])}",
        f"- **Fake (correct) answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `_group_board_common.py` ({a['pool_kind']})",
    ]
