"""NFL Season Awards domain adapter.

Built on `nfl_season_awards` (tools/data_refresh/nfl_wikipedia_history_
import.py) -- AP MVP/Offensive Player of the Year/Defensive Player of the
Year/Offensive Rookie of the Year/Defensive Rookie of the Year, plus Super
Bowl MVP, imported from Wikipedia as a secondary structured source (this
database had no NFL individual-award data of any kind before that import --
only CFB's Heisman Trophy, see cfb_heisman.py). Each awarding body is kept
distinct (never a combined generic "NFL MVP") per the explicit import
requirement -- see that module's own docstring.

Real, disclosed limit: player identity resolution against canonical_players
splits cleanly at roughly the 2000 season, not because of match-quality --
canonical_players is itself NFLVERSE-sourced and its own real identity
coverage does not reliably reach earlier than that (confirmed directly:
canonical_players.birth_date bottoms out at 1960; legends like Jim Brown
and Johnny Unitas have no canonical_players row at all yet). 238 of 369
real award-winner rows resolve to a real player_id and are playable here;
the rest are rejected honestly as PLAYER_UNRESOLVED, never guessed at.

Distractor pool is deliberately narrow -- other real NFL award winners,
never the full ~17,000-row canonical_players universe. That wider pool was
tried for cfb_heisman.py's schools and produced obviously-wrong distractors
a real fan would never mistake for plausible (see distractors.py's module
docstring for the exact incident); an award-winner guessing game has the
identical failure mode with random non-award-winning players, so this
adapter never falls back past the award-winner pool -- if fewer than 3
other real winners remain, the candidate is rejected outright rather than
padded with an implausible name.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .. import distractors as distractors_mod

OUT_PATH = None  # Director-pipeline-only, like cfb_heisman and nfl_super_bowl
CATEGORY = "NFL Season Awards"
REQUIRED_SOURCE_ID = "WIKIPEDIA_STRUCTURED"
REQUIRED_VERIFICATION_STATUS = "WIKIPEDIA_STRUCTURED_SECONDARY"
TRACK_ENTITY = True  # one question per real award instance

AWARD_LABELS = {
    "AP_MVP": "AP NFL Most Valuable Player Award",
    "AP_OPOY": "AP NFL Offensive Player of the Year Award",
    "AP_DPOY": "AP NFL Defensive Player of the Year Award",
    "AP_OROY": "AP NFL Offensive Rookie of the Year Award",
    "AP_DROY": "AP NFL Defensive Rookie of the Year Award",
    "SB_MVP": "Super Bowl MVP Award",
}

MIN_SEASON = 1957  # earliest real resolved award season on record (AP OROY, Jim Brown -- unresolved, but
                    # kept as the honest domain floor; see min_year handling below)
MAX_SEASON = 2025


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "nfl_season_awards", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT award_id, award_type, season, player_id, source_id, verification_status "
        "FROM nfl_season_awards ORDER BY season"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def _all_resolved_award_winners(c) -> dict:
    """The plausible-distractor pool: every real player who has won one of
    these six real award types -- 238 distinct award instances across a
    real, curated set of players. A wrong option drawn from this pool is
    always a real NFL award winner, never a random name. See module
    docstring for why this is never widened to all canonical_players."""
    rows = c.execute(
        "SELECT DISTINCT a.player_id, cp.display_name FROM nfl_season_awards a "
        "JOIN canonical_players cp ON cp.player_id = a.player_id "
        "WHERE a.player_id IS NOT NULL"
    ).fetchall()
    return {r["player_id"]: r["display_name"] for r in rows}


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if not row["player_id"]:
        return "PLAYER_UNRESOLVED"

    award_label = AWARD_LABELS.get(row["award_type"])
    if not award_label:
        return "UNKNOWN_AWARD_TYPE"

    player_row = c.execute(
        "SELECT display_name FROM canonical_players WHERE player_id=?", (row["player_id"],)
    ).fetchone()
    if not player_row:
        return "PLAYER_UNRESOLVED"
    correct_name = player_row["display_name"]

    winners_pool = _all_resolved_award_winners(c)
    distractor_map = distractors_mod.sample_plausible(rng, row["player_id"], winners_pool, winners_pool, k=3)
    if distractor_map is None:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_names = list(distractor_map.values())

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    season = row["season"]
    if row["award_type"] == "SB_MVP":
        question = f"Which player won Super Bowl MVP following the {season} NFL season?"
    else:
        question = f"Which player won the {award_label} for the {season} NFL season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"award:{row['award_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_AWARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    # No puzzle_catalog row exists for this domain -- same real, disclosed
    # gap every other adapter without one documents; a recency heuristic,
    # not a claim of empirical validation.
    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(max(0.0, min(1.0, diff_score)))
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_name} won the {award_label} ({season} NFL season)."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "award_id": row["award_id"], "award_type": row["award_type"], "season": season,
            "player_id": row["player_id"], "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band,
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real award instances on record; exported the maximum available "
        f"({accepted_count}) rather than loosen any rule to reach {target_count}. Most rejections "
        f"are PLAYER_UNRESOLVED -- canonical_players' own real identity coverage does not "
        f"reliably reach earlier than roughly the 2000 season."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_award = Counter(q["_audit"]["award_type"] for q in exported)
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    return {
        "award_type_distribution": dict(by_award),
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_season_awards.py -- NFL Season Awards.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Award/season:** {a['award_type']}, {a['season']} season",
        f"- **Winner:** `{a['player_id']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `nfl_season_awards`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
