"""NFL All-Pro domain adapter (Creator Semantic Routing + Who Am I pass).

Built on `nfl_all_pro_selections` (4,964 rows, WIKIPEDIA_STRUCTURED_SECONDARY,
seasons 1932-2025). "Which player was named [First-Team|Second-Team] All-Pro
at [position] in [season]" -- entity is one real AP All-Pro selection row,
answer is the real player name as recorded by the source.

Scoped to `is_ap=1` only (3,207 of 4,964 rows) -- the AP All-Pro team is the
one real, single, unambiguous "All-Pro team" concept this table covers (it
also carries selections from other historical bodies, e.g. NYDN/PFW/SN/UPI,
mixed into the same rows via `selectors_raw`; building on the specific,
named AP designation avoids silently conflating separate selecting bodies
into one implied "the" All-Pro team, the same discipline nfl_season_awards.py
already applies by keeping each award body distinct). Also excludes
`honor_level='UNKNOWN_NO_AP_TAG'` (424 of the full table, 0 once scoped to
is_ap=1 -- confirmed by direct query) since the whole point of this
capability is the real First-Team/Second-Team distinction the task
explicitly requires be preserved.

Does NOT require `player_id` resolution (only 2,765/4,964 rows resolve) --
unlike a capability that needs to JOIN to another player-identity table
(e.g. college), a standalone "guess which player" question only needs the
real, source-verified `player_name_raw` string as both the correct answer
and the distractor pool, exactly the same "raw sourced name is the real
answer" discipline `cfb_heisman.py`/`nfl_hof.py` already use. Distractors
are NOT position/season-scoped (drawn from the full distinct-name pool,
same disclosed tradeoff `cfb_heisman.py`'s school distractors already make)
-- position label text is inconsistent across eras (bracketed footnote
markers, spelling variants) and season-scoping would starve older seasons
of a real 3-name distractor pool.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "NFL All-Pro"
REQUIRED_SOURCE_ID = "WIKIPEDIA_STRUCTURED"
REQUIRED_VERIFICATION_STATUS = "WIKIPEDIA_STRUCTURED_SECONDARY"
TRACK_ENTITY = True

MIN_SEASON = 1932
MAX_SEASON = 2025

_HONOR_LABEL = {"FIRST_TEAM": "First-Team", "SECOND_TEAM": "Second-Team"}


def safety_check(c) -> dict:
    # nfl_all_pro_selections carries a real per-row source_id AND
    # verification_status, but the verification_status value is
    # 'WIKIPEDIA_STRUCTURED_SECONDARY', not 'SOURCE_BACKED' --
    # check_table_wide_safety() hardcodes the latter (confirmed directly
    # against safety.py before writing this, same real mix-up
    # cfb_heisman.py's own module comment documents), so this uses
    # check_verification_status_safety() instead, same pattern.
    return safety.check_verification_status_safety(
        c, "nfl_all_pro_selections", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra="is_ap = 1",
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT selection_id, season, position_raw, player_name_raw, honor_level, source_id, verification_status "
        "FROM nfl_all_pro_selections WHERE is_ap = 1 ORDER BY season, selection_id"
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
    honor_label = _HONOR_LABEL.get(row["honor_level"])
    if honor_label is None:
        return "UNRESOLVED_HONOR_LEVEL"

    correct_name = row["player_name_raw"]
    pool_rows = c.execute(
        "SELECT DISTINCT player_name_raw FROM nfl_all_pro_selections "
        "WHERE is_ap = 1 AND player_name_raw != ?",
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
    question = f"Which player was named {honor_label} All-Pro at {row['position_raw']} in the {season} NFL season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_allpro:{row['selection_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_SELECTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_name} was named {honor_label} All-Pro at {row['position_raw']} for the {season} NFL season."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "selection_id": row["selection_id"], "honor_level": row["honor_level"],
            "position_raw": row["position_raw"], "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "WIKIPEDIA_STRUCTURED_SECONDARY", "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real AP All-Pro selection records on file ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    honor_levels = Counter(q["_audit"]["honor_level"] for q in exported)
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "honor_level_distribution": dict(honor_levels),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_all_pro.py -- NFL All-Pro.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Selection:** `{a['selection_id']}`, {a['season']}, {a['honor_level']}",
        f"- **Position:** {a['position_raw']}",
        f"- **Underlying Engine source:** `nfl_all_pro_selections`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
