"""CFB All-America -> NFL Draft Team (Existing-Data Wiring pass) -- "this
real player was a College Football All-American; which real NFL team
drafted him?" Answers the exact CFB_ALL_AMERICAN -> NFL_DRAFT_TEAM
relationship named in the wiring spec's Phase 2/4.

Deliberately DOES NOT reuse _cross_league_honors_common.py's join verbatim
(unlike the sibling ALL_AMERICAN_TO_ALL_PRO/ALL_AMERICAN_TO_PRO_BOWL
capabilities, which join the full 7,745-row cfb_nfl_identity_bridge_
certified with no confidence-tier filter): this pass's own real-database
audit found that table is NOT uniformly rigorous -- only 2,542 of 7,745
rows (32.8%, confidence_tier='HIGH_CONFIDENCE_MULTI_SEASON_POSITION_
CORROBORATED') are ID-anchored and position/chronology-corroborated the
same way Engine's own separately-certified 3,534-row bridge is; the other
67% are a materially weaker name+chronology-only tier bolted on later
(flat confidence=0.85, no stable ID cross-check). Per the wiring spec's
own "accuracy over raw count, never loosen the certification standard"
rule, all NEW work this pass scopes to the HIGH_CONFIDENCE tier only --
measured directly: 463 real (cfb_player_id, nfl_draft_team) pairs at that
tier, a real, healthy candidate pool, not a thin one.

Team resolution reuses draft.py's own resolve_franchise() verbatim (the
exact same team_code+season -> real franchise name resolution DRAFTED_BY
already uses, including its franchise-relocation/rename handling) rather
than re-deriving team names from scratch.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise

OUT_PATH = None
CATEGORY = "CFB All-America"
TRACK_ENTITY = True
CONFIDENCE_TIER = "HIGH_CONFIDENCE_MULTI_SEASON_POSITION_CORROBORATED"


def safety_check(c) -> dict:
    from .. import safety
    return {
        "cfb_all_america_certified": safety.check_verification_status_safety(
            c, "cfb_all_america", "WIKIPEDIA_STRUCTURED", "WIKIPEDIA_STRUCTURED_SECONDARY",
        ),
    }


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        """
        SELECT DISTINCT aa.cfb_player_id, br.nfl_draft_team, br.nfl_draft_year,
               MIN(aa.season) AS aa_season, MIN(aa.position) AS aa_position,
               MAX(aa.is_consensus) AS was_consensus
        FROM cfb_all_america_certified aa
        JOIN cfb_nfl_identity_bridge_certified br ON br.cfb_player_id = aa.cfb_player_id
        WHERE br.confidence_tier = ? AND br.nfl_draft_team IS NOT NULL AND br.nfl_draft_year IS NOT NULL
        GROUP BY aa.cfb_player_id, br.nfl_draft_team, br.nfl_draft_year
        """,
        (CONFIDENCE_TIER,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def _display_name(c, cfb_player_id: str) -> str | None:
    row = c.execute("SELECT display_name FROM canonical_cfb_players WHERE cfb_player_id=?", (cfb_player_id,)).fetchone()
    return row["display_name"] if row else None


def evaluate(c, row, rng, guard):
    player_name = _display_name(c, row["cfb_player_id"])
    if not player_name:
        return "MISSING_FIELD"

    correct_franchise, err = resolve_franchise(c, row["nfl_draft_team"], row["nfl_draft_year"])
    if err or not correct_franchise:
        return "TEAM_UNRESOLVED"
    correct_name = correct_franchise["full_name"]

    pool_rows = c.execute(
        """
        SELECT DISTINCT br.nfl_draft_team, br.nfl_draft_year
        FROM cfb_all_america_certified aa
        JOIN cfb_nfl_identity_bridge_certified br ON br.cfb_player_id = aa.cfb_player_id
        WHERE br.confidence_tier = ? AND br.nfl_draft_team IS NOT NULL AND br.nfl_draft_year IS NOT NULL
        AND aa.cfb_player_id != ?
        """,
        (CONFIDENCE_TIER, row["cfb_player_id"]),
    ).fetchall()
    pool = []
    for r in pool_rows:
        fr, ferr = resolve_franchise(c, r["nfl_draft_team"], r["nfl_draft_year"])
        if not ferr and fr and fr["full_name"] != correct_name:
            pool.append(fr["full_name"])
    pool = list(dict.fromkeys(pool))
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    consensus_phrase = "a consensus " if row["was_consensus"] else "a "
    position_phrase = f" ({row['aa_position']})" if row["aa_position"] else ""
    question = (
        f"{player_name}{position_phrase} was {consensus_phrase}College Football All-American in "
        f"{row['aa_season']}. Which real NFL team drafted him?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_aa_draft_team:{row['cfb_player_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PLAYER"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    band = "MEDIUM"
    diff_label = difficulty_mod.map_band(band)
    notes = f"{player_name} was drafted by the {correct_name} ({row['nfl_draft_year']})."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "cfb_player_id": row["cfb_player_id"], "aa_season": row["aa_season"],
            "correct_answer_text": correct_name,
            "difficulty_score": 0.5, "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "DERIVED_FROM_CFB_NFL_IDENTITY_BRIDGE_CERTIFIED_HIGH_CONFIDENCE_TIER",
            "source_id": None,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real College-Football-All-American-to-NFL-draft-team candidates on file "
        f"(scoped to the bridge's HIGH_CONFIDENCE tier only, 463 real rows measured directly); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_all_america_draft_team.py -- CFB All-America -> NFL Draft Team.",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Player:** `{a['cfb_player_id']}`, {a['aa_season']} All-American (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `cfb_all_america_certified` + `cfb_nfl_identity_bridge_certified` "
        f"(HIGH_CONFIDENCE tier only) + `team_aliases`.",
    ]
