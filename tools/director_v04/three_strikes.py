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

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also").
Added CFB_SEASON_PASSING_THREE_STRIKES, reusing risk_it.py's own new real
CFB tiering (per-season national passing-yards rank, "which real school"
question) verbatim -- see risk_it.py's own module docstring for why this
proxy replaces draft_pick_overall for CFB.

Category variety pass (user feedback: "we don't need game modes based on
draft picks"). NFL_DRAFT_THREE_STRIKES now also draws, per round, from
risk_it.py's new real SEASON_PASSING category (real per-season national
passing-yards rank among real NFL QBs, "which real team did this player
play for" -- see risk_it.py's own module docstring). Which category a
given round uses is itself seeded/deterministic.

Two variants: NFL_DRAFT_THREE_STRIKES, CFB_SEASON_PASSING_THREE_STRIKES.
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
VARIANTS = frozenset({"NFL_DRAFT_THREE_STRIKES", "CFB_SEASON_PASSING_THREE_STRIKES"})
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

    is_cfb = variant == "CFB_SEASON_PASSING_THREE_STRIKES"
    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if is_cfb:
            category_data = {"CFB": (risk_it._build_rows_by_tier_season(c, risk_it._CFB_TIER_RANGES,
                                                                          risk_it._rows_for_tier_cfb),
                                      risk_it._build_tier_question_cfb)}
        else:
            category_data = {
                "DRAFT": (risk_it._build_rows_by_tier_season(c, risk_it._TIER_RANGES, risk_it._rows_for_tier),
                          risk_it._build_tier_question),
                "SEASON_PASSING": (risk_it._build_rows_by_tier_season(c, risk_it._NFL_PASSING_TIER_RANGES,
                                                                       risk_it._rows_for_tier_nfl_passing),
                                    risk_it._build_tier_question_nfl_passing),
            }
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        tier = _tier_for_index(i, round_count)
        if is_cfb:
            candidates = ["CFB"]
        else:
            cat_rng = engine_bootstrap.seeded(f"{seed}-ts-cat-{i}")
            candidates = list(risk_it._NFL_CATEGORIES)
            cat_rng.shuffle(candidates)
        q = None
        for category in candidates:
            rows_by_tier_season, build_tier_question = category_data[category]
            q = build_tier_question(engine_bootstrap.seeded(f"{seed}-ts-r{i}-{tier}-{category}"),
                                     rows_by_tier_season[tier])
            if q is not None:
                break
        if q is None:
            break
        points = risk_it._TIER_POINTS[tier]
        rounds.append({"tier": tier, "points": points, "prompt": q["prompt"],
                        "correct_team": q["correct_team"], "decoy_teams": q["decoy_teams"], "notes": q["notes"]})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real THREE_STRIKES rounds could be built with "
            f"a real, decoy-complete question; exported the maximum available rather than include a "
            f"fabricated or incomplete question."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_THREE_STRIKES": "Three Strikes", "CFB_SEASON_PASSING_THREE_STRIKES": "Three Strikes (CFB)"}


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
