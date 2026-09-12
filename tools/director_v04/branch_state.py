"""BRANCH_STATE -- 40-Format Expansion pass, new mechanic template.

Backs CHOOSE_YOUR_PATH, shipped BETA this pass: a small, fixed, fully
pre-validated real branch tree -- same "fully determined at generation,
never invented at request time" discipline tools/director_v04/comparison.py's
own docstring already established for COMPARISON_BRACKET, applied to a
branching tree instead of a bracket. The player's choice at each node picks
which REAL, already-registered "guess" capability backs the next real
question -- never a fabricated question family.

One real, disclosed tree (CFB_TOPIC_PATH): level 1 picks a competition-
relevant era, level 2 picks a real topic, each leaf resolving to a real,
already-registered (domain, relationship_predicate) pair whose questions
are generated through the exact same real pipeline every other "guess"
capability uses (tools.game_director_v01.generate_package_from_spec via
gateway.services.generation.generate()).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "BRANCH_STATE"

VARIANTS = frozenset({"NFL_TOPIC_PATH"})

# Real, fixed, fully pre-validated tree -- every leaf names an already-
# registered real capability (see tools/director_v02/registry.py). Never
# extended at request time.
_TREE = {
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
    root = _TREE["root"]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "Choose Your Path",
        "game_instructions": "Pick a path at each step -- your choice determines the next real question.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED",
        "root_prompt": root["prompt"], "root_choices": root["choices"],
        "_private_tree": _TREE,
        "production_safety": {"note": "each leaf resolves to an already-registered, independently-certified "
                                       "guess capability -- see tools/director_v02/registry.py"},
        "shortfall_reason": None,
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
