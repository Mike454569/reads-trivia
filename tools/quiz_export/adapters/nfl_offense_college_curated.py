"""NFL current-team offense by college (names hidden), CURATED source --
Rivalry Data + Gold Standard Content Integration operation.

--- WHY A NEW CAPABILITY, NOT A CHANGE TO lineup_college.py's EXISTING ONE ---
`NFL_OFFENSE_LINEUP_COLLEGE` (lineup_college.py) is real and stays exactly
as-is: 68 real HISTORICAL team-seasons (2006-2018), sourced from the
certified NFL<->CFB identity bridge, 5 skill positions only (OL excluded --
~10% real per-player college coverage, a genuine, disclosed data ceiling).
This is a DIFFERENT real domain: all 32 CURRENT (season 2026) NFL teams,
sourced from the Gold Standard Game Mode Blueprint workbook's own
human-curated "3. Pre-Made Puzzles" sheet, all 11 offensive positions
including the full offensive line (LT/LG/C/RG/RT individually, not a
generic "OL" group) -- a fix the identity-bridge approach could never reach,
because per-player OL college coverage in this database's own certified
bridge is a real, structural ceiling (see lineup_college.py's own module
docstring). The two capabilities have non-overlapping candidate pools (past
seasons vs. the current season) and different position coverage; neither
silently subsumes the other, matching the same "distinct registered
capability" discipline lineup_college.py's own docstring already documents
for its relationship to lineup.py.

--- WHAT MAKES THIS SAFE TO BUILD ON (real, disclosed) ---
Source: `curated_nfl_offense_college_board`/`curated_nfl_offense_college_position`,
imported directly from the Gold Standard workbook's "3. Pre-Made Puzzles"
sheet (32 rows, all 11 positions, zero blanks -- import-time validated, see
the import script). Team identity is resolved to this database's own real
`team_seasons` table for season 2026 (not a fabricated join) -- confirmed
directly: every one of the 32 real team codes on that sheet (after one real
alias fix, LAR -> this database's LA) resolved to a real franchise row.
Player names are never present in this source at all -- the workbook's
"4. Answer Key" sheet (which DOES carry real player names, for human QA
only) was deliberately never imported into any adapter-visible table.

--- REAL, DISCLOSED LIMITATION ---
This is the curated workbook's OWN "projected 2026 starters as of early Aug
2026" snapshot, not a live roster feed -- the workbook's own README caveat
("Always re-verify O-Line before live play -- camp battles move") is
preserved verbatim in every generated question's `notes` field.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as common

CATEGORY = "NFL Offense by College (2026)"
OUT_PATH = None  # Director-pipeline-only
REQUIRED_SOURCE_ID = "READS_GOLD_STANDARD_BLUEPRINT_V1"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_GOLD_STANDARD_BLUEPRINT_V1"
TRACK_ENTITY = True
BOARD_TYPE = "CURRENT_TEAM_2026"
_DIFF_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}

# P1 Release Readiness pass: real, source-checked resolution of the 3
# offensive-line cells the P0 pass flagged as unverifiable in-repo. Live
# web sources (team depth-chart releases + player bios) were checked for
# each -- 2 confirmed correct, 1 still genuinely unresolved (conflicting
# real sources, not a data error assumed from silence):
#   - PIT LG "South Dakota State" -- CONFIRMED. Steelers.com's own released
#     2026 depth chart names Mason McCormick (South Dakota State) as the
#     starting LG; matches Wikipedia. No action needed.
#   - CLE RT "Alabama State" -- CONFIRMED. Multiple 2026 depth-chart
#     sources name Tytus Howard (Alabama State) as the starting RT;
#     matches Wikipedia. No action needed.
#   - ARI RT "Elon" -- STILL UNRESOLVED. A real Elon alum (Oli Udoh) is on
#     the Cardinals' roster at offensive tackle, but is not clearly
#     confirmed as the RT starter specifically -- a dedicated "first depth
#     chart of 2026" source instead names Elijah Wilkinson (UMass) as the
#     RT starter, and a separate roster-projection article names Isaiah
#     Adams (Illinois, primarily a guard) at RT. Three real sources, three
#     different colleges, for the same slot -- exactly the kind of
#     genuine current-roster churn roster_freshness.py exists to describe,
#     concentrated on one team early. Per "do not guess": neither kept as
#     silently trusted nor overwritten with a guessed correction -- the
#     whole board is quarantined below instead (this capability shows all
#     11 positions as one board; there is no way to omit a single cell
#     without breaking the "11 positions, zero blanks" shape every other
#     board keeps, so quarantining the one affected board -- not all 32 --
#     is what "do not invalidate unrelated boards unless necessary" means
#     here). Re-verify and remove from this set once a single, consistent
#     source confirms the real 2026 ARI starting RT.
UNRESOLVED_CURRENT_TEAM_BOARD_IDS = frozenset({"GOLD_CUR_ARI_2026"})


def safety_check(c) -> dict:
    from .. import safety
    result = safety.check_verification_status_safety(
        c, "curated_nfl_offense_college_board", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra=f"board_type = '{BOARD_TYPE}'",
    )
    # P0/P1 Accuracy + Reliability Hardening passes: unlike every other
    # verification_status check above (which only ever asks "was this row
    # imported correctly"), current-team roster data also needs a
    # FRESHNESS answer -- "is this snapshot still likely true". Surfaced
    # here (production_safety.roster_freshness, visible to any admin/
    # Creator caller) AND actually enforced below in
    # fetch_ordered_candidates() -- P1 wires STALE to real quarantine
    # (0 candidates, never a silently-served stale current roster); WARN
    # stays non-blocking by design (a soft signal worth a human re-check,
    # not yet certain enough to take real content down).
    from tools.director_v02 import roster_freshness
    result["roster_freshness"] = roster_freshness.freshness_report()
    return result


def fetch_ordered_candidates(c, seed: str):
    from .. import engine
    from tools.director_v02 import roster_freshness
    # P1 Release Readiness pass: STALE means "do not keep serving this
    # current-team snapshot as if it were still true" -- returning zero
    # candidates here (rather than the real 32 boards) routes through the
    # exact same, already-proven "0 candidates -> qa_status FAILED ->
    # package_contract rejects -> NO_ELIGIBLE_GAME" pipeline the P0 pass
    # built for every other empty-pool case, so this capability degrades
    # exactly like any other temporarily-unavailable one -- never a crash,
    # never a silently-wrong answer. Historical capabilities (lineup.py,
    # sb_champion_offense_college.py, and everything else built on
    # curated_nfl_offense_college_board's OTHER board_type, SB_CHAMPION)
    # are untouched -- this check is scoped to CURRENT_TEAM_2026 data only,
    # the only board_type roster_freshness.py's snapshot date describes.
    if roster_freshness.freshness_report()["status"] == "STALE":
        return []
    boards = common.fetch_boards(c, BOARD_TYPE)
    # P1 Release Readiness pass: quarantine any board with a real,
    # unresolved fact -- see UNRESOLVED_CURRENT_TEAM_BOARD_IDS's own
    # comment above for exactly which board(s), why, and what was checked.
    # Scoped to just the affected board(s) -- the other 31 real,
    # independently-verified boards stay playable.
    boards = [b for b in boards if b["board_id"] not in UNRESOLVED_CURRENT_TEAM_BOARD_IDS]
    rng_order = engine.seeded(seed)
    rng_order.shuffle(boards)
    return boards


def evaluate(c, board, rng, guard):
    diff_label = _DIFF_MAP.get(board["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"

    all_boards = common.fetch_boards(c, BOARD_TYPE)
    pool = {b["board_id"]: b["team_display_name"] for b in all_boards if b["board_id"] != board["board_id"]}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[bid] for bid in distractor_ids]

    options = [board["team_display_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    positions = board["positions"]
    question = (
        f"Guess the NFL team from its 2026 projected starting offense "
        f"(QB from {positions['QB']}, LT from {positions['LT']}), shown by position and college only -- "
        f"player names hidden."
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_offense_college_curated:{board['board_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_BOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, board["team_display_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != board["team_display_name"]:
        return "INVALID_CORRECT_INDEX"

    visual_payload = {
        "positions": [{"position": p, "college": positions[p]} for p in common.POSITIONS],
        "season": board["season"],
    }
    notes = (
        f"The {common.possessive(board['team_display_name'])} projected 2026 starting offense, shown by position and real "
        f"college for all 11 positions (player names hidden). Source: curated Reads Football Gold Standard "
        f"workbook, \"projected 2026 starters as of early Aug 2026\" -- always re-verify the offensive line "
        f"before live play, camp battles move."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "visual_payload": visual_payload,
        "_audit": {
            "board_id": board["board_id"], "team_code": board["team_code"],
            "franchise_id": board["franchise_id"], "correct_answer_text": board["team_display_name"],
            "season": board["season"], "difficulty_band": diff_label,
            "lineup_colleges": [positions[p] for p in common.POSITIONS],
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of the {considered_count} real curated 2026 team offense boards passed "
        f"every validation rule; exported the maximum available ({accepted_count}) rather than loosen any "
        f"rule to reach {target_count}. This is a small, fixed real domain (32 NFL teams, one board each)."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {
        "difficulty_band_distribution": dict(by_band),
        "unique_teams": len({q["_audit"]["team_code"] for q in exported}),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_offense_college_curated.py -- NFL Offense by College (2026, curated).",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    colleges = ", ".join(a["lineup_colleges"])
    return [
        f"- **Team:** `{a['team_code']}` (\"{record['options'][record['correctIndex']]}\"), season {a['season']}",
        f"- **All 11 offense colleges shown (curated, names hidden):** {colleges}",
        f"- **Underlying Engine source:** `curated_nfl_offense_college_board`/`_position` "
        f"(Gold Standard Game Mode Blueprint workbook, \"3. Pre-Made Puzzles\")",
    ]
