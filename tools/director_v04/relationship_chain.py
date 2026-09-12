"""RELATIONSHIP_CHAIN -- 40-Format Expansion pass, new mechanic template.

Backs SIX_DEGREES and CHAIN_REACTION, BOTH shipped as BETA/
SUPPORTED_WITH_LIMITATIONS this pass (see visual_templates.py) --
deliberately bounded to 2 real, pre-validated hops assembled at generation
time from `cfb_nfl_identity_bridge_certified` (7,745 rows, real ID-keyed
CFB-college -> NFL-draft bridge), never arbitrary live pathfinding between
two named entities (that harder, general version already exists for NFL
player/coach/team relationships as coach_connections_graph.py's real BFS
engine -- this module is a distinct, narrower, cross-league chain, not a
replacement for it).

A real chain has exactly 3 nodes / 2 hops:
  node 0: a real CFB school (bridge.school_name)
  node 1: a real player who played there and was later NFL-drafted (bridge.player_name)
  node 2: the real NFL team that drafted him (bridge.nfl_draft_team, resolved
          to a real franchise display name via draft.py's resolve_franchise)

Every hop is a real, already-certified row -- never invented or inferred.
Progressive reveal mirrors player_from_clues.py's real "reveal one node at a
time, guess the next" shape, generalized from biographical clues to
relationship hops.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters.draft import resolve_franchise  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "RELATIONSHIP_CHAIN"
MIN_CHAINS = 5

VARIANTS = frozenset({"CFB_SCHOOL_TO_NFL_TEAM_CHAIN"})


def safety_check(c) -> dict:
    # cfb_nfl_identity_bridge_certified has no verification_status/source_id
    # columns (a real, structural fact about this table -- confirmed live,
    # matches the same real convention tools/quiz_export/adapters/
    # cfb_all_american_to_all_pro.py's own safety_check() already
    # established for this identical table), so check_table_wide_safety's
    # uniform-provenance check does not apply here; this table's own
    # confidence_tier column is the real per-row trust signal instead,
    # filtered to HIGH_CONFIDENCE tiers only in _build_chains() above.
    return {"cfb_nfl_identity_bridge_certified": "composed via cross_league_identity_bridge, "
                                                  "confidence_tier filtered to HIGH_CONFIDENCE* only"}


def _build_chains(c, seed: str, chain_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT school_name, player_name, nfl_draft_team, nfl_draft_year FROM cfb_nfl_identity_bridge_certified "
        "WHERE confidence_tier LIKE 'HIGH_CONFIDENCE%' AND school_name IS NOT NULL "
        "AND player_name IS NOT NULL AND nfl_draft_team IS NOT NULL AND nfl_draft_year IS NOT NULL"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    order = list(rows)
    rng.shuffle(order)

    chains = []
    for r in order:
        if len(chains) >= chain_count:
            break
        fr, err = resolve_franchise(c, r["nfl_draft_team"], r["nfl_draft_year"])
        if err or fr is None:
            continue
        chains.append({
            "nodes": [
                {"node_id": "N0", "kind": "school", "label": r["school_name"]},
                {"node_id": "N1", "kind": "player", "label": r["player_name"]},
                {"node_id": "N2", "kind": "team", "label": fr["full_name"]},
            ],
            "prompt": f"This player played college football at {r['school_name']} and was drafted into the NFL. "
                      f"Which real NFL team drafted him?",
        })
    return chains


def generate_chains(seed: str, variant: str, chain_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        chains = _build_chains(c, seed, chain_count)
    finally:
        c.close()

    shortfall_reason = None
    if len(chains) < MIN_CHAINS:
        shortfall_reason = (
            f"Only {len(chains)} of {chain_count} requested real 2-hop chains could be built from "
            f"high-confidence cfb_nfl_identity_bridge_certified rows -- exported the maximum available "
            f"rather than lower the confidence bar."
        )
    return {"chains": chains, "safety": safety_result, "shortfall_reason": shortfall_reason}


def build_package(seed: str, variant: str, chain_count: int = 8) -> dict:
    result = generate_chains(seed, variant, chain_count=chain_count)
    package_id = "GGP15:" + hashlib.sha256(
        f"RELATIONSHIP_CHAIN|{variant}|{seed}|{chain_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "College to NFL Chain",
        "game_instructions": "See a real player's college, then guess the real NFL team that drafted him.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if len(result["chains"]) >= MIN_CHAINS else "FAILED",
        "chains": result["chains"], "chain_count": len(result["chains"]),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
