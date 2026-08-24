"""CFB Rivalry Trivia domain adapter -- Rivalry Data + Gold Standard Content
Integration operation.

--- WHY THIS ADAPTER LOOKS DIFFERENT FROM EVERY OTHER ADAPTER IN THIS DIR ---
Every other `guess`-mechanic adapter DERIVES a question + 3 distractors from
a real fact row (a Heisman winner's school, a lineup's starting colleges,
etc.). This domain's source data is different in kind: a curated, fully
pre-authored multiple-choice trivia bank (`cfb_trivia_bank`, imported from
`College_Football_Trivia_Rivalry_Packs.xlsx`) that already ships its own
question text and all 4 options with one marked correct answer. There is no
distractor sampling here -- `evaluate()` only has to validate and reformat
the row into this pipeline's standard MCQ contract, never invent options.

--- WHAT'S IN THE BANK (imported this operation, see the import script) ---
1,272 real curated questions: 412 general CFB categories (Heisman Trophy,
National Championships, Coaches, Players & Legends, Deep Cuts, Bowls &
Playoff, Rivalries, Records & Stats, Conferences & History, Traditions &
Culture) + 860 rivalry-specific questions across 43 real school-vs-school
rivalry packs (20 questions each, e.g. "Iron Bowl (Alabama vs Auburn)",
"Red River Rivalry (Oklahoma vs Texas)"). School names on rivalry rows were
resolved to real `schools.school_id` values via an explicit, hand-verified
alias dict at import time (never a blind name join) -- see
`cfb_rivalry_pack_index` and the import script's own audit trail. One pack
(#13, Southwest Classic) has a genuinely ambiguous second school in the
source workbook itself ("Texas/Texas A&M") and was left unresolved rather
than guessed.

--- FILTERING BY RIVALRY (Creator "give me an Iron Bowl game" support) ---
`supported_filter_keys` includes `rivalry_pack_number` and `category` so a
Creator request naming a specific rivalry or pack can scope generation to
just that pack's 20 questions (or to the whole bank when no rivalry is
named). See `providers/mock.py` for the translator patterns that recognize
specific rivalry names and "SchoolA vs SchoolB" phrasing.
"""
from __future__ import annotations

from collections import Counter

from .. import difficulty as difficulty_mod
from .. import engine, safety, serializer

OUT_PATH = None  # Director-pipeline-only, like cfb_heisman.py
CATEGORY = "CFB Rivalry Trivia"
REQUIRED_SOURCE_ID = "CFB_RIVALRY_PACK_V1"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_RIVALRY_PACK_V1"
TRACK_ENTITY = True  # guard against ever repeating the same trivia_id within one export

# Opt-in marker `game_director_v01.generate_package_from_spec()` checks
# before calling `fetch_ordered_candidates()` with a 3rd `filters` argument
# -- every other adapter in this directory is called the original 2-arg way
# (c, seed) unchanged, so this is additive, not a signature break. See that
# function's own docstring for the full rationale (schema.py's
# ALLOWED_FILTER_KEYS was real, structural, but genuinely never wired to any
# adapter until this operation needed real "just this one rivalry pack"
# scoping for Creator requests like "Make me an Iron Bowl trivia game").
SUPPORTS_FILTERS = True

_DIFFICULTY_MAP = {"Medium": "Medium", "Hard": "Hard", "Very Hard": "Hard"}
_LETTER_TO_FIELD = {"A": "option_a", "B": "option_b", "C": "option_c", "D": "option_d"}


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_trivia_bank", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
    )


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None):
    filters = filters or {}
    where = ["verification_status = ?"]
    params = [REQUIRED_VERIFICATION_STATUS]
    pack_number = filters.get("rivalry_pack_number")
    if pack_number is not None:
        where.append("rivalry_pack_number = ?")
        params.append(pack_number)
    category = filters.get("category")
    if category is not None:
        where.append("category = ?")
        params.append(category)
    rivalry_only = filters.get("rivalry_only")
    if rivalry_only:
        where.append("is_rivalry = 1")

    rows = c.execute(
        f"SELECT * FROM cfb_trivia_bank WHERE {' AND '.join(where)} ORDER BY trivia_id",
        params,
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    options_in_order = [row["option_a"], row["option_b"], row["option_c"], row["option_d"]]
    if len(set(options_in_order)) != 4:
        return "DUPLICATE_OPTIONS"

    correct_field = _LETTER_TO_FIELD.get(row["correct_letter"])
    if correct_field is None:
        return "INVALID_CORRECT_LETTER"
    correct_text = row[correct_field]
    if not correct_text:
        return "MISSING_CORRECT_TEXT"

    question = row["question"]
    if not question:
        return "MISSING_QUESTION"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfbtrivia:{row['trivia_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_TRIVIA_ROW"

    distractor_texts = [o for o in options_in_order if o != correct_text]
    if len(distractor_texts) != 3:
        return "DISTRACTOR_COUNT_MISMATCH"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_text, distractor_texts)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_text:
        return "INVALID_CORRECT_INDEX"

    diff_label = _DIFFICULTY_MAP.get(row["difficulty"])
    if diff_label is None:
        return "UNKNOWN_DIFFICULTY_LABEL"
    band = "hard" if diff_label == "Hard" else "medium"

    category_label = row["category"]
    notes = row["notes"] or (
        f"From the curated Reads Football CFB Rivalry Trivia bank ({category_label})."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "trivia_id": row["trivia_id"], "source_category": category_label,
            "is_rivalry": bool(row["is_rivalry"]), "rivalry_pack_number": row["rivalry_pack_number"],
            "rivalry_pack_name": row["rivalry_pack_name"],
            "school_a_id": row["school_a_id"], "school_b_id": row["school_b_id"],
            "correct_answer_text": correct_text, "difficulty_band": band,
            "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the {considered_count} "
        f"curated CFB Rivalry Trivia rows this request matched; exported the maximum available "
        f"({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    packs = sorted({q["_audit"]["rivalry_pack_number"] for q in exported if q["_audit"]["rivalry_pack_number"]})
    categories = sorted({q["_audit"]["source_category"] for q in exported})
    return {
        "difficulty_band_distribution": dict(by_band),
        "rivalry_packs_covered": packs,
        "categories_covered": categories,
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_rivalry_trivia.py -- CFB Rivalry Trivia.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    pack = f"pack #{a['rivalry_pack_number']} ({a['rivalry_pack_name']})" if a["rivalry_pack_number"] else "general bank"
    return [
        f"- **Trivia row:** `{a['trivia_id']}`, category \"{a['source_category']}\" ({pack})",
        f"- **Correct answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_trivia_bank`, verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`",
    ]


def rivalry_coverage(c) -> dict:
    """Live coverage numbers for docs/known_limitations -- never hardcode a
    count that can silently go stale."""
    total = c.execute("SELECT COUNT(*) FROM cfb_trivia_bank").fetchone()[0]
    rivalry = c.execute("SELECT COUNT(*) FROM cfb_trivia_bank WHERE is_rivalry=1").fetchone()[0]
    packs = c.execute("SELECT COUNT(*) FROM cfb_rivalry_pack_index").fetchone()[0]
    return {"total_questions": total, "rivalry_questions": rivalry, "rivalry_packs": packs}
