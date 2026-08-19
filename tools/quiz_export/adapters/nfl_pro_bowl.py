"""NFL Pro Bowl domain adapter (Creator Semantic Routing + Who Am I pass).

Built on `nfl_pro_bowl_selections` (4,216 rows, WIKIPEDIA_STRUCTURED_SECONDARY,
seasons 1972-2025). "Which player was selected to the Pro Bowl at [position]
in [season]" -- entity is one real Pro Bowl selection row, answer is the real
player name as recorded by the source. Genuinely distinct honor from
NFL_ALL_PRO (different selection process, different real player pool per
season, not a filter on the same table) -- see nfl_all_pro.py for the
sibling capability this mirrors the structure of.

Covers all four real selection tiers (Starter/Reserve/Alternate/Selected) as
one combined "selected to the Pro Bowl" honor; the specific tier is surfaced
in the question's own notes, not yet a filterable axis (matching
registry.py's own disclosed known_limitations for this capability).

Same "no player_id resolution required" discipline as nfl_all_pro.py --
player_name_raw is the real, source-verified answer text.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "NFL Pro Bowl"
REQUIRED_SOURCE_ID = "WIKIPEDIA_STRUCTURED"
REQUIRED_VERIFICATION_STATUS = "WIKIPEDIA_STRUCTURED_SECONDARY"
TRACK_ENTITY = True

MIN_SEASON = 1972
MAX_SEASON = 2025

_TIER_LABEL = {
    "STARTER": "a Pro Bowl starter", "RESERVE": "a Pro Bowl reserve",
    "ALTERNATE": "a Pro Bowl alternate", "SELECTED": "selected to the Pro Bowl",
}


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "nfl_pro_bowl_selections", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT selection_id, season, position_raw, player_name_raw, tier, source_id, verification_status "
        "FROM nfl_pro_bowl_selections ORDER BY season, selection_id"
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if not row["player_name_raw"] or not row["position_raw"]:
        return "MISSING_FIELD"
    if row["tier"] not in _TIER_LABEL:
        return "UNRESOLVED_TIER"

    correct_name = row["player_name_raw"]
    pool_rows = c.execute(
        "SELECT DISTINCT player_name_raw FROM nfl_pro_bowl_selections WHERE player_name_raw != ?",
        (correct_name,),
    ).fetchall()
    pool = [r["player_name_raw"] for r in pool_rows]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    season = row["season"]
    question = f"Which player was named to the Pro Bowl at {row['position_raw']} for the {season} NFL season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_probowl:{row['selection_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_SELECTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_name} was {_TIER_LABEL[row['tier']]} at {row['position_raw']} for the {season} NFL season."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "selection_id": row["selection_id"], "tier": row["tier"],
            "position_raw": row["position_raw"], "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real Pro Bowl selection records on file ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    tiers = Counter(q["_audit"]["tier"] for q in exported)
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "tier_distribution": dict(tiers),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_pro_bowl.py -- NFL Pro Bowl.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Selection:** `{a['selection_id']}`, {a['season']}, {a['tier']}",
        f"- **Position:** {a['position_raw']}",
        f"- **Underlying Engine source:** `nfl_pro_bowl_selections`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
