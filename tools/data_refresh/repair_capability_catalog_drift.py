"""Targeted catalog-drift repair for five capabilities already shipped in registry/public routing.

Production's Engine volume predates the catalog writes that accompanied these
capabilities in development. This repair is intentionally narrow and idempotent:
it inserts only the five known-missing rows, never overwrites an existing row,
and records the real scoping rules the adapters enforce.
"""
from __future__ import annotations

import datetime as dt
import json

from tools.director_v02 import registry
from tools.quiz_export import engine

_REPAIRS = {
    ("guess", "CFB_2026_CURRENT_ROSTER", "ON_2026_ROSTER"): {
        "source_tables": "cfb_roster_seasons_real,canonical_cfb_players,schools",
        "source_id": "READS_MASTER_KNOWLEDGE_FEED_2026_09",
        "season_coverage_min": 2026, "season_coverage_max": 2026,
        "tie_rule": "one resolved school per player-season row",
        "ambiguity_rule": "exclude unresolved name collisions and rows missing required position data",
        "eligible_answer_rule": "resolved 2026 roster rows from the verified workbook source",
        "distractor_scoping_rule": "other real 2026 teams present in the same verified roster source",
        "min_candidate_pool_size": 4,
    },
    ("guess", "CFB_2026_HEAD_COACH", "COACHES_TEAM_2026"): {
        "source_tables": "cfb_team_2026_coaching_profile,cfb_coaches,schools",
        "season_coverage_min": 2026, "season_coverage_max": 2026,
        "tie_rule": "one recorded 2026 head coach per school profile",
        "ambiguity_rule": "reuse canonical coach identity when resolvable; never duplicate an existing coach-school identity",
        "eligible_answer_rule": "schools with a verified 2026 coaching-profile row",
        "distractor_scoping_rule": "other real teams represented in the verified 2026 coaching profile",
        "min_candidate_pool_size": 4,
    },
    ("guess", "CFB_BETTING", "COVERED_SPREAD"): {
        "source_tables": "cfb_betting_lines,cfb_games_canonical,schools",
        "tie_rule": "pushes are excluded because no team covered",
        "ambiguity_rule": "provider is scoped explicitly; consensus is the default provider",
        "eligible_answer_rule": "completed games with a non-push spread result and both real teams resolved",
        "distractor_scoping_rule": "binary choice is limited to the two teams that actually played",
        "min_candidate_pool_size": 2,
    },
    ("guess", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_NFL_DRAFT_TEAM"): {
        "source_tables": "cfb_all_america_certified,cfb_nfl_identity_bridge_certified,team_aliases",
        "tie_rule": "one resolved NFL draft franchise per certified player-draft record",
        "ambiguity_rule": "use only HIGH_CONFIDENCE_MULTI_SEASON_POSITION_CORROBORATED identity-bridge rows",
        "eligible_answer_rule": "certified All-Americans with a high-confidence bridge row and resolvable NFL draft team",
        "distractor_scoping_rule": "other resolvable NFL draft franchises from the same certified candidate pool",
        "min_candidate_pool_size": 4,
    },
    ("guess", "CFB_GAME_BOXSCORE", "HAD_MORE_SACKS"): {
        "source_tables": "cfb_plays,cfb_games_canonical,schools",
        "source_id": "CFBD_API_LIVE",
        "season_coverage_min": 2002, "season_coverage_max": 2025,
        "tie_rule": "games with equal team sack totals are excluded",
        "ambiguity_rule": "team-level only because CFB play-by-play has no reliable player sack identity",
        "eligible_answer_rule": "real CFB games with play-by-play and a decisive team sack-count comparison",
        "distractor_scoping_rule": "binary choice is limited to the two teams that actually played",
        "min_candidate_pool_size": 2,
    },
}


def repair_missing_catalog_rows(conn=None) -> dict:
    own = conn is None
    c = conn or engine.connect()
    inserted = []
    try:
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        for key, meta in _REPAIRS.items():
            mechanic, domain, predicate = key
            capability_id = f"{domain}__{predicate}"
            if c.execute("SELECT 1 FROM capability_catalog WHERE capability_id=?", (capability_id,)).fetchone():
                continue
            cap = registry.CAPABILITY_REGISTRY[key]
            adapter = cap.get("adapter")
            values = {
                "capability_id": capability_id,
                "version": 1,
                "mechanic": mechanic,
                "domain": domain,
                "relationship_predicate": predicate,
                "input_entity_type": cap.get("entity_type"),
                "output_entity_type": cap.get("answer_type"),
                "known_limitations": json.dumps(list(cap.get("known_limitations", []))),
                "verification_status": "PUBLIC_ENABLED",
                "human_review_status": "APPROVED",
                "compiler_support": "HAND_WRITTEN",
                "runtime_adapter_module": getattr(adapter, "__name__", None),
                "public_availability": "PUBLIC_ENABLED",
                "created_at": now,
                "updated_at": now,
                **meta,
            }
            cols = list(values)
            c.execute(
                f"INSERT INTO capability_catalog ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                [values[k] for k in cols],
            )
            inserted.append(capability_id)
        c.commit()
        return {"inserted": inserted, "inserted_count": len(inserted)}
    finally:
        if own:
            c.close()


if __name__ == "__main__":
    print(repair_missing_catalog_rows())
