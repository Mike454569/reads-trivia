"""CFB Transfer Path (ordered, NFL-bridged) domain adapter (Creator
Capability Completion pass).

Answers the real manual-failure prompt directly: "a transfer player who
later made the NFL... guess his college path" -- the ORDERED relationship
is the point (Section 11's own explicit instruction), never downgraded to
"which was one of his schools."

Built on `cfb_transfer_summary_v17` (109,221 rows; `schools` is a real,
chronologically-ordered comma-separated string -- confirmed directly by
cross-checking against `cfb_roster_seasons_real`'s own per-season order
before building, e.g. Will Rogers: Mississippi State 2020/2022/2023 then
Washington 2024 matches "Mississippi State,Washington" exactly) filtered
to `school_count >= 2`, joined by real display name to
`nfl_cfb_player_links` (`match_status='AUTO_HIGH'`, the higher-confidence
half of this Engine's only real NFL<->CFB player bridge).

Real, disclosed limitation: this bridge is itself a bare exact-name match
(`match_rule='EXACT_NORMALIZED_NAME'` for every one of its 124 rows -- no
multi-signal verification), and this adapter joins to it a SECOND time by
name (transfer-summary display_name -> bridge cfb_player_name) rather than
a shared id -- a real, disclosed double-name-join, not silently presented
as a certified identity chain. Real eligible pool measured directly before
building: 12 real players (Cam Newton, Joe Burrow, Kyler Murray, Jalen
Hurts, Michael Penix Jr., and others) -- small, but real and disclosed, not
padded.

Uses the existing `guess` mechanic, not a new sorting mechanic (Section 1's
own "reuse the existing mechanic" instruction): the correct option is the
real path in correct chronological order; every distractor is either the
SAME player's path in a real-but-wrong order, or a DIFFERENT real player's
correctly-ordered path -- so a correct guess requires genuinely knowing
both which schools and their real order, never just recognizing one
familiar name.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Transfer Path (NFL-Bridged)"
TRACK_ENTITY = True
MIN_SCHOOL_COUNT = 2


def safety_check(c) -> dict:
    # Neither cfb_transfer_summary_v17 nor nfl_cfb_player_links carries a
    # per-row source_id/verification_status column of its own (both are
    # derived tables -- confirmed directly against their real schema, same
    # real distinction cfb_player_from_clues.py's own transfer_school_count
    # clue type already discloses). This reports the real row counts and
    # the double-name-join methodology instead of a fabricated status.
    total = c.execute("SELECT COUNT(*) FROM cfb_transfer_summary_v17 WHERE school_count >= ?", (MIN_SCHOOL_COUNT,)).fetchone()[0]
    bridge_total = c.execute("SELECT COUNT(*) FROM nfl_cfb_player_links WHERE match_status='AUTO_HIGH'").fetchone()[0]
    return {
        "source_id": None, "verification_status": "DERIVED_NAME_JOIN_AUTO_HIGH_ONLY",
        "cfb_transfer_summary_v17_multi_school_rows": total,
        "nfl_cfb_player_links_auto_high_rows": bridge_total,
    }


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        """
        SELECT t.cfb_player_id, t.display_name, t.schools, t.school_count
        FROM cfb_transfer_summary_v17 t
        JOIN nfl_cfb_player_links l ON l.cfb_player_name = t.display_name AND l.match_status = 'AUTO_HIGH'
        WHERE t.school_count >= ?
        """,
        (MIN_SCHOOL_COUNT,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if not row["schools"] or not row["display_name"]:
        return "MISSING_FIELD"
    schools = [s.strip() for s in row["schools"].split(",") if s.strip()]
    if len(schools) < 2:
        return "INSUFFICIENT_SCHOOL_COUNT"
    if len(set(schools)) != len(schools):
        return "DUPLICATE_SCHOOL_IN_PATH"

    correct_path = " → ".join(schools)
    reversed_path = " → ".join(reversed(schools))

    other_rows = c.execute(
        """
        SELECT t.schools FROM cfb_transfer_summary_v17 t
        JOIN nfl_cfb_player_links l ON l.cfb_player_name = t.display_name AND l.match_status = 'AUTO_HIGH'
        WHERE t.school_count >= ? AND t.cfb_player_id != ?
        """,
        (MIN_SCHOOL_COUNT, row["cfb_player_id"]),
    ).fetchall()
    other_paths = []
    for r in other_rows:
        other_schools = [s.strip() for s in (r["schools"] or "").split(",") if s.strip()]
        if len(other_schools) >= 2 and len(set(other_schools)) == len(other_schools):
            other_paths.append(" → ".join(other_schools))
    other_paths = list(dict.fromkeys(other_paths))

    distractor_pool = [reversed_path] + [p for p in other_paths if p not in (correct_path, reversed_path)]
    distractor_pool = list(dict.fromkeys(distractor_pool))
    if len(distractor_pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_paths = [distractor_pool[0]] + list(rng.sample(distractor_pool[1:], min(2, len(distractor_pool) - 1)))
    if len(distractor_paths) < 3:
        distractor_paths = list(rng.sample(distractor_pool, 3))

    options = [correct_path] + distractor_paths
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = (
        f"{row['display_name']} played college football at {len(schools)} real schools before reaching "
        f"the NFL. Which is the correct chronological order?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_transfer_path:{row['cfb_player_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAYER"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_path, distractor_paths)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_path:
        return "INVALID_CORRECT_INDEX"

    # More real schools in the path = more to keep straight = harder.
    diff_score = min((len(schools) - 2) / 2, 1.0)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{row['display_name']}'s real college path, in order: {correct_path}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "cfb_player_id": row["cfb_player_id"], "school_count": len(schools),
            "correct_answer_text": correct_path,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "DERIVED_NAME_JOIN_AUTO_HIGH_ONLY", "source_id": None,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real NFL-bridged multi-school transfer players on file (a genuinely small, "
        f"real pool -- this Engine's only NFL<->CFB player bridge has 124 total rows); exported the "
        f"maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_transfer_path.py -- CFB Transfer Path (NFL-Bridged).",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Player:** `{a['cfb_player_id']}`, {a['school_count']} real schools",
        f"- **Path:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_transfer_summary_v17` + `nfl_cfb_player_links` "
        f"(name-joined, AUTO_HIGH only) -- see this adapter's own module docstring for the full "
        f"identity-resolution disclosure.",
    ]
