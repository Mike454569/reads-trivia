"""NFL First Touchdown Scorer domain adapter (Creator Capability Completion
pass). Answers the real manual-failure prompt directly: "who scored the
first touchdown" -- a GAME -> PLAYER relationship, never downgraded to
GAME -> WINNER (that's the pre-existing, genuinely different WON_GAME
capability).

Built on `nfl_plays` (1,279,628 rows, SOURCE_BACKED/NFLVERSE_DATA,
1999-2025) -- the same real, resolved `receiver_player_key`/
`rusher_player_key` fields, joined to `canonical_players` for a real
display name (never a name join -- both keys are PFR-style ids, joined on
id). Real resolution measured directly before building: 19,317/21,041
pass touchdowns (91.8%) and 11,135/12,240 rush touchdowns (91.0%) resolve
a real scorer identity; unresolved plays are excluded, never guessed at.

Entity is the FIRST touchdown play of a real game (MIN(play_id) among that
game's touchdown=1 rows) -- matching the exact real question asked
("who scored THE FIRST touchdown"), not just any touchdown in the game.
`play_desc` (the source's own raw text play-by-play description) is NEVER
shown to the player -- it contains the scorer's name directly (e.g.
"14-S.Howell scrambles... TOUCHDOWN"), which would leak the answer; this
adapter builds its own clean question text instead.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise

OUT_PATH = None
CATEGORY = "NFL First Touchdown Scorer"
REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
TRACK_ENTITY = True
MIN_SEASON = 1999
MAX_SEASON = 2025

# Real, measured N+1 fix (Creator Capability Completion pass): evaluate()'s
# distractor pool query is a CASE-expression JOIN across the full 1.28M-row
# nfl_plays table -- real, but far too expensive to re-run once per
# candidate (measured: a single Tier-2 certification pass took ~600s before
# this fix, well past the real 45s admin generation timeout, meaning this
# capability was certifiable but functionally unusable in production). Same
# fix as _defensive_event_common.py: cache per (min_season, max_season)
# window for the duration of one generation call only -- reset at the top
# of fetch_ordered_candidates() (called exactly once per real request), so
# a later data refresh is never masked by a stale cache.
_pool_cache: dict[tuple, list[str]] = {}

# Same real, already-established safeguard as compiler.py's own
# RelationshipSpec.max_fetched_candidates -- nfl_plays is large (1,279,628
# rows); capping the per-call evaluate() workload here too, on top of the
# pool-cache fix above.
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(c, "nfl_plays", REQUIRED_SOURCE_ID)


def fetch_ordered_candidates(c, seed: str):
    _pool_cache.clear()
    # One row per real game: the first touchdown play (min play_id among
    # touchdown=1 rows), with whichever of receiver/rusher key applies.
    rows = c.execute(
        """
        SELECT p.game_id, p.season, p.posteam, p.defteam, p.play_id,
               p.pass_touchdown, p.rush_touchdown, p.receiver_player_key, p.rusher_player_key,
               p.source_id, p.verification_status
        FROM nfl_plays p
        JOIN (
            SELECT game_id, MIN(play_id) AS first_td_play_id
            FROM nfl_plays WHERE touchdown = 1
            GROUP BY game_id
        ) first_td ON first_td.game_id = p.game_id AND first_td.first_td_play_id = p.play_id
        WHERE p.touchdown = 1
        ORDER BY p.game_id
        """
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"

    if row["pass_touchdown"]:
        scorer_key, td_type = row["receiver_player_key"], "receiving"
    elif row["rush_touchdown"]:
        scorer_key, td_type = row["rusher_player_key"], "rushing"
    else:
        return "UNSUPPORTED_TOUCHDOWN_TYPE"  # e.g. a defensive/special-teams TD -- no offensive scorer key to use

    if not scorer_key:
        return "UNRESOLVED_SCORER_KEY"
    scorer_row = c.execute("SELECT display_name FROM canonical_players WHERE player_id=?", (scorer_key,)).fetchone()
    if not scorer_row or not scorer_row["display_name"]:
        return "UNRESOLVED_SCORER_IDENTITY"
    scorer_name = scorer_row["display_name"]

    season = row["season"]
    franchise_off, err = resolve_franchise(c, row["posteam"], season)
    franchise_def, err2 = resolve_franchise(c, row["defteam"], season)
    if err or err2 or not franchise_off or not franchise_def:
        return "TEAM_UNRESOLVED"

    window = (max(season - 3, MIN_SEASON), min(season + 3, MAX_SEASON))
    cached_pool = _pool_cache.get(window)
    if cached_pool is None:
        pool_rows = c.execute(
            "SELECT DISTINCT cp.display_name FROM nfl_plays p "
            "JOIN canonical_players cp ON cp.player_id = "
            "  (CASE WHEN p.pass_touchdown=1 THEN p.receiver_player_key ELSE p.rusher_player_key END) "
            "WHERE p.touchdown=1 AND p.season BETWEEN ? AND ?",
            window,
        ).fetchall()
        cached_pool = [r["display_name"] for r in pool_rows]
        _pool_cache[window] = cached_pool
    pool = [n for n in cached_pool if n != scorer_name]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [scorer_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = (
        f"In the {season} NFL game between the {franchise_off['full_name']} and the "
        f"{franchise_def['full_name']}, who scored the first touchdown?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_first_td:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, scorer_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != scorer_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{scorer_name} scored the first touchdown of this game on a {td_type} play."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "game_id": row["game_id"], "play_id": row["play_id"], "td_type": td_type,
            "correct_answer_text": scorer_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real games with a resolved first touchdown ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    by_type = Counter(q["_audit"]["td_type"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band), "td_type_distribution": dict(by_type)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_first_touchdown.py -- NFL First Touchdown Scorer.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}`, {a['season']}, play `{a['play_id']}` ({a['td_type']})",
        f"- **Scorer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `nfl_plays`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
