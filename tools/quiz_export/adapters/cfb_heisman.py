"""Heisman Trophy domain adapter -- CFB Heisman Winners (production deployment
+ CFB data enrichment operation, Phase 12/14).

--- WHY HEISMAN, NOT ANOTHER CFB AWARD ---
The v1.8 report already found and disclosed real CFB award data limits: this
database's `cfb_award_facts` table contains exactly ONE award type --
Heisman Trophy, 91 rows, 1935-2025 -- confirmed directly this phase
(`SELECT DISTINCT award_name` returns a single value). There is no
All-America, no positional award, no conference award data anywhere in this
database. This adapter builds the one real, honest award-based game the
data actually supports; it does not claim broader awards coverage.

--- WHY THIS DATA IS SAFE TO BUILD ON (audited before writing this file) ---
`cfb_award_facts`: 91/91 rows have a non-null `school_id`, a single
`verification_status` value (`SOURCE_BACKED_FROM_CFB_MASTER`), zero
duplicate (award_year, cfb_player_id) pairs (Heisman is one winner per
year by construction). Compare to `cfb_coaches` (audited the same session):
that table has visible parsing-artifact rows (e.g. a coach "name" that is
actually a mis-parsed win-percentage value) -- genuinely NOT safe to build
a game on without real cleanup first. Heisman was chosen specifically
because it is the one CFB award domain that is completely clean, not
because it was the first one checked.

--- WHY DISTRACTOR SCHOOLS AREN'T SEASON-SCOPED (a disclosed, real limitation) ---
Draft/Championship (NFL) source distractors from `team_aliases`, which is
season-scoped (`teams_active_in_season()`), because Game Factory's own
franchise-lineage model makes that precise and correct. The CFB equivalent,
`cfb_school_seasons`, only covers 2002-2025 -- Heisman goes back to 1935.
Rather than either (a) fabricating pre-2002 season-scoped participation, or
(b) restricting this entire capability to 2002+ and silently discarding 66
real years of real winners, this adapter still does not season-scope
distractors. Every option shown is still a REAL school that plays/played
real college football, never an invented name.

--- DISTRACTOR QUALITY FIX (live-generated-game quality pass) ---
Originally sampled distractors uniformly at random from ALL 805 schools in
`schools`. Caught by actually playing this mode, not assumed: a famous
Heisman winner (e.g. Ohio State, Notre Dame, LSU) ended up surrounded by
random Division-III/NAIA names ("Presentation", "Mars Hill", "Nichols
College") no real fan would ever consider plausible -- the correct answer
was obvious by elimination alone, without knowing any football. Fixed via
`tools.quiz_export.distractors.sample_plausible()`: distractors now prefer
the pool of OTHER real schools that have themselves produced a Heisman
winner (41 distinct schools across 91 real winners -- confirmed directly
against `cfb_award_facts`, always >= 3 excluding the correct answer, so the
full-805 fallback is never actually needed in practice, but stays in place
as a genuine fallback, never removed). A wrong option is now always a real
program a football fan would recognize as football-relevant, never a
structurally obvious giveaway.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .. import distractors as distractors_mod

OUT_PATH = None  # Director-pipeline-only, like player_from_clues and lineup
CATEGORY = "CFB Heisman Winners"
AWARD_NAME = "Heisman Trophy"
# Real, registered, approved_for_import source (confirmed directly against
# the `sources` table before writing this) -- NOT the same string as the
# verification_status value below, a real mix-up caught by actually running
# generation.generate() against this adapter (see safety.py's new
# check_verification_status_safety() docstring for the full story: this
# table has no per-row source_id column at all, unlike every NFL adapter's
# table, so the existing check_table_wide_safety() genuinely does not fit).
REQUIRED_SOURCE_ID = "READS_CFB_MASTER"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_CFB_MASTER"
TRACK_ENTITY = True  # one real winner per year -- guard against ever repeating a player within one export

MIN_YEAR = 1935
MAX_YEAR = 2025  # matches the real, current MAX(award_year) -- see module docstring's audit


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_award_facts", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra="award_name = 'Heisman Trophy'",
    )


def _all_real_schools(c) -> dict:
    rows = c.execute("SELECT school_id, school_name FROM schools").fetchall()
    return {r["school_id"]: r["school_name"] for r in rows}


def _heisman_winning_schools(c) -> dict:
    """The plausible-distractor pool: every real school that has itself
    produced at least one real Heisman winner -- 41 distinct schools across
    the 91 real winners (confirmed by direct query). A wrong option drawn
    from this pool is always a school a football fan would recognize as
    genuinely Heisman-caliber, not a random name from the full 805-school
    universe."""
    rows = c.execute(
        "SELECT DISTINCT school_id, school_name FROM cfb_award_facts "
        "WHERE award_name = ? AND verification_status = ?",
        (AWARD_NAME, REQUIRED_VERIFICATION_STATUS),
    ).fetchall()
    return {r["school_id"]: r["school_name"] for r in rows}


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT award_year, player_name, school_id, school_name FROM cfb_award_facts "
        "WHERE award_name = ? AND verification_status = ? ORDER BY award_year",
        (AWARD_NAME, REQUIRED_VERIFICATION_STATUS),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    year = row["award_year"]
    if not (MIN_YEAR <= year <= MAX_YEAR):
        return "YEAR_OUT_OF_RANGE"
    if not row["school_id"] or not row["school_name"]:
        return "MISSING_SCHOOL"

    plausible_schools = _heisman_winning_schools(c)
    full_schools = _all_real_schools(c)
    distractor_map = distractors_mod.sample_plausible(rng, row["school_id"], plausible_schools, full_schools, k=3)
    if distractor_map is None:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_names = list(distractor_map.values())

    options = [row["school_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which school did {year} Heisman Trophy winner {row['player_name']} play for?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"heisman:{row['player_name']}:{year}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAYER"

    shuffled_options, correct_index = serializer.finalize_options(rng, row["school_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != row["school_name"]:
        return "INVALID_CORRECT_INDEX"

    # No puzzle_catalog row exists for this domain (same real gap
    # lineup.py's difficulty section already documents) -- same disclosed
    # recency heuristic, not a claim of empirical validation.
    diff_score = (MAX_YEAR - year) / (MAX_YEAR - MIN_YEAR)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{row['player_name']} won the {year} Heisman Trophy while playing for {row['school_name']}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "award_year": year, "player_name": row["player_name"],
            "school_id": row["school_id"], "correct_answer_text": row["school_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band,
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real Heisman Trophy winners on record; exported the maximum "
        f"available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    years = [q["_audit"]["award_year"] for q in exported]
    schools = sorted(set(q["_audit"]["school_id"] for q in exported))
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_year": min(years) if years else None,
        "max_year": max(years) if years else None,
        "unique_schools": len(schools),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_heisman.py -- CFB Heisman Winners.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Award year/player:** {a['award_year']}, {a['player_name']}",
        f"- **School:** `{a['school_id']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `cfb_award_facts`, verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`",
    ]
