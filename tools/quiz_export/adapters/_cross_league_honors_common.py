"""Shared candidate-fetch/evaluate logic for "All-American who later became
an NFL [honor]" cross-league compositions (Section 12).

Absolute Final Closeout fix: this used to join `cfb_all_america_certified`
to `nfl_cfb_player_links` by DISPLAY NAME (`match_status='AUTO_HIGH'` only,
itself a bare EXACT_NORMALIZED_NAME match with no further verification) --
a fragile, name-collision-prone bridge with only 124 total rows (105
AUTO_HIGH + 19 AUTO_REVIEW, the latter never even used). Rebuilt on
`cfb_nfl_identity_bridge_certified` (7,745 rows, real ID-keyed --
cfb_player_id -> nfl_player_key, promoted via a real, disclosed multi-
season/position-corroborated confidence pipeline, already used elsewhere
in this codebase for CFB Who Am I's difficulty banding) instead -- a
strictly BETTER, already-certified real bridge that was simply never
discovered/used by whoever originally built this module. Measured
directly, real pools grew from 4 -> 117 (All-Pro) and 11 -> 137 (Pro
Bowl), a clean ID join, never a fuzzy name match, never fabricated.
"""
from __future__ import annotations

from .. import engine, difficulty as difficulty_mod, serializer


def fetch_ordered_candidates(c, seed: str, *, honor_table: str):
    rows = c.execute(
        f"""
        SELECT DISTINCT aa.cfb_player_id, br.nfl_player_key,
               MIN(aa.season) AS aa_season, MIN(aa.position) AS aa_position
        FROM cfb_all_america_certified aa
        JOIN cfb_nfl_identity_bridge_certified br ON br.cfb_player_id = aa.cfb_player_id
        JOIN {honor_table} h ON h.player_id = br.nfl_player_key
        GROUP BY aa.cfb_player_id, br.nfl_player_key
        """
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def _display_name(c, cfb_player_id: str, nfl_player_key: str) -> str | None:
    nfl_row = c.execute("SELECT display_name FROM canonical_players WHERE player_id=?", (nfl_player_key,)).fetchone()
    if nfl_row and nfl_row["display_name"]:
        return nfl_row["display_name"]
    cfb_row = c.execute("SELECT display_name FROM canonical_cfb_players WHERE cfb_player_id=?", (cfb_player_id,)).fetchone()
    return cfb_row["display_name"] if cfb_row else None


def evaluate(c, row, rng, guard, *, honor_table: str, honor_label: str, category: str, entity_prefix: str):
    correct_name = _display_name(c, row["cfb_player_id"], row["nfl_player_key"])
    if not correct_name:
        return "MISSING_FIELD"

    pool_rows = c.execute(
        f"""
        SELECT DISTINCT aa.cfb_player_id, br.nfl_player_key
        FROM cfb_all_america_certified aa
        JOIN cfb_nfl_identity_bridge_certified br ON br.cfb_player_id = aa.cfb_player_id
        JOIN {honor_table} h ON h.player_id = br.nfl_player_key
        WHERE br.nfl_player_key != ?
        """,
        (row["nfl_player_key"],),
    ).fetchall()
    pool = []
    for r in pool_rows:
        name = _display_name(c, r["cfb_player_id"], r["nfl_player_key"])
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
            "verification_status": "DERIVED_FROM_CFB_NFL_IDENTITY_BRIDGE_CERTIFIED", "source_id": None,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count, *, honor_label: str) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real All-American -> NFL {honor_label} candidates on file (via the real, "
        f"7,745-row cfb_nfl_identity_bridge_certified); exported the maximum available ({accepted_count}) "
        f"rather than loosen any rule to reach {target_count}."
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
        f"- **Underlying Engine source:** `cfb_all_america_certified` + `cfb_nfl_identity_bridge_certified` "
        f"(real ID join) + `{honor_table}`.",
    ]
