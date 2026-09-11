"""CFB 2026 Head Coach domain adapter -- Power 4 Coverage Closeout workbook.

Real universe: `cfb_team_2026_coaching_profile` (67 rows, one per real
2026 Power 4 team, sourced from tools/data_refresh/
cfb_2026_coach_scheme_workbook_import.py -- see that module's own
docstring for why this lives in a new table rather than
cfb_coach_school_links). Genuinely new season-level knowledge: the Engine
has no other real source for a 2026 CFB head coach (cfb_coach_school_links
has no season column at all; coach_team_seasons' real 2026 rows are 100%
NFLVERSE_DATA -- confirmed directly before building this).

Question shape: "Which team does [real 2026 head coach] coach?" -- always
a single, unambiguous real answer (one head coach per team), distractors
sampled from the other 66 real 2026 head coaches' real teams.
"""
from __future__ import annotations

from .. import safety, serializer

CATEGORY = "CFB 2026 Head Coach"
REQUIRED_SOURCE_ID = "READS_POWER4_CLOSEOUT_2026_09_09"
TRACK_ENTITY = True


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(c, "cfb_team_2026_coaching_profile", REQUIRED_SOURCE_ID)


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        """SELECT p.school_id, s.school_name, p.head_coach_name
           FROM cfb_team_2026_coaching_profile p JOIN schools s ON s.school_id = p.school_id
           WHERE p.source_id=? AND p.head_coach_name IS NOT NULL""",
        (REQUIRED_SOURCE_ID,),
    ).fetchall()
    rows = list(rows)
    from .. import engine
    rng_order = engine.seeded(seed)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if not row["head_coach_name"] or not row["school_name"]:
        return "MISSING_REQUIRED_FIELD"
    entity_key = f"cfb2026coach:{row['school_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"

    pool = c.execute(
        """SELECT s.school_name FROM cfb_team_2026_coaching_profile p JOIN schools s ON s.school_id = p.school_id
           WHERE p.source_id=? AND p.head_coach_name IS NOT NULL AND p.school_id != ?""",
        (REQUIRED_SOURCE_ID, row["school_id"]),
    ).fetchall()
    other_teams = [r["school_name"] for r in pool]
    if len(other_teams) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_teams = list(rng.sample(other_teams, 3))

    question = f"Which team does {row['head_coach_name']} coach in 2026?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    correct = row["school_name"]
    shuffled_options, correct_index = serializer.finalize_options(rng, correct, distractor_teams)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct:
        return "INVALID_CORRECT_INDEX"

    return {
        "category": CATEGORY, "difficulty": "Medium", "question": question,
        "options": shuffled_options, "correctIndex": correct_index,
        "notes": f"{row['head_coach_name']} is {correct}'s real 2026 head coach, per Ourlads' current "
                 f"team depth-chart page.",
        "_audit": {
            "entity_key": entity_key, "school_id": row["school_id"],
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCE_ID,
            "difficulty_band": "medium",
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of {considered_count} real 2026 head-coach candidates passed every "
        f"validation rule; exported the maximum available ({accepted_count}) rather than loosen any rule "
        f"to reach {target_count}."
    )


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_2026_head_coach.py -- CFB 2026 Head Coach.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Team:** `{a['school_id']}`, real 2026 head coach",
        f"- **Correct answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_team_2026_coaching_profile`, source_id `{a['source_id']}`",
    ]
