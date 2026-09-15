"""THREE_STRIKES -- 75-Format Expansion (Wave 1), format #32 overall.

Real strikes-budget survival: the player answers a sequence of real
questions of escalating real difficulty (reusing risk_it.py's own real
draft_pick_overall difficulty proxy and real 4-option decoy-building
logic verbatim). The real question is always shown directly (never a
blind tier-commit). A wrong answer costs one of the player's 3 starting
strikes; the run ends when strikes reach 0 or the real question pool is
exhausted, whichever comes first. Each correct answer earns that round's
real fixed points (LOW=1, MEDIUM=2, HIGH=3) -- score and streak both
tracked, but points never double (unlike DOUBLE_OR_NOTHING).

Deliberately distinct from RISK_IT (protected, 15-Format Expansion):
RISK_IT requires the player to blindly COMMIT to a risk tier before
seeing any question content each round -- the tier is a real strategic
choice. THREE_STRIKES never hides the question or asks the player to
choose a tier at all; difficulty escalates automatically by round
position, and the real challenge is purely survival across a 3-strike
budget. Also distinct from ELIMINATION_SURVIVAL (protected, Reliability
Design Phase 6): that format is single-miss (1 life) true/false
category-membership; THREE_STRIKES is a 3-life budget over 4-option MC
questions from a different real domain (draft picks, not championship
membership). Also distinct from DOUBLE_OR_NOTHING (this pass): that
format has NO lives at all (one miss ends the run) and doubles points
with an explicit bank-or-risk choice; THREE_STRIKES has a real strike
budget, fixed per-tier points, and no bank choice.

Single variant: NFL_DRAFT_THREE_STRIKES.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import risk_it  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "THREE_STRIKES"
VARIANTS = frozenset({"NFL_DRAFT_THREE_STRIKES"})
STARTING_STRIKES = 3

# Real difficulty escalates by round position -- LOW for the first third
# of the run, MEDIUM for the middle third, HIGH after that. Reuses
# risk_it.py's own real _TIER_RANGES/_TIER_POINTS verbatim (same real
# draft_pick_overall proxy, same real point values per tier).
_TIER_SEQUENCE = ["LOW", "MEDIUM", "HIGH"]


def _tier_for_index(i: int, round_count: int) -> str:
    third = max(1, round_count // 3)
    return _TIER_SEQUENCE[min(i // third, len(_TIER_SEQUENCE) - 1)]


def safety_check(c) -> dict:
    return risk_it.safety_check(c)


def generate_rounds(seed: str, variant: str, round_count: int = 12) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        rows_by_tier_season: dict[str, dict[int, list]] = {}
        for tier, (lo, hi) in risk_it._TIER_RANGES.items():
            by_season: dict[int, list] = {}
            for r in risk_it._rows_for_tier(c, lo, hi):
                by_season.setdefault(r["draft_season"], []).append(r)
            rows_by_tier_season[tier] = by_season
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        tier = _tier_for_index(i, round_count)
        q = risk_it._build_tier_question(
            engine_bootstrap.seeded(f"{seed}-ts-r{i}-{tier}"), rows_by_tier_season[tier])
        if q is None:
            break
        rounds.append({"tier": tier, "points": risk_it._TIER_POINTS[tier], "prompt": q["prompt"],
                        "correct_team": q["correct_team"], "decoy_teams": q["decoy_teams"], "notes": q["notes"]})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real THREE_STRIKES rounds could be built with "
            f"a real, decoy-complete question; exported the maximum available rather than include a "
            f"fabricated or incomplete question."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_THREE_STRIKES": "Three Strikes"}


def build_package(seed: str, variant: str, round_count: int = 12) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP34:" + hashlib.sha256(
        f"THREE_STRIKES|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_team"]] + list(r["decoy_teams"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-ts-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "tier": r["tier"], "points": r["points"], "prompt": r["prompt"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Answer real questions of rising real difficulty -- a wrong answer costs a "
                              "strike. Survive 3 strikes and the run ends.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds), "starting_strikes": STARTING_STRIKES,
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
