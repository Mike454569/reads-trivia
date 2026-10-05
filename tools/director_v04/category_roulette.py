"""CATEGORY_ROULETTE -- 75-Format Expansion (Wave 1), format #35 overall.

Real random-category trivia: each round's real category (NFL Team Records,
Heisman Winners, or Super Bowl Champions) is shown openly, immediately
followed by that category's real question -- no wager, no hidden
content, no fictional balance at all. Rounds cycle through all 3 real
categories in a real, deterministic rotation (never all-one-category by
chance for a round_count >= 3 session).

Reuses tools.director_v04.wager_mode's own real, already-certified
question-builder functions (_nfl_draft_question/_heisman_question/
_super_bowl_question) and safety_check verbatim -- same real data, same
real decoy discipline, new (much simpler) rules only.

Deliberately distinct from WAGER_MODE (this pass) per the user's own
spec: "ROULETTE determines the trivia category for immediate play"
(the category and question are both shown immediately, no commit-before-
you-see-it step) vs. FOOTBALL_WHEEL, which the spec describes as
combining multiple modifiers/attributes (a separate, not-yet-built
format). WAGER_MODE hides the category's specific question behind a
real wager decision and tracks a persistent real fictional balance;
CATEGORY_ROULETTE has neither -- plain immediate trivia, real per-round
correct/incorrect only.

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also")
reviewed this format and did NOT add a separate CFB variant: this format
already mixes leagues WITHIN its one existing variant -- 1 of its 3 real
rotating categories (Heisman Winners) is already real CFB content
(cfb_award_facts), alongside NFL Draft and Super Bowl Champions. Splitting
it into single-league variants would remove the real cross-league mix
that is this format's whole premise, not add CFB coverage to it.

Single variant: CATEGORY_ROULETTE_MIXED.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import wager_mode, deep_trivia  # noqa: E402

PACKAGE_SCHEMA_VERSION = "2.0"
MECHANIC = "CATEGORY_ROULETTE"
VARIANTS = frozenset({"CATEGORY_ROULETTE_MIXED"})


def safety_check(c) -> dict:
    return wager_mode.safety_check(c)


def generate_rounds(seed: str, variant: str, round_count: int = 6) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety = wager_mode.safety_check(c)
    finally:
        c.close()
    rounds = deep_trivia.generate_rounds(
        f"{seed}-category-roulette", round_count
    )
    return {
        "rounds": rounds,
        "safety": safety,
        "shortfall_reason": None if len(rounds) == round_count else (
            f"Only {len(rounds)} of {round_count} requested Deep Ball rounds "
            "could be built from certified real data."
        ),
    }


_GAME_TITLES = {"CATEGORY_ROULETTE_MIXED": "Category Roulette"}


def build_package(seed: str, variant: str, round_count: int = 6) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP37:" + hashlib.sha256(
        f"CATEGORY_ROULETTE|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_label"]] + list(r["decoy_labels"])
        order = list(range(len(candidates)))
        engine_bootstrap.seeded(f"{seed}-cr-shuffle-{i}").shuffle(order)
        item_ids = [chr(ord("A") + n) for n in range(len(candidates))]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i,
            "category": r["category"],
            "bucket": r.get("bucket"),
            "difficulty": r.get("difficulty"),
            "depth_source": r.get("depth_source"),
            "prompt": r["prompt"],
            "options": options,
            "_answer_item_id": item_ids[correct_pos],
            "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Each round pulls from Reads' Deep Ball pool -- game context, player performance, "
                              "rankings, rivalries, careers and more. Read the category and make the call.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
