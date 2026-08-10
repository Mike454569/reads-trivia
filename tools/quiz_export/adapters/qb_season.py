"""QB/Season domain adapter -- Passing Records & QB Trivia.

Reproduces tools/export_quiz_engine_qb_pilot.py's exact logic and exact
per-candidate check order. No Game Factory predicate exists for this
domain, so candidates come from a direct, deterministically-shuffled query
against qb_team_seasons. Difficulty is cross-referenced from Engine's own
pre-existing qb_season puzzle_catalog mode rather than invented.

JS header text preserved verbatim from the original script -- see
draft.py's module docstring for why.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise, teams_active_in_season  # byte-identical across all three originals

OUT_PATH = engine.DATA_DIR / "quiz-engine-qb-pilot.js"
SEED = "reads-quiz-engine-qb-pilot-v1"
TARGET_COUNT = 100
ID_START = 300000
CATEGORY = "Passing Records & QB Trivia"
GLOBAL_NAME = "QUIZ_DATA_ENGINE_QB_PILOT"
REQUIRED_SOURCE = "NFLVERSE_DATA"
TRACK_ENTITY = True

IDENTITY_INCONSISTENT_QB_IDS = {
    "00-0017200", "00-0033869", "00-0034577", "00-0035228",
    "00-0035289", "00-0036355", "00-0039917",
}


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(c, "qb_team_seasons", REQUIRED_SOURCE)


def fetch_ordered_candidates(c, seed: str):
    all_rows = c.execute(
        "SELECT season, team_code, qb_source_id, qb_name, starts_observed, "
        "verification_status, source_id FROM qb_team_seasons "
        "ORDER BY qb_source_id, season, team_code"
    ).fetchall()
    rng_order = engine.seeded(seed)
    all_rows = list(all_rows)
    rng_order.shuffle(all_rows)
    return all_rows


def evaluate(c, row, rng, guard):
    if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
        return "ROW_NOT_VERIFIED"

    qb_id = row["qb_source_id"]

    if qb_id in IDENTITY_INCONSISTENT_QB_IDS:
        return "UNRESOLVED_QB_IDENTITY"

    season = row["season"]
    if (qb_id, season) in _multi_team_pairs(c):
        return "MULTIPLE_PLAUSIBLE_ANSWERS_MIDSEASON_TRADE"

    if guard.entity_seen(qb_id):
        return "DUPLICATE_PLAYER"

    correct, err = resolve_franchise(c, row["team_code"], season)
    if err:
        return err

    diff_info = difficulty_mod.difficulty_from_puzzle_catalog(
        c, "qb_season", qb_id, season, REQUIRED_SOURCE
    )
    if not diff_info:
        return "NO_ENGINE_DIFFICULTY_AVAILABLE"

    pool = teams_active_in_season(c, season)
    pool.pop(correct["franchise_id"], None)
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[fid] for fid in distractor_ids]

    options = [correct["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which NFL team did {row['qb_name']} play for in the {season} season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct["full_name"]:
        return "INVALID_CORRECT_INDEX"

    band = diff_info["difficulty_band"]
    if band not in difficulty_mod.DIFFICULTY_MAP:
        return "UNKNOWN_DIFFICULTY_BAND"
    diff_label = difficulty_mod.map_band(band)

    starts = row["starts_observed"]
    notes = f"{row['qb_name']} made {starts} start{'s' if starts != 1 else ''} for the {correct['full_name']} in {season}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "entity_key": qb_id,
            "qb_source_id": qb_id, "qb_name": row["qb_name"], "team_code": row["team_code"],
            "season": season, "starts_observed": starts,
            "franchise_id": correct["franchise_id"], "correct_answer_text": correct["full_name"],
            "difficulty_score": diff_info["difficulty_score"], "difficulty_band": band,
            "verification_status": row["verification_status"], "source_id": row["source_id"],
        },
    }


_multi_team_cache: dict = {}


def _multi_team_pairs(c):
    """Computed once per process and cached (pure function of unchanging
    Engine data, not per-call state) -- matches the original script's
    single up-front computation before its main loop."""
    if "pairs" not in _multi_team_cache:
        _multi_team_cache["pairs"] = {
            (r["qb_source_id"], r["season"])
            for r in c.execute(
                "SELECT qb_source_id, season FROM qb_team_seasons "
                "GROUP BY qb_source_id, season HAVING COUNT(DISTINCT team_code) > 1"
            )
        }
    return _multi_team_cache["pairs"]


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count}-row qb_team_seasons table; exported the maximum available "
        f"({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    seasons = [q["_audit"]["season"] for q in exported]
    franchises = sorted(set(q["_audit"]["franchise_id"] for q in exported))
    dup_players = [p for p, n in Counter(q["_audit"]["qb_source_id"] for q in exported).items() if n > 1]
    return {
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_franchises": len(franchises),
        "unique_qbs": len(set(q["_audit"]["qb_source_id"] for q in exported)),
        "dup_players": dup_players,
        "identity_inconsistent_qb_ids_excluded": sorted(IDENTITY_INCONSISTENT_QB_IDS),
        "multi_team_season_pairs_excluded": len(_multi_team_cache.get("pairs", [])),
    }


def header_lines(seed: str) -> list[str]:
    # Verbatim text from the original script -- see draft.py's module docstring.
    return [
        "// AUTO-GENERATED PILOT FILE -- do not hand-edit.",
        "// Produced by tools/export_quiz_engine_qb_pilot.py from Reads Football Data",
        "// Engine v4.0 (qb_team_seasons + team_aliases, direct query -- Game Factory has",
        "// no built-in QB/season predicate). Pilot Domain #2, independent of the Draft",
        "// Pilot exporters (tools/export_quiz_engine_pilot.py / _v2.py).",
        f"// Deterministic seed: \"{seed}\". Rerunning the exporter against an",
        "// unchanged database reproduces this file byte-for-byte.",
        "//",
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or",
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_QB_PILOT, distinct",
        "// from window.QUIZ_DATA and both Draft Pilot globals, so it cannot collide",
        "// with any of them even if loaded by mistake.",
        "//",
        "// See QUIZ_ENGINE_QB_PILOT_REPORT.md for the full audit trail.",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **QB:** {a['qb_name']} (GSIS id `{a['qb_source_id']}`)",
        f"- **Season:** {a['season']}",
        f"- **Team/context:** raw team code `{a['team_code']}`, resolved franchise `{a['franchise_id']}` "
        f"(\"{record['options'][record['correctIndex']]}\"), {a['starts_observed']} start(s) observed that season",
        f"- **Engine source/domain:** `qb_team_seasons` row, verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`; difficulty cross-referenced from Engine's pre-existing `qb_season` "
        f"`puzzle_catalog` mode",
    ]
