"""NFL Hall of Fame domain adapter (Creator Semantic Routing + Who Am I pass).

Built on `nfl_hof_inductees` (387 rows, WIKIPEDIA_STRUCTURED_SECONDARY,
class years 1963-2026). "Which player was inducted into the Pro Football
Hall of Fame in [class year]" -- entity is one real player inductee row,
answer is the real inductee name as recorded by the source.

Scoped to `is_player=1` (336 of 387 rows) -- the other 51 rows are
non-player inductees (coaches, contributors, executives), a genuinely
different real question this capability does not ask (a player was never
claimed to be "inducted for playing" when the record is actually a coach).

Same "no player_id resolution required" discipline as nfl_all_pro.py/
nfl_pro_bowl.py -- inductee_name_raw is the real, source-verified answer
text (only 107 of 387 rows resolve a player_id at all).
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "NFL Hall of Fame"
REQUIRED_SOURCE_ID = "WIKIPEDIA_STRUCTURED"
REQUIRED_VERIFICATION_STATUS = "WIKIPEDIA_STRUCTURED_SECONDARY"
TRACK_ENTITY = True

MIN_CLASS_YEAR = 1963
MAX_CLASS_YEAR = 2026


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "nfl_hof_inductees", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra="is_player = 1",
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT hof_id, class_year, position_raw, inductee_name_raw, source_id, verification_status "
        "FROM nfl_hof_inductees WHERE is_player = 1 ORDER BY class_year, hof_id"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if not row["inductee_name_raw"]:
        return "MISSING_FIELD"

    correct_name = row["inductee_name_raw"]
    pool_rows = c.execute(
        "SELECT DISTINCT inductee_name_raw FROM nfl_hof_inductees "
        "WHERE is_player = 1 AND inductee_name_raw != ?",
        (correct_name,),
    ).fetchall()
    pool = [r["inductee_name_raw"] for r in pool_rows]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    class_year = row["class_year"]
    position_phrase = f" ({row['position_raw']})" if row["position_raw"] else ""
    question = f"Which player{position_phrase} was inducted into the Pro Football Hall of Fame's Class of {class_year}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_hof:{row['hof_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_INDUCTEE"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_CLASS_YEAR - class_year) / max(MAX_CLASS_YEAR - MIN_CLASS_YEAR, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_name} was inducted into the Pro Football Hall of Fame's Class of {class_year}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "class_year": class_year, "hof_id": row["hof_id"], "position_raw": row["position_raw"],
            "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real player Hall of Fame inductee records on file "
        f"({MIN_CLASS_YEAR}-{MAX_CLASS_YEAR}); exported the maximum available ({accepted_count}) "
        f"rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    years = [q["_audit"]["class_year"] for q in exported]
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_class_year": min(years) if years else None,
        "max_class_year": max(years) if years else None,
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_hof.py -- NFL Hall of Fame.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Inductee:** `{a['hof_id']}`, Class of {a['class_year']}",
        f"- **Position:** {a['position_raw'] or '(none recorded)'}",
        f"- **Underlying Engine source:** `nfl_hof_inductees`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
