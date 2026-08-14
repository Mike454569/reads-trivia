"""NFL Super Bowl History domain adapter.

Built on `nfl_championship_events` (tools/data_refresh/nfl_wikipedia_history_
import.py) -- 60 real Super Bowl games (SB I-LX, 1966-2025 seasons),
imported from Wikipedia as a secondary structured source since this
database's primary NFLVERSE_DATA-backed championship signal
(season_standings.playoff_result, the existing NFL_CHAMPIONSHIP/
TEAM_POSTSEASON_RESULT capability) only covers 2002+ and asks a different
question (how did team X finish its season) rather than the Super Bowl
GAME itself (who beat whom).

Real, disclosed limit: team identity resolution for the winner/loser of
each game uses `team_aliases`, which only covers seasons 2002+ (the same
real, pre-existing limit every other team-guessing adapter in this codebase
inherits from that table). 24 of the 60 real Super Bowls (2002-2025
seasons) resolve to real franchises and are playable here; the other 36
(1966-2001 seasons) are rejected honestly as TEAM_UNRESOLVED, same
rejection reason nfl_game_result.py already uses for the identical
underlying limitation -- never guessed at, never silently dropped without
being counted.
"""
from __future__ import annotations

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise, teams_active_in_season

OUT_PATH = None  # Director-pipeline-only, like cfb_heisman and player_from_clues
CATEGORY = "NFL Super Bowl History"
REQUIRED_SOURCE_ID = "WIKIPEDIA_STRUCTURED"
REQUIRED_VERIFICATION_STATUS = "WIKIPEDIA_STRUCTURED_SECONDARY"
TRACK_ENTITY = True  # one question per real Super Bowl event

MIN_SEASON = 2002  # matches team_aliases' real coverage start -- see module docstring
MAX_SEASON = 2025  # the most recent season with a resolved Super Bowl as of this import


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "nfl_championship_events", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT event_id, sb_number, season, game_date, winner_team_code, loser_team_code, "
        "winner_score, loser_score, overtime, venue, city, source_id, verification_status "
        "FROM nfl_championship_events ORDER BY season"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if not row["winner_team_code"] or not row["loser_team_code"]:
        return "TEAM_UNRESOLVED"

    season = row["season"]
    winner, err = resolve_franchise(c, row["winner_team_code"], season)
    if err:
        return "TEAM_UNRESOLVED"
    loser, err = resolve_franchise(c, row["loser_team_code"], season)
    if err:
        return "TEAM_UNRESOLVED"

    active = teams_active_in_season(c, season)
    pool = {fid: name for fid, name in active.items()
            if fid not in (winner["franchise_id"], loser["franchise_id"])}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(list(pool.values()), 3)

    options = [winner["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which team won Super Bowl {row['sb_number']}, played following the {season} NFL season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"sb_champion:{row['event_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_EVENT"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner["full_name"]:
        return "INVALID_CORRECT_INDEX"

    # No puzzle_catalog row exists for this domain -- same real, disclosed
    # gap every other adapter without one documents; a recency heuristic,
    # not a claim of empirical validation.
    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    ot_note = " in overtime" if row["overtime"] else ""
    notes = (
        f"The {winner['full_name']} beat the {loser['full_name']} "
        f"{row['winner_score']}-{row['loser_score']}{ot_note} in Super Bowl {row['sb_number']} "
        f"({season} NFL season)."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "event_id": row["event_id"], "sb_number": row["sb_number"], "season": season,
            "winner_franchise_id": winner["franchise_id"], "loser_franchise_id": loser["franchise_id"],
            "correct_answer_text": winner["full_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band,
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real Super Bowl games on record; exported the maximum available "
        f"({accepted_count}) rather than loosen any rule to reach {target_count}. Most rejections "
        f"are pre-2002 games -- team_aliases (the table every team-guessing adapter in this "
        f"codebase resolves franchises through) doesn't cover seasons before 2002."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    franchises = sorted(set(q["_audit"]["winner_franchise_id"] for q in exported))
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_champion_franchises": len(franchises),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_super_bowl.py -- NFL Super Bowl History.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Super Bowl/season:** {a['sb_number']}, {a['season']} season",
        f"- **Winner:** `{a['winner_franchise_id']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `nfl_championship_events`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
