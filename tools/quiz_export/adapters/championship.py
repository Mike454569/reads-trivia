"""Championship/Postseason domain adapter -- Playoffs & Postseason Moments.

Reproduces tools/export_quiz_engine_championship_award_pilot.py's exact
logic and exact per-candidate check order. No Game Factory predicate
exists for this domain. Distractors come from a closed 5-value outcome
vocabulary (not a team_aliases query), and this domain deliberately does
not enforce unique-entity-per-export -- each (team, season) pair is already
unique by primary key and independently represents a distinct fact.

JS header text preserved verbatim from the original script -- see
draft.py's module docstring for why.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise  # byte-identical across all three originals

OUT_PATH = engine.DATA_DIR / "quiz-engine-championship-award-pilot.js"
SEED = "reads-quiz-engine-championship-award-pilot-v1"
TARGET_COUNT = 100
ID_START = 400000
CATEGORY = "Playoffs & Postseason Moments"
GLOBAL_NAME = "QUIZ_DATA_ENGINE_CHAMPIONSHIP_AWARD_PILOT"
REQUIRED_SOURCE = "NFLVERSE_DATA"
TRACK_ENTITY = False  # deliberate -- see module docstring

OUTCOME_LABELS = {
    "WonSB": "Won the Super Bowl",
    "LostSB": "Lost the Super Bowl",
    "LostCC": "Lost in the Conference Championship",
    "LostDV": "Lost in the Divisional Round",
    "LostWC": "Lost in the Wild Card Round",
}


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(
        c, "season_standings", REQUIRED_SOURCE, where_extra="playoff_result IS NOT NULL"
    )


def fetch_ordered_candidates(c, seed: str):
    all_rows = c.execute(
        "SELECT season, team_code, wins, losses, ties, playoff_result, "
        "verification_status, source_id FROM season_standings "
        "WHERE playoff_result IS NOT NULL ORDER BY season, team_code"
    ).fetchall()
    rng_order = engine.seeded(seed)
    all_rows = list(all_rows)
    rng_order.shuffle(all_rows)
    return all_rows


def evaluate(c, row, rng, guard):
    if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
        return "ROW_NOT_VERIFIED"

    outcome = row["playoff_result"]
    if outcome not in OUTCOME_LABELS:
        return "UNKNOWN_OUTCOME_LABEL"

    season = row["season"]
    franchise, err = resolve_franchise(c, row["team_code"], season)
    if err:
        return err

    diff_info = difficulty_mod.difficulty_from_puzzle_catalog(
        c, "playoff_result", row["team_code"], season, REQUIRED_SOURCE, expected_answer=outcome
    )
    if not diff_info:
        return "NO_ENGINE_DIFFICULTY_AVAILABLE"

    correct_label = OUTCOME_LABELS[outcome]
    other_labels = [lab for code, lab in OUTCOME_LABELS.items() if code != outcome]
    distractor_labels = rng.sample(other_labels, 3)

    options = [correct_label] + distractor_labels
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"How did the {franchise['full_name']} finish the {season} NFL season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_label, distractor_labels)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_label:
        return "INVALID_CORRECT_INDEX"

    band = diff_info["difficulty_band"]
    if band not in difficulty_mod.DIFFICULTY_MAP:
        return "UNKNOWN_DIFFICULTY_BAND"
    diff_label = difficulty_mod.map_band(band)

    wins, losses, ties = row["wins"], row["losses"], row["ties"]
    if wins is None or losses is None:
        return "MISSING_RECORD"
    record_str = f"{wins}-{losses}" + (f"-{ties}" if ties else "")
    notes = f"The {franchise['full_name']} went {record_str} in {season} and {correct_label[0].lower()}{correct_label[1:]}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "team_code": row["team_code"], "season": season, "record": record_str,
            "playoff_result": outcome, "franchise_id": franchise["franchise_id"],
            "correct_answer_text": correct_label,
            "difficulty_score": diff_info["difficulty_score"], "difficulty_band": band,
            "verification_status": row["verification_status"], "source_id": row["source_id"],
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count}-row season_standings playoff pool; exported the maximum available "
        f"({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_outcome = Counter(q["_audit"]["playoff_result"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    franchises = sorted(set(q["_audit"]["franchise_id"] for q in exported))
    dup_team_seasons = [
        ts for ts, n in Counter((q["_audit"]["team_code"], q["_audit"]["season"]) for q in exported).items() if n > 1
    ]
    return {
        "outcome_distribution": dict(by_outcome),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_franchises": len(franchises),
        "dup_team_seasons": [list(x) for x in dup_team_seasons],
    }


def header_lines(seed: str) -> list[str]:
    # Verbatim text from the original script -- see draft.py's module docstring.
    return [
        "// AUTO-GENERATED PILOT FILE -- do not hand-edit.",
        "// Produced by tools/export_quiz_engine_championship_award_pilot.py from Reads",
        "// Football Data Engine v4.0 (season_standings.playoff_result, direct query --",
        "// Game Factory has no championship/award predicate). Pilot Domain #3,",
        "// independent of the Draft and QB Pilot exporters.",
        f"// Deterministic seed: \"{seed}\". Rerunning the exporter against an",
        "// unchanged database reproduces this file byte-for-byte.",
        "//",
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or",
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_CHAMPIONSHIP_AWARD_PILOT,",
        "// distinct from window.QUIZ_DATA and every other pilot global, so it cannot",
        "// collide with any of them even if loaded by mistake.",
        "//",
        "// See QUIZ_ENGINE_CHAMPIONSHIP_AWARD_PILOT_REPORT.md for the full audit trail.",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Season/year:** {a['season']}",
        f"- **Team/context:** raw team code `{a['team_code']}`, resolved franchise `{a['franchise_id']}` "
        f"(\"{record['options'][record['correctIndex']]}\" for {a['season']}), regular-season record "
        f"{a['record']}, raw outcome code `{a['playoff_result']}`",
        f"- **Engine source/domain:** `season_standings` row, verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`; difficulty cross-referenced from Engine's pre-existing `playoff_result` "
        f"`puzzle_catalog` mode",
    ]
