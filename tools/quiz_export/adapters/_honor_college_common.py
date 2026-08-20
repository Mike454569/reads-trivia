"""Shared candidate-fetch/evaluate logic for "which honored player attended
this college" compositions (All-Pro+college, Pro Bowl+college, HOF+college)
-- Section 13/14's real composed relationship, never downgraded to generic
college-attendance trivia and never stripping the honor qualifier.

Built on `draft_facts.college` (12,914/12,927 real draft rows with a known
college, the same real, already-registered ATTENDED_COLLEGE/NFL_DRAFT
capability's own data) joined to each honor table's own resolved
`player_id` -- never a name join. Real pools measured directly before
building: 842 real All-Pro-player-seasons with a resolved college, 1,092
Pro Bowl, 104 Hall of Fame.
"""
from __future__ import annotations

from .. import engine, difficulty as difficulty_mod, serializer

# Same N+1-avoidance discipline as the other new _*_common.py adapters this
# pass -- cached per honor_table for the duration of one generation call,
# reset at the top of fetch_ordered_candidates().
_pool_cache: dict[str, list[str]] = {}


def fetch_ordered_candidates(c, seed: str, *, honor_table: str, honor_where: str = "1=1"):
    _pool_cache.clear()
    rows = c.execute(
        f"""
        SELECT DISTINCT h.player_id, d.college
        FROM {honor_table} h
        JOIN nfl_players_draft d ON d.player_key = h.player_id
        WHERE h.player_id IS NOT NULL AND d.college IS NOT NULL AND d.college != '' AND ({honor_where})
        """
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard, *, honor_table: str, honor_label: str, category: str, entity_prefix: str,
             name_column: str = "player_id"):
    player_row = c.execute("SELECT display_name FROM canonical_players WHERE player_id=?", (row["player_id"],)).fetchone()
    if not player_row or not player_row["display_name"]:
        return "UNRESOLVED_PLAYER_IDENTITY"
    correct_name = player_row["display_name"]
    college = row["college"]

    # Section 21 fix: a real, measured multi-valid-answer risk -- 107 real
    # colleges have more than one distinct real All-Pro alumnus (checked
    # directly before writing this). A college with more than one real
    # honored alumnus makes "which [honor] attended this college" a
    # genuinely ambiguous question (more than one real correct answer) --
    # rejected outright here, never resolved by arbitrarily picking one.
    same_college_count = c.execute(
        f"""
        SELECT COUNT(DISTINCT h.player_id) AS n
        FROM {honor_table} h JOIN nfl_players_draft d ON d.player_key = h.player_id
        WHERE h.player_id IS NOT NULL AND d.college = ?
        """,
        (college,),
    ).fetchone()["n"]
    if same_college_count > 1:
        return "AMBIGUOUS_MULTIPLE_HONORED_ALUMNI"

    cached = _pool_cache.get(honor_table)
    if cached is None:
        pool_rows = c.execute(
            f"""
            SELECT DISTINCT cp.display_name, d.college
            FROM {honor_table} h
            JOIN nfl_players_draft d ON d.player_key = h.player_id
            JOIN canonical_players cp ON cp.player_id = h.player_id
            WHERE h.player_id IS NOT NULL AND d.college IS NOT NULL AND d.college != ''
            """
        ).fetchall()
        cached = [(r["display_name"], r["college"]) for r in pool_rows if r["display_name"]]
        _pool_cache[honor_table] = cached
    pool = [name for name, coll in cached if name != correct_name and coll != college]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which NFL {honor_label} attended {college}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"{entity_prefix}:{row['player_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAYER"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    band = "MEDIUM"
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_name} ({honor_label}) attended {college}."

    return {
        "category": category, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "player_id": row["player_id"], "college": college, "correct_answer_text": correct_name,
            "difficulty_score": 0.5, "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED_COMPOSED", "source_id": "NFLVERSE_DATA",
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, honor_label: str) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real {honor_label}+college composed records on file; exported the maximum "
        f"available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def human_review_context(record: dict, *, honor_label: str, honor_table: str) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Player:** `{a['player_id']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **College:** {a['college']}",
        f"- **Underlying Engine source:** `{honor_table}` + `nfl_players_draft.college`, "
        f"composed via player_id (never a name join)",
    ]
