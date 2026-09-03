"""Three Clues, One Champion -- Gold Standard concept #28: "Reveal exactly
three structured clues; name team + season."

Gold Standard Modes + Creator Quality follow-up pass: no longer relies
mainly on roster/college clues. Real clue candidates now come from
`_champion_clue_common.py`'s 5 real, independently verified families
(real Super Bowl opponent, real final score, real head coach, real Super
Bowl MVP, and college -- kept as one family among five, never the default).
At least 2 of the 3 revealed clues must be non-roster real facts -- a
champion without enough real non-roster data on file (pre-1999 coach
coverage gap, unresolved MVP) is rejected outright rather than silently
falling back to an all-roster puzzle. Same curated SB_CHAMPION source as
sb_champion_offense_college.py for team+season identity and the college
family (60 real champions, 1966-2025).
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _champion_clue_common as clue_common
from . import _college_offense_curated_common as common

CATEGORY = "Three Clues, One Champion"
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
            where_extra="board_type = 'SB_CHAMPION'",
        ),
        "championship_events": safety.check_verification_status_safety(
            c, "nfl_championship_events", "WIKIPEDIA_STRUCTURED", "WIKIPEDIA_STRUCTURED_SECONDARY",
        ),
        "coach_team_seasons": safety.check_verification_status_safety(
            c, "coach_team_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
        ),
        "sb_mvp": safety.check_verification_status_safety(
            c, "nfl_season_awards", "WIKIPEDIA_STRUCTURED", "WIKIPEDIA_STRUCTURED_SECONDARY",
            where_extra="award_type = 'SB_MVP'",
        ),
    }


# Era Gauntlet (Gold Standard concept #51) redesign (Gold Standard Modes +
# Creator Quality follow-up pass): the OLD version filtered
# NFL_SB_CHAMPION_OFFENSE_COLLEGE (full 11-position roster boards) to one
# per decade -- still a roster/college-list game, just fewer of them. This
# capability's real non-roster clue majority (>=2 of 3 clues from real
# opponent/score/coach/MVP facts, enforced in evaluate()) makes THIS the
# genuine redesign target instead: one real champion per real represented
# decade, chosen only from champions with enough real non-roster data to
# guarantee a real non-roster-majority puzzle for every era slot, returned
# oldest-era-first (a real progression -- earlier eras have less real
# non-roster data on file, e.g. no coach coverage pre-1999, so they are
# naturally harder, not artificially graded).
_ERAS = [(1960, 1969), (1970, 1979), (1980, 1989), (1990, 1999), (2000, 2009), (2010, 2019), (2020, 2029)]
SUPPORTS_FILTERS = True


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None):
    from .. import engine
    filters = filters or {}
    boards = common.fetch_boards(c, "SB_CHAMPION")

    if filters.get("era_gauntlet"):
        eligible = [b for b in boards if len([cl for cl in clue_common.real_available_clues(c, b) if cl[0] != "COLLEGE"]) >= 2]
        rng_pick = engine.seeded(f"{seed}:era_gauntlet")
        by_era = {}
        for start, end in _ERAS:
            era_boards = [b for b in eligible if start <= b["season"] <= end]
            if era_boards:
                by_era[start] = rng_pick.choice(sorted(era_boards, key=lambda b: b["board_id"]))
        return [by_era[start] for start in sorted(by_era)]

    rng_order = engine.seeded(seed)
    rng_order.shuffle(boards)
    return boards


def _display(board) -> str:
    return f"{board['season']} {board['team_display_name']}"


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    all_clues = clue_common.real_available_clues(c, board)
    non_roster = [cl for cl in all_clues if cl[0] != "COLLEGE"]
    roster = [cl for cl in all_clues if cl[0] == "COLLEGE"]
    if len(non_roster) < 2:
        return "INSUFFICIENT_NON_ROSTER_CLUES"

    if len(non_roster) >= 3:
        chosen = [non_roster[i] for i in rng.sample(range(len(non_roster)), 3)]
    else:
        chosen = list(non_roster)
        if not roster:
            return "INSUFFICIENT_CLUES"
        chosen.append(roster[rng.randrange(len(roster))])
    rng.shuffle(chosen)
    clue_families = [family for family, _ in chosen]
    clue_texts = [text for _, text in chosen]

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

    clue_list = "; ".join(clue_texts)
    question = f"Exactly 3 real clues, 1 champion: {clue_list}. Guess the Super Bowl-winning team AND season."
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_three_clues_one_champion:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_text, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_text:
        return "INVALID_CORRECT_INDEX"

    notes = f"The {correct_text} won the Super Bowl -- these 3 real clues ({', '.join(clue_families)}) all describe it."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "board_id": board["board_id"], "correct_answer_text": correct_text,
            "season": board["season"], "difficulty_band": diff_label, "clue_families": clue_families,
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real curated Super Bowl champions had at least "
        f"2 real non-roster clues (real opponent/score/coach/MVP) plus a 3rd real clue on file; exported "
        f"the maximum available ({accepted_count}) rather than loosen the non-roster-majority rule to "
        f"reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    by_family = Counter(family for q in exported for family in q["_audit"]["clue_families"])
    return {"difficulty_band_distribution": dict(by_band), "clue_family_distribution": dict(by_family)}


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
        f"- **3 revealed clue families:** {', '.join(a['clue_families'])}",
        f"- **Underlying Engine source:** `nfl_championship_events` / `coach_team_seasons` / "
        f"`nfl_season_awards` / `curated_nfl_offense_college_board`",
    ]
