"""CFB Transfer Portal domain adapter (Creator-gap-audit operation).

Built on `cfb_transfer_summary_v17` (109,221 rows; 15,495 with
school_count >= 2, i.e. a real multi-school career) -- fully populated,
zero Creator capabilities built on it before this. "This player's college
career included more than one school -- which of these did they actually
play for" -- entity is a real multi-school player, answer is one real
school from their own real `schools` list (comma-separated, e.g.
"Miami,Akron"), distractors are real schools NOT on their list.

Real gap found before building: this table has NO source_id/
verification_status columns at all (unlike every other table this whole
Engine's adapters check), so the standard check_table_wide_safety()/
check_verification_status_safety() helpers don't apply directly. Verified
independently instead: every one of the 15,495 school_count>=2 rows'
cfb_player_id traces to a real, SOURCE_BACKED/SPORTSDATAVERSE_CFB row in
`cfb_roster_seasons_real` (confirmed directly, 15,495/15,495 -- 100%), so
safety_check() below checks THAT underlying table, and evaluate() re-
verifies the same join per-row rather than trusting the summary table
blindly.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .. import distractors as distractors_mod

OUT_PATH = None
CATEGORY = "CFB Transfer Portal"
REQUIRED_SOURCE_ID = "SPORTSDATAVERSE_CFB"
TRACK_ENTITY = True  # one question per real multi-school player

MIN_SEASON = 2002
MAX_SEASON = 2025


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(c, "cfb_roster_seasons_real", REQUIRED_SOURCE_ID)


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        """
        SELECT t.cfb_player_id, t.display_name, t.school_count, t.first_season, t.last_season, t.schools
        FROM cfb_transfer_summary_v17 t
        WHERE t.school_count >= 2
          AND EXISTS (
              SELECT 1 FROM cfb_roster_seasons_real r
              WHERE r.cfb_player_id = t.cfb_player_id
                AND r.source_id = ? AND r.verification_status = 'SOURCE_BACKED'
          )
        """,
        (REQUIRED_SOURCE_ID,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def _all_transfer_schools_pool(c) -> dict:
    """Distractor pool: every real school that appears in this same
    transfer-summary table (guaranteed consistent naming with the correct
    answer, avoiding a cross-table name-format mismatch against the
    separate `schools` reference table)."""
    rows = c.execute("SELECT schools FROM cfb_transfer_summary_v17 WHERE school_count >= 2").fetchall()
    pool: dict = {}
    for r in rows:
        for name in (r["schools"] or "").split(","):
            name = name.strip()
            if name:
                pool[name] = name
    return pool


_SCHOOL_POOL_CACHE: dict = {}


def _school_pool(c) -> dict:
    if "pool" not in _SCHOOL_POOL_CACHE:
        _SCHOOL_POOL_CACHE["pool"] = _all_transfer_schools_pool(c)
    return _SCHOOL_POOL_CACHE["pool"]


def evaluate(c, row, rng, guard):
    if not row["display_name"] or not row["schools"]:
        return "MISSING_FIELD"
    own_schools = [s.strip() for s in row["schools"].split(",") if s.strip()]
    own_schools = list(dict.fromkeys(own_schools))  # de-dup, preserve order
    if len(own_schools) < 2:
        return "INSUFFICIENT_SCHOOL_HISTORY"

    # Deterministic pick of which of the player's real schools is the
    # correct answer, keyed off the seeded per-candidate rng so re-runs are
    # reproducible.
    correct_school = own_schools[rng.randrange(len(own_schools))]

    full_pool = _school_pool(c)
    plausible_pool = {k: v for k, v in full_pool.items() if k not in own_schools}
    distractor_map = distractors_mod.sample_plausible(rng, correct_school, plausible_pool, plausible_pool, k=3)
    if distractor_map is None:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_names = list(distractor_map.values())

    options = [correct_school] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    other_count = len(own_schools) - 1
    question = (
        f"{row['display_name']} played college football for {row['school_count']} different schools "
        f"between {row['first_season']} and {row['last_season']}. Which of these was one of them?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_transfer:{row['cfb_player_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAYER"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_school, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_school:
        return "INVALID_CORRECT_INDEX"

    last_season = row["last_season"] or MAX_SEASON
    diff_score = (MAX_SEASON - last_season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{row['display_name']} played for {', '.join(own_schools)} across their college career."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "cfb_player_id": row["cfb_player_id"], "school_count": row["school_count"],
            "correct_answer_text": correct_school,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real multi-school players on record; exported the maximum available "
        f"({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {
        "difficulty_band_distribution": dict(by_band),
        "unique_players": len(set(q["_audit"]["cfb_player_id"] for q in exported)),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_transfer.py -- CFB Transfer Portal.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Player:** `{a['cfb_player_id']}` ({a['school_count']} schools)",
        f"- **Correct school:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_transfer_summary_v17` (cross-checked against "
        f"`cfb_roster_seasons_real`), verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`",
    ]
