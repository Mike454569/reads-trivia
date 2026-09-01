"""Super Bowl champion offense by college (names hidden), guess team + season
-- Rivalry Data + Gold Standard Content Integration operation. This is Gold
Standard concept #1, "College Offense", from the workbook's own "10. New
Game Modes" backlog sheet: "Show 11 colleges by offensive position; guess
champion team + season." Also directly answers this operation's own
explicit request: "Give me a Super Bowl winning offense by colleges and
make me guess the team and season."

--- REAL COVERAGE: 60 OF 60 SUPER BOWLS, 1966-2025 ---
Source: `curated_nfl_offense_college_board`/`curated_nfl_offense_college_position`
(board_type='SB_CHAMPION'), imported from the Gold Standard workbook's
"7. SB Modern (1999-2026)" (28 rows) + "8. SB Historic (I-XXXII)" (32 rows)
sheets -- every real Super Bowl champion from Super Bowl I (1967 Green Bay
Packers) through the real 2026 champion (Seattle Seahawks, consistent with
this Engine's own already-certified NFL championship data), all 11
offensive positions, zero blanks (import-time validated).

--- WHY THE ANSWER IS A COMBINED "YEAR TEAM" STRING, NOT A FRANCHISE_ID ---
This database's real franchise-identity tables (`team_aliases`,
`team_seasons`, `franchises`) all only cover seasons 2002-2026 -- confirmed
directly before writing this adapter. 34 of the 60 real champion seasons
here predate that coverage (1967-2001). Rather than fabricate a franchise_id
link this database cannot actually certify, team identity is carried as the
curated workbook's own plain display text (e.g. "1999 Denver Broncos"), and
the answer combines team + season into one string -- both because the
question asks the player to identify both, and because it sidesteps ever
needing to resolve a pre-2002 franchise_id that does not exist here.

--- WHAT'S NOT SHOWN (real, disclosed) ---
No real player names anywhere in this source table -- the workbook's "4.
Answer Key" sheet (player names, for human QA only) was never imported.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "Super Bowl Champion Offense by College"
OUT_PATH = None  # Director-pipeline-only
REQUIRED_SOURCE_ID = "READS_GOLD_STANDARD_BLUEPRINT_V1"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_GOLD_STANDARD_BLUEPRINT_V1"
TRACK_ENTITY = True
BOARD_TYPE = "SB_CHAMPION"
_DIFF_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}

# Franchise Marathon (Gold Standard concept #19) / Era Gauntlet (#51): both
# are FILTERS on this same base capability, not separate adapters -- Gold
# Standard concept #19 is "given a franchise, solve every championship
# lineup in chronological order" and #51 is "clear one champion puzzle from
# each era in sequence"; both are real selection strategies over the exact
# same 60-board dataset this capability already serves, so reusing the
# mechanic here (rather than writing 2 more near-identical adapters) is the
# same "reuse existing mechanics" discipline this whole operation follows.
SUPPORTS_FILTERS = True
_ERAS = [(1960, 1969), (1970, 1979), (1980, 1989), (1990, 1999), (2000, 2009), (2010, 2019), (2020, 2029)]


def safety_check(c) -> dict:
    from .. import safety
    return safety.check_verification_status_safety(
        c, "curated_nfl_offense_college_board", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra=f"board_type = '{BOARD_TYPE}'",
    )


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None):
    from .. import engine
    boards = common.fetch_boards(c, BOARD_TYPE)
    filters = filters or {}

    franchise_name = filters.get("franchise_name")
    if franchise_name:
        # Franchise Marathon: every real title for one franchise, in real
        # chronological order (not shuffled) -- the whole point of a
        # "marathon" is playing a dynasty's real history in sequence.
        matched = [b for b in boards if b["team_display_name"] == franchise_name]
        matched.sort(key=lambda b: b["season"])
        result = matched
    elif filters.get("era_gauntlet"):
        # Era Gauntlet: exactly one real champion per real represented era,
        # deterministically chosen (seeded), returned oldest-era-first --
        # "clear one puzzle from each era in sequence."
        rng_pick = engine.seeded(f"{seed}:era_gauntlet")
        by_era = {}
        for start, end in _ERAS:
            era_boards = [b for b in boards if start <= b["season"] <= end]
            if era_boards:
                by_era[start] = rng_pick.choice(sorted(era_boards, key=lambda b: b["board_id"]))
        result = [by_era[start] for start in sorted(by_era)]
    else:
        rng_order = engine.seeded(seed)
        rng_order.shuffle(boards)
        result = boards

    # O-Line Only ("More Puzzle Ideas" sheet), composable with any of the
    # branches above -- same "_oline_only" board-dict marker as
    # nfl_offense_college_curated.py's own comment explains.
    if filters.get("oline_only"):
        result = [dict(b, _oline_only=True) for b in result]
    return result


def _display(board) -> str:
    return f"{board['season']} {board['team_display_name']}"


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    all_boards = common.fetch_boards(c, BOARD_TYPE)
    correct_text = _display(board)
    pool = {b["board_id"]: _display(b) for b in all_boards if b["board_id"] != board["board_id"]}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[bid] for bid in distractor_ids]

    options = [correct_text] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    positions = board["positions"]
    oline_only = bool(board.get("_oline_only"))
    shown_positions = ("LT", "LG", "C", "RG", "RT") if oline_only else common.POSITIONS
    if oline_only:
        # All 5 O-Line colleges as the hint -- checked directly against all
        # 60 real boards: even using every OL position, 5 pairs of real
        # champions still share the identical 5-college combination (a real
        # data property of a 60-board pool drawn from a much smaller real
        # college universe, not fixable by adding more OL clues since all 5
        # are already used) -- those specific collisions correctly fall
        # through to the existing DUPLICATE_QUESTION guard below and are
        # skipped, exactly like every other adapter's real, disclosed
        # collision handling (see the non-oline branch's own comment).
        question = (
            f"Hardcore mode: guess the Super Bowl-winning team AND season from its offensive line ONLY "
            f"(LT from {positions['LT']}, LG from {positions['LG']}, C from {positions['C']}, "
            f"RG from {positions['RG']}, RT from {positions['RT']}), shown by position and college -- "
            f"player names hidden."
        )
    else:
        # Four clues, not two -- a real, measured fix: (QB, LT) alone collides
        # text-for-text across 13 of the 60 real champion boards (two different
        # championship seasons can share the same QB+LT college pair), which
        # would otherwise reject a real, distinct board as DUPLICATE_QUESTION
        # purely because of thin question-text phrasing, never because the
        # underlying data repeats. (QB, LT, RB) still collides on 9; (QB, LT,
        # RB, WR1) collides on 0 (measured directly against all 60 real boards
        # before finalizing this) -- still never reveals the season/answer
        # itself, only real, already-shown-on-the-board colleges.
        question = (
            f"Guess the Super Bowl-winning team AND season from its starting offense "
            f"(QB from {positions['QB']}, LT from {positions['LT']}, RB from {positions['RB']}, "
            f"WR1 from {positions['WR1']}), shown by position and college only -- player names hidden."
        )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"sb_champion_offense_college:{board['board_id']}:{'oline' if oline_only else 'full'}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_text, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_text:
        return "INVALID_CORRECT_INDEX"

    # Never include the real season in visual_payload -- season IS half of
    # the answer here (a real gameplay bug caught by the project owner
    # actually playing this mode: showing the year lets a player look up
    # "who won the Super Bowl that year" instead of reading the colleges,
    # defeating the whole puzzle). The `_audit` block below still records it
    # for QA/telemetry -- that stays server-side, never serialized into the
    # player-facing payload (see gateway/services/public_game.py, which
    # passes `visual_payload` straight through to /v1/public/game).
    visual_payload = {
        "positions": [{"position": p, "college": positions[p]} for p in shown_positions],
    }
    if oline_only:
        notes = (
            f"The {correct_text} won the Super Bowl with this starting offensive line (hardcore mode -- "
            f"only the 5 O-Line positions shown, player names hidden). Source: curated Reads Football "
            f"Gold Standard workbook (\"7. SB Modern\" / \"8. SB Historic\" sheets)."
        )
    else:
        notes = (
            f"The {correct_text} won the Super Bowl with this starting offense, shown by position and real "
            f"college for all 11 positions (player names hidden). Source: curated Reads Football Gold Standard "
            f"workbook (\"7. SB Modern\" / \"8. SB Historic\" sheets)."
        )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "visual_payload": visual_payload,
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": correct_text,
            "season": board["season"], "difficulty_band": diff_label,
            "lineup_colleges": [positions[p] for p in shown_positions], "oline_only": oline_only,
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real curated Super Bowl champion offense boards "
        f"passed every validation rule; exported the maximum available ({accepted_count}) rather than "
        f"loosen any rule to reach {target_count}. This is a small, fixed real domain (60 champion seasons, "
        f"one board each)."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/sb_champion_offense_college.py -- Super Bowl Champion Offense by College.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    colleges = ", ".join(a["lineup_colleges"])
    return [
        f"- **Champion:** \"{record['options'][record['correctIndex']]}\"",
        f"- **All 11 offense colleges shown (curated, names hidden):** {colleges}",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position` "
        f"(Gold Standard Game Mode Blueprint workbook, \"7. SB Modern\" / \"8. SB Historic\")",
    ]
