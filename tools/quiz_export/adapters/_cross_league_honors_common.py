"""Shared candidate-fetch/evaluate logic for "All-American who later became
an NFL [honor]" cross-league compositions (Section 12). Real, disclosed
double-name-join: `cfb_all_america_certified` (real, cfb_player_id-keyed)
joined by DISPLAY NAME to `nfl_cfb_player_links` (`match_status='AUTO_HIGH'`,
itself already a bare `EXACT_NORMALIZED_NAME` match, no further
verification) joined by `nfl_player_key` to the target NFL honor table.
Real pools measured directly before building: 4 real All-American -> NFL
All-Pro players, 11 real All-American -> NFL Pro Bowl players -- genuinely
small, disclosed, never padded. All-American -> Hall of Fame is NOT built
(real, measured overlap: 0) -- a genuine data-gap limitation, not an
unwritten adapter.
"""
from __future__ import annotations

from .. import engine, difficulty as difficulty_mod, serializer


def fetch_ordered_candidates(c, seed: str, *, honor_table: str):
    rows = c.execute(
        f"""
        SELECT DISTINCT aa.cfb_player_id, cp.display_name AS cfb_display_name, l.nfl_player_key,
               MIN(aa.season) AS aa_season, MIN(aa.position) AS aa_position
        FROM cfb_all_america_certified aa
        JOIN canonical_cfb_players cp ON cp.cfb_player_id = aa.cfb_player_id
        JOIN nfl_cfb_player_links l ON l.cfb_player_name = cp.display_name AND l.match_status = 'AUTO_HIGH'
        JOIN {honor_table} h ON h.player_id = l.nfl_player_key
        GROUP BY aa.cfb_player_id, cp.display_name, l.nfl_player_key
        """
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard, *, honor_table: str, honor_label: str, category: str, entity_prefix: str):
    nfl_row = c.execute("SELECT display_name FROM canonical_players WHERE player_id=?", (row["nfl_player_key"],)).fetchone()
    correct_name = (nfl_row["display_name"] if nfl_row and nfl_row["display_name"] else row["cfb_display_name"])
    if not correct_name:
        return "MISSING_FIELD"

    pool_rows = c.execute(
        f"""
        SELECT DISTINCT cp.display_name AS cfb_display_name, l.nfl_player_key
        FROM cfb_all_america_certified aa
        JOIN canonical_cfb_players cp ON cp.cfb_player_id = aa.cfb_player_id
        JOIN nfl_cfb_player_links l ON l.cfb_player_name = cp.display_name AND l.match_status = 'AUTO_HIGH'
        JOIN {honor_table} h ON h.player_id = l.nfl_player_key
        WHERE l.nfl_player_key != ?
        """,
        (row["nfl_player_key"],),
    ).fetchall()
    pool = []
    for r in pool_rows:
        nr = c.execute("SELECT display_name FROM canonical_players WHERE player_id=?", (r["nfl_player_key"],)).fetchone()
        name = nr["display_name"] if nr and nr["display_name"] else r["cfb_display_name"]
        if name and name != correct_name:
            pool.append(name)
    pool = list(dict.fromkeys(pool))
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    position_phrase = f" at {row['aa_position']}" if row["aa_position"] else ""
    question = (
        f"Which player was a real {row['aa_season']} College Football All-American{position_phrase} who "
        f"later became an NFL {honor_label}?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"{entity_prefix}:{row['cfb_player_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAYER"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    band = "MEDIUM"
    diff_label = difficulty_mod.map_band(band)
    notes = f"{correct_name} was a real College Football All-American who went on to become an NFL {honor_label}."

    return {
        "category": category, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "cfb_player_id": row["cfb_player_id"], "nfl_player_key": row["nfl_player_key"],
            "correct_answer_text": correct_name,
            "difficulty_score": 0.5, "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "DERIVED_DOUBLE_NAME_JOIN_AUTO_HIGH_ONLY", "source_id": None,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, honor_label: str) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real All-American -> NFL {honor_label} candidates on file (a genuinely small, "
        f"real, disclosed pool -- this Engine's only NFL<->CFB player bridge has 124 total rows); exported "
        f"the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def human_review_context(record: dict, *, honor_label: str, honor_table: str) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Player:** `{a['cfb_player_id']}` / `{a['nfl_player_key']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Cross-league honor:** College Football All-American -> NFL {honor_label}",
        f"- **Underlying Engine source:** `cfb_all_america_certified` + `nfl_cfb_player_links` "
        f"(name-joined, AUTO_HIGH only) + `{honor_table}` -- see this module's own docstring for the "
        f"full identity-resolution disclosure.",
    ]
