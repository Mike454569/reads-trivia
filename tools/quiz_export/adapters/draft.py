"""Draft domain adapter -- NFL Draft History.

Reproduces tools/export_quiz_engine_pilot_v2.py's exact logic and exact
per-candidate check order (required for byte-identical RNG behavior -- see
QUIZ_EXPORT_FRAMEWORK_REFACTOR_PLAN.md). This is the only domain of the
three with a Game Factory predicate (DRAFTED_BY), so candidate generation
delegates to game_factory.generate_candidates() rather than a direct query.

The JS header text below is preserved verbatim from the original script,
including its self-reference to that filename -- changing it would change
the output file's bytes, which the refactor's byte-identical requirement
does not allow. See the refactor plan and
QUIZ_EXPORT_FRAMEWORK_REFACTOR_VERIFICATION.md (written after this adapter
is verified) for that tradeoff made explicit.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = engine.DATA_DIR / "quiz-engine-pilot-v2.js"
SEED = "reads-quiz-engine-pilot-v1"
TARGET_COUNT = 100
CANDIDATE_LIMIT = 500
ID_START = 200000
CATEGORY = "NFL Draft History"
GLOBAL_NAME = "QUIZ_DATA_ENGINE_PILOT_V2"
REQUIRED_DOMAIN = "NFL_DRAFT"
REQUIRED_SOURCE = "NFLVERSE_DATA"
TRACK_ENTITY = True

_SPEC = {
    "description": "which team drafted this nfl player",
    "competition_id": "NFL", "mechanic": "guess",
    "entity_type": "nfl_player", "relationship_predicate": "DRAFTED_BY",
    "object_type": "team", "answer_type": "team", "group_size": 4, "filters": {},
}


def resolve_franchise(c, team_code: str, season: int):
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE team_code=? AND ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (team_code, season, season),
    ).fetchall()
    if len(rows) == 0:
        return None, "TEAM_UNRESOLVED"
    if len(rows) > 1:
        return None, "TEAM_AMBIGUOUS"
    return {"franchise_id": rows[0]["franchise_id"], "full_name": rows[0]["full_name"]}, None


def teams_active_in_season(c, season: int) -> dict:
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (season, season),
    ).fetchall()
    return {r["franchise_id"]: r["full_name"] for r in rows}


def safety_check(c) -> dict:
    return safety.check_domain_coverage_safety(c, REQUIRED_DOMAIN)


# Lineup Concurrency pass: real root cause of the reproduced NFL_DRAFT-call
# slowness, found via cProfile (same technique lineup.py's own fix docstring
# describes), not assumed -- `_SPEC` here is a fixed module-level constant,
# never varying call to call, yet `engine.gf.feasibility(_SPEC)` (a real,
# ~1200-execute()-call, multi-second-on-a-cold-cache read against
# `game_factory_legacy.py`'s vendored feasibility()) was being recomputed
# from scratch on EVERY single fetch_ordered_candidates() call purely to
# gate a SystemExit sanity check whose answer cannot change within one
# process's lifetime (it depends only on the Engine DB's schema/table
# presence, never on `seed` or any other per-call input). Identical bug
# shape to the one already fixed in lineup.py's certified_college_lookup()
# -- cached here the same way, in project code, never touching the vendored
# Engine's own feasibility()/generate_candidates() functions. This was
# never a concurrency/isolation bug -- draft.py's own admin/shared executor
# was always correctly isolated from the lineup-isolated one -- it was
# every NFL_DRAFT generation call independently paying real, avoidable
# per-call DB cost that a fixed, unbounded GENERATION_TIMEOUT-sensitive
# caller (like a starvation test, or a real user's first request) could hit.
_FEASIBILITY_CACHE: dict = {}


def fetch_ordered_candidates(c, seed: str):
    feas = _FEASIBILITY_CACHE.get("result")
    if feas is None:
        feas = engine.gf.feasibility(_SPEC)
        _FEASIBILITY_CACHE["result"] = feas
    if feas["status"] != "SUPPORTED":
        raise SystemExit(f"ABORT: Engine feasibility() returned {feas['status']}, not SUPPORTED.")
    rows, _feas2 = engine.gf.generate_candidates(_SPEC, limit=CANDIDATE_LIMIT, seed=seed)
    return rows


def evaluate(c, raw, rng, guard):
    payload, diff, amb, sources = raw

    issues = engine.gf.qa_candidate(payload)
    if any(i["severity"] == "ERROR" for i in issues):
        return f"ENGINE_QA_{issues[0]['issue_type']}"

    entity_id = payload["entity"]["id"]
    if guard.entity_seen(entity_id):
        return "DUPLICATE_PLAYER"

    row = c.execute(
        "SELECT draft_team,draft_season,player_name,verification_status,source_id "
        "FROM draft_facts WHERE player_key=?",
        (entity_id,),
    ).fetchone()
    if not row:
        return "ROW_NOT_FOUND"
    if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
        return "ROW_NOT_VERIFIED"
    if row["draft_team"] != payload["answer_id"]:
        return "ANSWER_MISMATCH"

    season = row["draft_season"]
    if season is None:
        return "MISSING_SEASON"

    correct, err = resolve_franchise(c, row["draft_team"], season)
    if err:
        return err

    pool = teams_active_in_season(c, season)
    pool.pop(correct["franchise_id"], None)
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[fid] for fid in distractor_ids]

    options = [correct["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which NFL team drafted {row['player_name']}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct["full_name"], distractor_names)

    band = engine.band(diff)
    diff_label = difficulty_mod.map_band(band)

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": "",
        "_audit": {
            "entity_key": entity_id,
            "player_key": entity_id, "player_name": row["player_name"],
            "draft_team_code": row["draft_team"], "draft_season": season,
            "franchise_id": correct["franchise_id"], "correct_answer_text": correct["full_name"],
            "difficulty_score": round(diff, 4), "difficulty_band": band,
            "source_table": sources[0] if sources else None,
            "verification_status": row["verification_status"], "source_id": row["source_id"],
            "engine_qa_issues": issues,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule within a "
        f"{CANDIDATE_LIMIT}-candidate deterministic sample; exported the maximum "
        f"available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    seasons = [q["_audit"]["draft_season"] for q in exported]
    franchises = sorted(set(q["_audit"]["franchise_id"] for q in exported))
    dup_players = [p for p, n in Counter(q["_audit"]["player_key"] for q in exported).items() if n > 1]
    feas = engine.gf.feasibility(_SPEC)
    return {
        "candidate_limit": CANDIDATE_LIMIT,
        "feasibility": {
            "status": feas.get("status"), "estimated_candidates": feas.get("estimated_candidates"),
            "reason": feas.get("reason"), "source_table": feas.get("source_table"),
        },
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_franchises": len(franchises),
        "unique_players": len(set(q["_audit"]["player_key"] for q in exported)),
        "dup_players": dup_players,
    }


def header_lines(seed: str) -> list[str]:
    # Verbatim text from the original script -- see module docstring.
    return [
        "// AUTO-GENERATED PILOT V2 FILE -- do not hand-edit.",
        "// Produced by tools/export_quiz_engine_pilot_v2.py from Reads Football Data",
        "// Engine v4.0 (game_factory.py, DRAFTED_BY predicate, guess mechanic), after",
        "// the 30 SAFE_FIX_AVAILABLE team_aliases corrections in",
        "// TEAM_ALIAS_SAFE_FIX_CHANGELOG.md were applied.",
        f"// Deterministic seed: \"{seed}\". Rerunning the exporter against an",
        "// unchanged database reproduces this file byte-for-byte.",
        "//",
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or",
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_PILOT_V2, a",
        "// distinct global from window.QUIZ_DATA and window.QUIZ_DATA_ENGINE_PILOT",
        "// (Pilot v1), so it cannot collide with either even if loaded by mistake.",
        "//",
        "// See QUIZ_ENGINE_PILOT_V2_REPORT.md for the full v1-vs-v2 audit trail.",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Draft year / source context:** {a['player_name']} was drafted in the **{a['draft_season']}** "
        f"NFL Draft by team code `{a['draft_team_code']}`, resolved to franchise `{a['franchise_id']}` "
        f"via Engine's `team_aliases` table (season-matched).",
        f"- **Underlying Engine source:** `draft_facts` row, player_key `{a['player_key']}`, "
        f"verification_status `{a['verification_status']}`, source_id `{a['source_id']}` "
        f"(domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` "
        f"(source table reported by Engine: `{a['source_table']}`).",
    ]
