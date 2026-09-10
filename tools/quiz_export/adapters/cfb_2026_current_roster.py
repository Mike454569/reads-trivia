"""CFB 2026 Current Roster domain adapter -- MASTER WORKBOOK ingestion pass.

--- WHY THIS IS A NEW CAPABILITY, NOT A DUPLICATE ---
Every existing CFB roster-driven adapter in this directory
(cfb_offense_lineup.py, cfb_player_season_school.py,
director_v04/cfb_player_from_clues.py) requires a FINISHED season's
accumulated stats or a multi-season career history to work -- none of
them can use a bare current-roster snapshot for a season that hasn't been
played yet. The 2026 CFB season has no season-total stats and no
finished-season completeness signal (`cfb_school_seasons` doesn't have a
2026 row yet), so none of those adapters can reach it. This adapter is
the first one built specifically for "who is on this real 2026 roster
right now" -- reusing the existing `guess` mechanic and
`DEFAULT_MULTIPLE_CHOICE` format exactly as-is (see the format registry's
own compatibility matrix), not inventing either.

Real universe: `cfb_roster_seasons_real` rows where
`source_id='READS_MASTER_KNOWLEDGE_FEED_2026_09'` -- the rows
`tools/data_refresh/cfb_2026_roster_workbook_import.py` published from the
user's MASTER Knowledge Feed workbook (official team-athletics-site
sourced, Tier 1, for 8 real 2026 rosters: Alabama, Auburn, Georgia Tech,
Kansas, Oregon, Texas, UCLA, USC). Deliberately excludes the automated
SPORTSDATAVERSE_CFB rows in the same table (no 2026 season exists there
at all yet) -- this is the one real source for this one real season.

Question shape: reveal a real player's position, class year, and (when
present) hometown, then ask which of this workbook's 8 real 2026 rosters
he's actually on -- the "Silhouette Reveal" concept from the workbook's
own GAME_IDEAS_2026_EXPANSION sheet, built on the `guess` mechanic instead
of a new one since a player's team is always a single, unambiguous
answer (unlike jersey number, which real rosters legitimately duplicate
within a team -- verified directly: 196 duplicate (team, jersey) pairs
across these same 8 rosters, so jersey number is used here only as a
non-identifying clue, never as the thing being asked about).
"""
from __future__ import annotations

from .. import safety, serializer

CATEGORY = "CFB 2026 Current Roster"
REQUIRED_SOURCE_ID = "READS_MASTER_KNOWLEDGE_FEED_2026_09"
SEASON = 2026
TRACK_ENTITY = True

_CLASS_YEAR_LABEL = {
    "1": "freshman", "2": "sophomore", "3": "junior", "4": "senior",
    "5": "fifth-year", "6": "sixth-year",
}


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(
        c, "cfb_roster_seasons_real", REQUIRED_SOURCE_ID, where_extra=f"season={SEASON}",
    )


def _team_pool(c) -> list[dict]:
    rows = c.execute(
        "SELECT DISTINCT r.school_id, s.school_name FROM cfb_roster_seasons_real r "
        "JOIN schools s ON s.school_id = r.school_id "
        "WHERE r.season=? AND r.source_id=?",
        (SEASON, REQUIRED_SOURCE_ID),
    ).fetchall()
    return [{"school_id": row["school_id"], "school_name": row["school_name"]} for row in rows]


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        """SELECT r.school_id, r.cfb_player_id, r.position, r.class_year, r.jersey_number,
           p.display_name, p.hometown_city, p.hometown_state
           FROM cfb_roster_seasons_real r
           JOIN canonical_cfb_players p ON p.cfb_player_id = r.cfb_player_id
           WHERE r.season=? AND r.source_id=?""",
        (SEASON, REQUIRED_SOURCE_ID),
    ).fetchall()
    rows = list(rows)
    from .. import engine
    rng_order = engine.seeded(seed)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if not row["display_name"] or not row["position"]:
        return "MISSING_REQUIRED_FIELD"
    entity_key = f"cfb2026roster:{row['cfb_player_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"

    pool = _team_pool(c)
    correct = next((t["school_name"] for t in pool if t["school_id"] == row["school_id"]), None)
    if not correct:
        return "UNMAPPED_SCHOOL"
    other_teams = [t["school_name"] for t in pool if t["school_id"] != row["school_id"]]
    if len(other_teams) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_teams = list(rng.sample(other_teams, 3))

    class_label = _CLASS_YEAR_LABEL.get(str(row["class_year"]))
    clue_parts = []
    if class_label:
        clue_parts.append(f"a {class_label} {row['position']}")
    else:
        clue_parts.append(f"a {row['position']}")
    if row["hometown_city"] and row["hometown_state"]:
        clue_parts.append(f"from {row['hometown_city']}, {row['hometown_state']}")
    question = f"This player is {' '.join(clue_parts)} on a real 2026 roster. Which team is he on?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct, distractor_teams)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct:
        return "INVALID_CORRECT_INDEX"

    jersey_note = f" He wears #{row['jersey_number']}." if row["jersey_number"] is not None else ""
    return {
        "category": CATEGORY, "difficulty": "Medium", "question": question,
        "options": shuffled_options, "correctIndex": correct_index,
        "notes": f"{row['display_name']} is on {correct}'s real 2026 roster, per the school's own official "
                 f"athletics site.{jersey_note}",
        "_audit": {
            "entity_key": entity_key, "cfb_player_id": row["cfb_player_id"], "school_id": row["school_id"],
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCE_ID,
            "difficulty_band": "medium",
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of {considered_count} real 2026-roster candidates passed every validation "
        f"rule; exported the maximum available ({accepted_count}) rather than loosen any rule to reach "
        f"{target_count}."
    )


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_2026_current_roster.py -- CFB 2026 Current Roster.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Player:** `{a['cfb_player_id']}`, real 2026 roster row, school `{a['school_id']}`",
        f"- **Correct answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_roster_seasons_real`, source_id `{a['source_id']}`",
    ]
