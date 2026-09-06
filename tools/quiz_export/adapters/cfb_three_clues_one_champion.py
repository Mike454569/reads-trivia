"""Three Clues, One Champion / Era Gauntlet -- Gold Standard concept #28:
"Reveal exactly three structured clues; name team + season."

Era Gauntlet rebuild (Pass 2.7): this domain used to draw ONLY from the 60
real Super Bowl champions (`curated_nfl_offense_college_board`,
board_type='SB_CHAMPION') -- 100% Super Bowl content by construction, since
that was the only real pool this adapter ever imported, despite
`_group_board_common.py`'s wider, already-proven 5-source pool sitting
right next to it and already used by 3 sibling adapters. Now draws from the
3 pool_kinds that genuinely represent a real (team, season) pair --
SB_CHAMPION (60), CURRENT_TEAM_2026 (32), NFL_TEAM_SEASON_ROSTER (410) --
502 real boards instead of 60. (DRAFT_CLASS/HONOR_GROUP are deliberately
excluded: they represent a draft class or an All-Pro class, not a team's
season, so "guess the team AND season" has no coherent answer for them.)

Real clue candidates come from `_champion_clue_common.py`'s real,
independently verified families -- see that module's own docstring for the
full real-fact-by-pool_kind breakdown (opponent/score/SB MVP for real
champions; real head coach and real season record/playoff result for ANY
team-season; college, for every pool_kind). At least 2 of the 3 revealed
clues must be non-roster real facts -- a board without enough real
non-roster data on file (pre-1999 coach coverage gap, unresolved MVP, no
standings row) is rejected outright rather than silently falling back to an
all-roster puzzle -- unchanged discipline, now applied across the wider
pool.

Question/notes wording is pool_kind-aware (Pass 2.7 fix): the OLD hardcoded
"Guess the Super Bowl-winning team AND season" would have been FALSE for
the newly-added non-champion boards (a CURRENT_TEAM_2026/
NFL_TEAM_SEASON_ROSTER board's real answer team did not necessarily win
the Super Bowl that season) -- see _question_and_notes_template() below.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _champion_clue_common as clue_common
from . import _group_board_common as group_common

CATEGORY = "Three Clues, One Champion"
OUT_PATH = None
REQUIRED_SOURCE_ID = "READS_GOLD_STANDARD_BLUEPRINT_V1"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_GOLD_STANDARD_BLUEPRINT_V1"
TRACK_ENTITY = True
_DIFF_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}

# The 3 real pool_kinds this domain can coherently ask "guess the team AND
# season" about -- see module docstring for why DRAFT_CLASS/HONOR_GROUP are
# excluded.
_TEAM_SEASON_POOL_KINDS = ("SB_CHAMPION", "CURRENT_TEAM_2026", "NFL_TEAM_SEASON_ROSTER")

# Era anti-leak rule (Pass 2.7): distractors must be plausible teams from
# roughly the same period, never a random mix across 60 years -- a +/-12
# year window around the real answer's season, widened only if that window
# doesn't have enough real distinct options.
_DISTRACTOR_ERA_WINDOW_YEARS = 12


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
        "season_standings": safety.check_verification_status_safety(
            c, "season_standings", "NFLVERSE_DATA", "SOURCE_BACKED",
        ),
    }


# Era Gauntlet (Gold Standard concept #51): one real board per real
# represented decade, chosen only from boards with enough real non-roster
# data to guarantee a real non-roster-majority puzzle for every era slot,
# returned oldest-era-first (a real progression -- earlier eras have less
# real non-roster data on file, e.g. no coach/standings coverage pre-2002,
# so they naturally lean on SB_CHAMPION's own opponent/score/MVP facts
# instead, never artificially graded).
_ERAS = [(1960, 1969), (1970, 1979), (1980, 1989), (1990, 1999), (2000, 2009), (2010, 2019), (2020, 2029)]
SUPPORTS_FILTERS = True



# Real perf fix caught by this pass's own test suite, not assumed: evaluate()
# below used to re-call group_common.fetch_all_boards() once PER CANDIDATE
# to build the distractor pool (502 real calls for a real 502-board pool).
# That function's own docstring says it's designed to be "called exactly
# once per real request, before any evaluate() calls" -- it CLEARS its own
# internal per-pool_kind cache on every call, so calling it 502 times
# doesn't just skip the cache, it actively defeats it, redoing every real
# source query (including NFL_TEAM_SEASON_ROSTER's own real per-team-season
# resolve_franchise() joins) 502 times. Measured directly: this alone
# accounted for ~145ms/candidate, ~73s total for a 502-board pool -- enough
# to blow generation.py's 45s GENERATION_TIMEOUT_SECONDS on every single
# public request (confirmed: gateway/tests/test_public_mode_wiring.py's
# cfb_three_clues_guess round-trip test consistently timed out at 45.4s
# before this fix). fetch_ordered_candidates() is always called exactly
# once before any evaluate() call in the real pipeline
# (game_director_v01.generate_package_from_spec()) -- caching its own
# all_boards list here, once, and having evaluate() reuse it instead of
# re-fetching respects the same one-call contract group_common.py's own
# cache already assumes, just one level up.
_all_boards_cache: list[dict] | None = None


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None):
    global _all_boards_cache
    from .. import engine
    filters = filters or {}
    boards = group_common.fetch_all_boards(c, pool_kinds=_TEAM_SEASON_POOL_KINDS)
    _all_boards_cache = boards

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

    # Reuse the list fetch_ordered_candidates() already built -- see the
    # module-level _all_boards_cache docstring above for why re-calling
    # group_common.fetch_all_boards() here would be a real, measured perf
    # regression, not just a style choice. Falls back to a fresh fetch only
    # if evaluate() were ever somehow called without fetch_ordered_candidates()
    # having run first (never true in the real pipeline, but a safe, cheap
    # guard rather than a hard crash).
    all_boards = _all_boards_cache if _all_boards_cache is not None else group_common.fetch_all_boards(c, pool_kinds=_TEAM_SEASON_POOL_KINDS)
    correct_text = _display(board)
    others = [b for b in all_boards if b["board_id"] != board["board_id"]]
    # Era anti-leak rule (Pass 2.7): prefer distractors from roughly the
    # same period as the real answer, not an unscoped mix across 60 years
    # of real team-seasons -- widen the window only if it doesn't have
    # enough real, distinct options (never silently narrower than needed).
    season = board["season"]
    near = {b["board_id"]: _display(b) for b in others
            if abs(b["season"] - season) <= _DISTRACTOR_ERA_WINDOW_YEARS and _display(b) != correct_text}
    pool = near if len(near) >= 3 else {b["board_id"]: _display(b) for b in others if _display(b) != correct_text}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[bid] for bid in distractor_ids]

    options = [correct_text] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    # Pool_kind-aware wording (Pass 2.7 fix): the old hardcoded "Guess the
    # Super Bowl-winning team AND season" would be FALSE for a non-champion
    # board (CURRENT_TEAM_2026/NFL_TEAM_SEASON_ROSTER) -- its real answer
    # team did not necessarily win the Super Bowl that season.
    is_champion = board.get("pool_kind") == "SB_CHAMPION"
    clue_list = "; ".join(clue_texts)
    ask = "Guess the Super Bowl-winning team AND season." if is_champion else "Guess the team AND season."
    question = f"Exactly 3 real clues, 1 team: {clue_list}. {ask}"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_three_clues_one_champion:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_text, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_text:
        return "INVALID_CORRECT_INDEX"

    notes = (
        f"The {correct_text} won the Super Bowl -- these 3 real clues ({', '.join(clue_families)}) all describe it."
        if is_champion else
        f"These 3 real clues ({', '.join(clue_families)}) all describe the {correct_text}."
    )

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
        f"Only {accepted_count} of the {considered_count} real team-seasons (Super Bowl champions, current "
        f"2026 teams, and historical team-season rosters) had at least 2 real non-roster clues (real "
        f"opponent/score/coach/MVP/season record) plus a 3rd real clue on file; exported the maximum "
        f"available ({accepted_count}) rather than loosen the non-roster-majority rule to reach {target_count}."
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
        f"- **Answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **3 revealed clue families:** {', '.join(a['clue_families'])}",
        f"- **Underlying Engine source:** `nfl_championship_events` / `coach_team_seasons` / "
        f"`nfl_season_awards` / `season_standings` / `curated_nfl_offense_college_board` / "
        f"`canonical_roster_seasons`",
    ]
