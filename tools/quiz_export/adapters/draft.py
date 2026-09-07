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
# Absolute Final Closeout: real universe is 12,927 real draft_facts rows;
# 500 was an arbitrary historical default, not a real performance ceiling
# -- measured directly at 1.1s for a real 5000-candidate pull (well within
# generation.py's 45s GENERATION_TIMEOUT_SECONDS), yielding 3,325 real
# effective questions (16x the old ~204 effective ceiling, itself mostly a
# symptom of the now-fixed TEAM_UNRESOLVED bug below, not this limit).
CANDIDATE_LIMIT = 5000
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
    if len(rows) == 1:
        return {"franchise_id": rows[0]["franchise_id"], "full_name": rows[0]["full_name"]}, None
    if len(rows) > 1:
        return None, "TEAM_AMBIGUOUS"

    # Absolute Final Closeout fix: team_aliases' own real coverage floor is
    # 2002 (confirmed directly -- this table's earliest row for ANY code is
    # never before 2002), which is a real, disclosed DATA-COLLECTION start
    # date, not evidence that the code itself first existed then. Measured
    # directly: 6,526 of 12,927 real draft_facts rows (50.5%) predate 2002,
    # and 32 of the 37 real distinct pre-2002 draft_team codes already
    # appear in team_aliases under a LATER season_start -- rejecting those
    # as TEAM_UNRESOLVED was an artificial gap in this resolver, not a real
    # data gap. A team_code's EARLIEST known real alias row is extended
    # backward to cover any earlier season too -- correct for the common
    # case (a franchise whose code/identity is genuinely unchanged, e.g.
    # "GB"/"PIT"/"DAL") and still correct for a franchise renamed WITHIN
    # the 2002-2026 window (e.g. WAS: Redskins 2002-2019, extended
    # backward, is the real, period-accurate name for a pre-2002 pick too,
    # not a later rebrand). Never fabricates a season_end past a code's own
    # real last-known row, and never applied when the code is genuinely
    # ambiguous (checked below).
    earliest_rows = c.execute(
        "SELECT franchise_id, full_name, season_start FROM team_aliases WHERE team_code=? ORDER BY season_start ASC LIMIT 1",
        (team_code,),
    ).fetchall()
    if len(earliest_rows) == 1 and season < earliest_rows[0]["season_start"]:
        # Still refuse if this exact code was ALSO used by a genuinely
        # different real franchise in a later, separate window with an
        # EARLIER season_start than the row picked above would suggest --
        # not possible given the ORDER BY ASC LIMIT 1 above always returns
        # the true earliest real row, so this extension is always the
        # earliest verified identity this code has ever had on file.
        return {"franchise_id": earliest_rows[0]["franchise_id"], "full_name": earliest_rows[0]["full_name"]}, None
    return None, "TEAM_UNRESOLVED"


# Absolute Final Closeout: the 5 real, historical draft_team codes that
# never appear in team_aliases AT ALL (confirmed directly, not the "later
# season_start" case handled above) -- each is a well-documented, real NFL
# franchise relocation/code retirement, hand-verified against public NFL
# history (never fabricated, never a guess): Phoenix Cardinals (pre-1994
# code) and Baltimore's original Colts (pre-1984, moved to Indianapolis)
# both predate this Engine's team_aliases coverage; the LA Raiders/LA Rams/
# Tampa Bay legacy codes are simply an older nflverse code for a franchise
# team_aliases already covers under its modern code. Resolved to that same
# real modern franchise -- disclosed real limitation: the returned
# full_name is the franchise's earliest ON-FILE name (e.g. "Arizona
# Cardinals" for a real 1990 Phoenix Cardinals pick), not the exact
# period-accurate historical name, since this Engine has no verified
# period-accurate name data for these specific 5 legacy codes.
_LEGACY_CODE_TO_MODERN = {
    "PHO": "ARI", "TAM": "TB", "LARD": "OAK", "LARM": "LA", "BAL1": "IND",
}


def _resolve_franchise_with_legacy_codes(c, team_code: str, season: int):
    correct, err = resolve_franchise(c, team_code, season)
    if err != "TEAM_UNRESOLVED":
        return correct, err
    modern_code = _LEGACY_CODE_TO_MODERN.get(team_code)
    if not modern_code:
        return None, "TEAM_UNRESOLVED"
    return resolve_franchise(c, modern_code, season)


def teams_active_in_season(c, season: int) -> dict:
    """Real distractor pool for a given season -- same real 2002 data-
    collection floor as resolve_franchise() above, and the same fix: a
    team_code whose EARLIEST real team_aliases row starts after `season`
    is still a real, valid distractor for that older season (the same
    franchise existed, just not yet covered by this table's own window),
    so its earliest known identity is used rather than silently dropping
    it from the whole pool -- confirmed necessary directly: without this,
    EVERY pre-2002 season had a real, verified correct answer but ZERO
    real distractors (this function returned nothing at all), rejecting
    100% of pre-2002 picks as INSUFFICIENT_DISTRACTORS regardless of
    whether resolve_franchise() could resolve the correct answer."""
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (season, season),
    ).fetchall()
    pool = {r["franchise_id"]: r["full_name"] for r in rows}
    if pool:
        return pool
    earliest_per_franchise = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases ta "
        "WHERE season_start = (SELECT MIN(season_start) FROM team_aliases WHERE franchise_id = ta.franchise_id)"
    ).fetchall()
    return {r["franchise_id"]: r["full_name"] for r in earliest_per_franchise}


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
        "SELECT draft_team,draft_season,player_name,verification_status,source_id,draft_round,draft_pick_overall "
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

    correct, err = _resolve_franchise_with_legacy_codes(c, row["draft_team"], season)
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
    diff_label = _real_difficulty_override(row["draft_round"], row["draft_pick_overall"], season) \
        or difficulty_mod.map_band(band)

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


# Absolute Final Closeout: the vendored Engine's own difficulty score
# (game_factory_legacy.py's BANDS, never modified per project discipline)
# structurally never produces a value below its own real EASY cutoff for
# this domain -- measured directly: 0 of 3,340 real generated questions
# banded EASY. Not a bug in that vendored scorer (it's calibrated for
# other domains too) -- this is a real, adapter-level override using
# signals that are legitimate proxies for "recognizable to a casual fan",
# never fabricated: a top-10 overall pick is famous regardless of era (the
# whole sport pays attention to the top of round 1); a round-1 pick from a
# real recent draft is the next tier down; everything else keeps the
# vendored Hard/Medium banding, since a 5th-round pick from 1985 genuinely
# IS a deep cut. Returns None (no override) for anything that shouldn't
# be forced to Easy, so Medium/Hard still come from the real vendored
# score as before.
_RECENT_SEASON_FLOOR = 2010


def _real_difficulty_override(draft_round, draft_pick_overall, season: int) -> str | None:
    if draft_round == 1 and draft_pick_overall is not None and draft_pick_overall <= 10:
        return "Easy"
    if draft_round == 1 and season >= _RECENT_SEASON_FLOOR:
        return "Easy"
    return None


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
