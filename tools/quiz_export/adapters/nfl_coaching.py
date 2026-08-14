"""NFL Coaching domain adapter (Creator-gap-audit operation).

Built on `coach_team_seasons` (936 rows, 1999-2026, real coach-per-team-
per-season records) -- fully populated, zero Creator capabilities built on
it before this. "Which team did [coach] coach in [season]" -- entity is a
(coach, season) pair, answer is the real team, resolved through the same
team_aliases/resolve_franchise() machinery every other team-guessing
adapter in this codebase already uses (so a historical relocation/rename
is handled identically here, not reinvented).

Real check done before building: 43 (team, season) pairs have two coach
rows (real in-season coaching changes -- an interim coach case, not a data
bug), but ZERO (coach, season) pairs map to more than one team -- confirmed
directly by query. That's the only direction this capability's identity
resolution actually depends on (coach+season -> team, never team+season ->
coach), so it's genuinely safe to build on without excluding anything for
that reason.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise, teams_active_in_season

OUT_PATH = None
CATEGORY = "NFL Coaching History"
REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
TRACK_ENTITY = True  # one question per real (coach, season) record

MIN_SEASON = 1999
MAX_SEASON = 2026


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(c, "coach_team_seasons", REQUIRED_SOURCE_ID)


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT season, team_code, coach_id, coach_name, games_observed, source_id, verification_status "
        "FROM coach_team_seasons ORDER BY season, coach_id"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != "SOURCE_BACKED":
        return "ROW_NOT_VERIFIED"
    if not row["coach_name"] or not row["team_code"]:
        return "MISSING_FIELD"
    # A coach must have actually been observed on the sideline for a real
    # number of games that season -- a 0/near-zero games_observed row would
    # be a stub/placeholder, not a real coaching tenure fact.
    if not row["games_observed"] or row["games_observed"] < 1:
        return "INSUFFICIENT_GAMES_OBSERVED"

    season = row["season"]
    franchise, err = resolve_franchise(c, row["team_code"], season)
    if err:
        return err

    active = teams_active_in_season(c, season)
    pool = {fid: name for fid, name in active.items() if fid != franchise["franchise_id"]}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(list(pool.values()), 3)

    options = [franchise["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which NFL team did {row['coach_name']} coach in the {season} season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_coach:{row['coach_id']}:{season}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_COACH_SEASON"

    shuffled_options, correct_index = serializer.finalize_options(rng, franchise["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != franchise["full_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{row['coach_name']} coached the {franchise['full_name']} in {season} ({row['games_observed']} games observed)."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "coach_id": row["coach_id"], "team_code": row["team_code"],
            "franchise_id": franchise["franchise_id"], "correct_answer_text": franchise["full_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real (coach, season) records on file ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    coaches = sorted(set(q["_audit"]["coach_id"] for q in exported))
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_coaches": len(coaches),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_coaching.py -- NFL Coaching History.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Coach/season:** `{a['coach_id']}`, {a['season']}",
        f"- **Team:** `{a['franchise_id']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `coach_team_seasons`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
