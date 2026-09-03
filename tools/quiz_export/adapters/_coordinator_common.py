"""Shared candidate-fetch/evaluate logic for nfl_coordinators-based "which
team's OC/DC" capabilities -- same extraction discipline as
_boxscore_stat_common.py (see that module's docstring): two near-identical
adapters (offense/defense) differing only in which `role` value they
filter to and how the question is worded, not two genuinely different real
logics.

Built on `nfl_coordinators` -- 2026-only (WIKIPEDIA_STRUCTURED_SECONDARY,
current-season snapshot) UNTIL the Gold Standard Modes + Creator Quality
follow-up pass's `nfl_coordinators_historical_import.py` backfill, which
extends the SAME table/UNIQUE(season,team_code,role) constraint with real
2000-2025 rows (source_id still 'WIKIPEDIA_STRUCTURED', a real per-team-
season Wikipedia page scrape -- see that module's own docstring for exact
real coverage/gaps). "Which team did [coach] coordinate the offense/
defense for in a real NFL season" -- entity is one real (team, season,
role) coordinator row, answer is the real team name (or coach name,
TEAM_TO_COACH direction) -- season now read from the row itself, never a
hardcoded constant, so this genuinely answers whatever real season the row
is for, never silently substituting 2026 data for a different-season ask.

season_min/season_max filters (Gold Standard Modes + Creator Quality
follow-up pass) let a caller scope to an exact requested season (e.g. "the
2014 offensive coordinator" -> season_min=season_max=2014) or a real range
("coordinators from the 2000s" -> 2000-2009); default is every real season
on file.
"""
from __future__ import annotations

from .. import engine, difficulty as difficulty_mod, serializer

REQUIRED_SOURCE_ID = "WIKIPEDIA_STRUCTURED"
REQUIRED_VERIFICATION_STATUS = "WIKIPEDIA_STRUCTURED_SECONDARY"
SUPPORTS_FILTERS = True


def safety_check(c, *, role: str) -> dict:
    from .. import safety
    return safety.check_verification_status_safety(
        c, "nfl_coordinators", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra=f"role = '{role}'",
    )


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None, *, role: str):
    filters = filters or {}
    season_min = filters.get("season_min")
    season_max = filters.get("season_max")
    query = (
        "SELECT coordinator_id, season, team_name_raw, team_franchise_id, coach_name_raw, "
        "role, source_id, verification_status FROM nfl_coordinators WHERE role = ?"
    )
    params: list = [role]
    if season_min is not None:
        query += " AND season >= ?"
        params.append(int(season_min))
    if season_max is not None:
        query += " AND season <= ?"
        params.append(int(season_max))
    query += " ORDER BY coordinator_id"
    rows = c.execute(query, params).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard, *, role: str, side_label: str, category: str, entity_prefix: str,
             direction: str = "COACH_TO_TEAM"):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if row["role"] != role:
        return "ROW_WRONG_ROLE"
    if not row["coach_name_raw"] or not row["team_name_raw"] or not row["team_franchise_id"]:
        return "MISSING_FIELD"

    # Universal Data Reuse pass: a real, precisely-found direction bug --
    # the ONLY variant that existed asked "which team did [coach] coordinate
    # for", the reverse of what a request phrased as "give me a team and
    # season, guess the coordinator" (team is the GIVEN fact, coordinator
    # name is the answer) actually wants. Same real nfl_coordinators row,
    # same real data either way -- just swapping which field is embedded in
    # the question text vs which is the answer/options pool. Kept as one
    # shared function (not a copy-pasted second evaluate()) since every
    # other line -- safety, provenance, difficulty, audit fields -- is
    # identical regardless of direction.
    season = row["season"]
    # Distractors scoped to the SAME real season -- a more thematically
    # coherent, comparable-era pool than any season on file (real, low-risk
    # improvement made alongside the multi-season expansion below: with
    # only 2026 on file there was only ever one season to draw from
    # anyway, so this changes nothing about existing behavior).
    if direction == "TEAM_TO_COACH":
        correct_answer = row["coach_name_raw"]
        pool_rows = c.execute(
            "SELECT DISTINCT coach_name_raw FROM nfl_coordinators WHERE role = ? AND season = ? AND coach_name_raw != ?",
            (role, season, correct_answer),
        ).fetchall()
        pool = [r["coach_name_raw"] for r in pool_rows]
        if len(pool) < 3:
            return "INSUFFICIENT_DISTRACTOR_POOL"
        distractor_names = rng.sample(pool, 3)
        options = [correct_answer] + distractor_names
        if len(set(options)) != 4:
            return "DUPLICATE_OPTIONS"
        question = f"Who was the real {season} {row['team_name_raw']} {side_label.lower()} coordinator?"
        entity_key = f"{entity_prefix}_rev:{row['coordinator_id']}"
        notes = f"{correct_answer} was the {season} {row['team_name_raw']} {side_label.lower()} coordinator."
    else:
        correct_answer = row["team_name_raw"]
        pool_rows = c.execute(
            "SELECT DISTINCT team_name_raw FROM nfl_coordinators WHERE role = ? AND season = ? AND team_name_raw != ?",
            (role, season, correct_answer),
        ).fetchall()
        pool = [r["team_name_raw"] for r in pool_rows]
        if len(pool) < 3:
            return "INSUFFICIENT_DISTRACTOR_POOL"
        distractor_names = rng.sample(pool, 3)
        options = [correct_answer] + distractor_names
        if len(set(options)) != 4:
            return "DUPLICATE_OPTIONS"
        question = f"Which real NFL team did {row['coach_name_raw']} serve as {side_label} coordinator for in the {season} season?"
        entity_key = f"{entity_prefix}:{row['coordinator_id']}"
        notes = f"{row['coach_name_raw']} was the {season} {correct_answer} {side_label.lower()} coordinator."

    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_COORDINATOR"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_answer, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_answer:
        return "INVALID_CORRECT_INDEX"

    # A single real season has no real recency axis -- fixed Medium, same
    # discipline cfb_rivalry.py already uses for its own single-snapshot,
    # no-season-variety domain (requesting easy/hard correctly yields zero
    # results rather than mislabel a question).
    band = "MEDIUM"
    diff_label = difficulty_mod.map_band(band)

    return {
        "category": category, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": row["season"], "coordinator_id": row["coordinator_id"], "role": role,
            "team_franchise_id": row["team_franchise_id"], "correct_answer_text": correct_answer,
            "difficulty_score": 0.5, "difficulty_band": band, "entity_key": entity_key,
            "direction": direction,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, side_label: str) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real {side_label.lower()} coordinator records on file (real per-season "
        f"scrape coverage varies -- some seasons/teams have no resolvable real Wikipedia coordinator "
        f"data, never fabricated); exported the maximum available ({accepted_count}) rather than loosen "
        f"any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    seasons = sorted({q["_audit"]["season"] for q in exported})
    return {
        "seasons_covered": seasons,
        "unique_teams": len(set(q["_audit"]["team_franchise_id"] for q in exported)),
    }


def human_review_context(record: dict, *, table_name: str) -> list[str]:
    a = record["_audit"]
    answer_label = "Coordinator" if a.get("direction") == "TEAM_TO_COACH" else "Team"
    return [
        f"- **Coordinator record:** `{a['coordinator_id']}`, {a['season']}, {a['role']}",
        f"- **Team:** `{a['team_franchise_id']}`",
        f"- **{answer_label} (the real answer):** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `{table_name}`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
