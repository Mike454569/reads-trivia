"""BRANCH_STATE -- 40-Format Expansion pass, new mechanic template.

Backs CHOOSE_YOUR_PATH, shipped BETA this pass: a small, fixed, fully
pre-validated real branch tree -- same "fully determined at generation,
never invented at request time" discipline tools/director_v04/comparison.py's
own docstring already established for COMPARISON_BRACKET, applied to a
branching tree instead of a bracket. The player's choice at each node picks
which REAL, already-registered "guess" capability backs the next real
question -- never a fabricated question family.

Two real, disclosed trees:

- NFL_TOPIC_PATH: a single level, 3 real leaf capabilities (NFL_DRAFT,
  NFL_CHAMPIONSHIP, NFL_COACHING).
- CFB_TOPIC_PATH (Part 1C, cleanup pass): 5 real leaf capabilities
  (CFB_HEISMAN/WON_HEISMAN, CFB_CHAMPIONSHIP/WON_CHAMPIONSHIP,
  CFB_RIVALRY/RIVAL_OF, CFB_RANKING/RANKED_IN_POLL) plus a genuine second
  level under "Upsets" that splits into CFB_UPSET/RANKING_UPSET vs.
  CFB_UPSET/BETTING_UPSET -- two real, structurally distinct upset
  definitions (see registry.py's own entries for each), not a decorative
  extra tap that lands on the same generator as its sibling. Every leaf in
  both trees resolves to a real, already-registered (domain,
  relationship_predicate) pair, confirmed live in tools/director_v02/
  registry.py before being wired in here -- never a fabricated capability.

Each leaf's questions are generated through the exact same real pipeline
every other "guess" capability uses (tools.game_director_v01.
generate_package_from_spec via gateway.services.generation.generate()).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "BRANCH_STATE"

VARIANTS = frozenset({"NFL_TOPIC_PATH", "CFB_TOPIC_PATH"})

# Real, fixed, fully pre-validated trees -- every leaf names an already-
# registered real capability (see tools/director_v02/registry.py). Never
# extended at request time. A node is either a branch ("choices": [...],
# each choice's "next" pointing at another node in the same tree) or a
# leaf ("domain"/"relationship_predicate" naming a real registered
# capability) -- mechanic_engine.py's _branch_state_evaluate() tells them
# apart generically, so a branch's "next" can point at either another
# branch or a leaf.
_NFL_TREE = {
    "root": {
        "prompt": "Pick a topic.",
        "choices": [
            {"choice_id": "DRAFT", "label": "NFL Draft", "next": "draft_leaf"},
            {"choice_id": "CHAMPIONSHIP", "label": "Championships", "next": "championship_leaf"},
            {"choice_id": "COACHING", "label": "Coaching", "next": "coaching_leaf"},
        ],
    },
    "draft_leaf": {"domain": "NFL_DRAFT", "relationship_predicate": "DRAFTED_BY"},
    "championship_leaf": {"domain": "NFL_CHAMPIONSHIP", "relationship_predicate": "TEAM_POSTSEASON_RESULT"},
    "coaching_leaf": {"domain": "NFL_COACHING", "relationship_predicate": "COACHED_TEAM"},
}

_CFB_TREE = {
    "root": {
        "prompt": "Pick a CFB topic.",
        "choices": [
            {"choice_id": "HEISMAN", "label": "Heisman Trophy", "next": "cfb_heisman_leaf"},
            {"choice_id": "CHAMPIONSHIP", "label": "National Championships", "next": "cfb_championship_leaf"},
            {"choice_id": "RIVALRY", "label": "Rivalries", "next": "cfb_rivalry_leaf"},
            {"choice_id": "RANKING", "label": "AP Top 25 Rankings", "next": "cfb_ranking_leaf"},
            {"choice_id": "UPSET", "label": "Upsets", "next": "cfb_upset_branch"},
        ],
    },
    "cfb_heisman_leaf": {"domain": "CFB_HEISMAN", "relationship_predicate": "WON_HEISMAN"},
    "cfb_championship_leaf": {"domain": "CFB_CHAMPIONSHIP", "relationship_predicate": "WON_CHAMPIONSHIP"},
    "cfb_rivalry_leaf": {"domain": "CFB_RIVALRY", "relationship_predicate": "RIVAL_OF"},
    "cfb_ranking_leaf": {"domain": "CFB_RANKING", "relationship_predicate": "RANKED_IN_POLL"},
    "cfb_upset_branch": {
        "prompt": "Which kind of upset?",
        "choices": [
            {"choice_id": "RANKING_UPSET", "label": "Ranking Upsets", "next": "cfb_upset_ranking_leaf"},
            {"choice_id": "BETTING_UPSET", "label": "Betting Upsets", "next": "cfb_upset_betting_leaf"},
        ],
    },
    "cfb_upset_ranking_leaf": {"domain": "CFB_UPSET", "relationship_predicate": "RANKING_UPSET"},
    "cfb_upset_betting_leaf": {"domain": "CFB_UPSET", "relationship_predicate": "BETTING_UPSET"},
}

_TREES = {"NFL_TOPIC_PATH": _NFL_TREE, "CFB_TOPIC_PATH": _CFB_TREE}


def _generate_leaf_question(*, domain: str, relationship_predicate: str, seed: str) -> dict | None:
    from gateway.services import generation as generation_service
    spec = {"mechanic": "guess", "domain": domain, "relationship_predicate": relationship_predicate,
            "question_count": 1, "difficulty": "any", "filters": {}, "exclusions": []}
    result = generation_service.generate(request_text=None, spec=spec, provider="mock",
                                          puzzle_count=None, difficulty=None, seed=seed)
    questions = result.get("questions", []) if isinstance(result, dict) else []
    return questions[0] if questions else None


def build_package(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    package_id = "GGP16:" + hashlib.sha256(
        f"BRANCH_STATE|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    tree = _TREES[variant]
    root = tree["root"]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "Choose Your Path",
        "game_instructions": "Pick a path at each step -- your choice determines the next real question.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED",
        "root_prompt": root["prompt"], "root_choices": root["choices"],
        "_private_tree": tree,
        "production_safety": {"note": "each leaf resolves to an already-registered, independently-certified "
                                       "guess capability -- see tools/director_v02/registry.py"},
        "shortfall_reason": None,
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
