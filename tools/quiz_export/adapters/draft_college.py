"""NFL Draft College domain adapter -- "guess the college an NFL player
attended" (Creator/Feasibility stale-college-data fix).

--- WHY THIS EXISTS ---
Before this adapter, a general "guess the college of an NFL player" request
had no registered capability at all, so it fell through to
`tools/director_v02/feasibility.py`'s generic `KNOWN_MISSING_DATA_SIGNALS`
"college" entry -- a HARDCODED string citing `cfb_nfl_identity_bridge_
certified`'s 2,542-row count (now stale; that bridge has since grown, see
`lineup_college.py`). That fallback was written when this database genuinely
had no usable general-purpose player<->college data. That stopped being true
the moment `draft_facts.college` / `nfl_players_draft.college` were backfilled
(a real gap-check pass: the `draft_picks.csv` source used by
`tools/data_refresh/nfl_draft_refresh.py` has always had a `college` column
that was never mapped -- added additively, backfilled on the existing
(season, pick) key, 12,914 of 12,927 existing draft rows got a real college;
the other 13 have none in the source). This adapter is what makes that data
real, generatable content instead of an unused column.

--- WHY THIS IS A SEPARATE CAPABILITY FROM THE LINEUP-COLLEGE ONE ---
`lineup_college.py` (NFL_OFFENSE_LINEUP_COLLEGE) answers a narrower,
harder question: "which TEAM started these 5 skill-position players (shown
by college, names hidden) in a specific SEASON" -- it requires
SEASON-SPECIFIC starting-lineup membership on top of a college fact, sourced
from `cfb_nfl_identity_bridge_certified` (a cross-referenced NFL-roster/CFB-
participation bridge with position corroboration). This adapter answers a
simpler, broader question -- "which COLLEGE did this specific drafted PLAYER
attend" -- sourced directly from the draft record itself, with no season-
lineup-membership requirement at all. The two capabilities are NOT
interchangeable and this one does not shrink or replace the other's
disclosed limitations.

--- WHY THIS DATA IS SAFE TO BUILD ON (audited before writing this file) ---
Every one of the 12,914 college-populated `draft_facts` rows carries a
single, uniform (verification_status, source_id) pair -- SOURCE_BACKED /
NFLVERSE_DATA, confirmed directly (`GROUP BY verification_status, source_id`
returns exactly one row). Zero duplicate player_key rows. 428 distinct real
college names, every one of which produced at least one actual NFL draft
pick -- structurally, this is already a football-relevant distractor
universe (unlike `cfb_heisman.py`'s original all-805-schools pool, which
included real but Heisman-irrelevant D-III programs), so no separate
"plausible subset" curation is needed the way Heisman's distractor fix
required.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .. import distractors as distractors_mod

OUT_PATH = None  # Director-pipeline-only, like player_from_clues/lineup/cfb_heisman
CATEGORY = "NFL Draft — College"
REQUIRED_DOMAIN = "NFL_DRAFT"
REQUIRED_SOURCE = "NFLVERSE_DATA"
TRACK_ENTITY = True  # one question per real drafted player

# Real, measured range this capability spans (draft_facts rows with a
# non-null college) -- see live_college_coverage() for the always-fresh,
# never-hardcoded version feasibility.py's reason text actually reports.
MIN_ROUND = 1
MAX_ROUND_FOR_DIFFICULTY = 7  # round 7+ treated as max difficulty; matches the
                               # modern 7-round draft even though some pre-1994
                               # drafts ran longer (12 rounds seen in this data)


def safety_check(c) -> dict:
    return safety.check_domain_coverage_safety(c, REQUIRED_DOMAIN)


def live_college_coverage(c) -> dict:
    """Real, live-measured coverage for this exact capability -- the number
    `feasibility.py` reports for a general college request, computed fresh
    every call, never a hardcoded/documented figure that can go stale the
    way the original 2,542-citation did."""
    total = c.execute(
        "SELECT COUNT(*) FROM draft_facts WHERE verification_status='SOURCE_BACKED' AND source_id=?",
        (REQUIRED_SOURCE,),
    ).fetchone()[0]
    with_college = c.execute(
        "SELECT COUNT(*) FROM draft_facts WHERE verification_status='SOURCE_BACKED' AND source_id=? "
        "AND college IS NOT NULL AND college != ''",
        (REQUIRED_SOURCE,),
    ).fetchone()[0]
    unique_players = c.execute(
        "SELECT COUNT(DISTINCT player_key) FROM draft_facts WHERE verification_status='SOURCE_BACKED' "
        "AND source_id=? AND college IS NOT NULL AND college != ''",
        (REQUIRED_SOURCE,),
    ).fetchone()[0]
    unique_colleges = c.execute(
        "SELECT COUNT(DISTINCT college) FROM draft_facts WHERE verification_status='SOURCE_BACKED' "
        "AND source_id=? AND college IS NOT NULL AND college != ''",
        (REQUIRED_SOURCE,),
    ).fetchone()[0]
    season_range = c.execute(
        "SELECT MIN(draft_season) mn, MAX(draft_season) mx FROM draft_facts WHERE verification_status='SOURCE_BACKED' "
        "AND source_id=? AND college IS NOT NULL AND college != ''",
        (REQUIRED_SOURCE,),
    ).fetchone()
    return {
        "table": "draft_facts", "source_id": REQUIRED_SOURCE,
        "total_draft_rows": total, "rows_with_college": with_college,
        "unique_players_with_college": unique_players, "unique_colleges": unique_colleges,
        "min_season": season_range["mn"], "max_season": season_range["mx"],
    }


def _all_colleges(c) -> dict:
    rows = c.execute(
        "SELECT DISTINCT college FROM draft_facts WHERE verification_status='SOURCE_BACKED' AND source_id=? "
        "AND college IS NOT NULL AND college != ''",
        (REQUIRED_SOURCE,),
    ).fetchall()
    return {r["college"]: r["college"] for r in rows}


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_round, college FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id=? AND college IS NOT NULL AND college != '' "
        "ORDER BY draft_season, draft_pick_overall",
        (REQUIRED_SOURCE,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    entity_key = row["player_key"]
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAYER"
    if not row["college"]:
        return "MISSING_COLLEGE"

    full_colleges = _all_colleges(c)
    # The full college pool IS the plausible pool here (module docstring) --
    # every entry already produced a real NFL draft pick, so there is no
    # "obviously wrong" tier the way Heisman's unfiltered 805-school pool had.
    distractor_map = distractors_mod.sample_plausible(rng, row["college"], full_colleges, full_colleges, k=3)
    if distractor_map is None:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_names = list(distractor_map.values())

    options = [row["college"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    round_ord = row["draft_round"]
    round_text = f"round {round_ord}" if round_ord else "the draft"
    question = f"Which college did {row['player_name']} attend before being drafted in {round_text} of the {row['draft_season']} NFL Draft?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, row["college"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != row["college"]:
        return "INVALID_CORRECT_INDEX"

    # Disclosed heuristic (not empirically validated, same discipline as
    # cfb_heisman.py's recency heuristic): earlier draft rounds correspond to
    # more well-known players/colleges, so difficulty scales with round.
    round_for_score = round_ord if round_ord else MAX_ROUND_FOR_DIFFICULTY
    diff_score = min(round_for_score - 1, MAX_ROUND_FOR_DIFFICULTY - 1) / (MAX_ROUND_FOR_DIFFICULTY - 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{row['player_name']} attended {row['college']} before being selected in round {round_ord} of the {row['draft_season']} NFL Draft."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "player_key": row["player_key"], "player_name": row["player_name"],
            "draft_season": row["draft_season"], "draft_round": round_ord,
            "correct_answer_text": row["college"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band,
            "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCE,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real drafted players with a known college on record; exported the maximum "
        f"available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["draft_season"] for q in exported]
    colleges = sorted(set(q["_audit"]["correct_answer_text"] for q in exported))
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_colleges": len(colleges),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/draft_college.py -- NFL Draft College.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Player/season/round:** {a['player_name']}, {a['draft_season']} draft, round {a['draft_round']}",
        f"- **College:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `draft_facts.college`, verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`",
    ]
