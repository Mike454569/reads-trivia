"""DOUBLE_OR_NOTHING -- 75-Format Expansion (Wave 1), format #26 overall.

Real bank-or-risk escalation: the player answers a sequence of real
questions of increasing real difficulty (reusing risk_it.py's own real
draft_pick_overall difficulty proxy and its real 4-option decoy-building
logic verbatim, rather than a second, possibly-diverging copy of that
data/decoy logic). The first correct answer banks a real fictional base
of 100 points; every SUBSEQUENT correct answer DOUBLES the current
points. After any correct answer, the player may either bank (end the
run, keep the points) or answer the next, harder question (risk it all
on doubling again). A single wrong answer loses everything -- no lives,
no partial credit, unlike RISK_IT's 3-life budget.

Deliberately distinct from RISK_IT (protected, 15-Format Expansion):
RISK_IT commits to a risk TIER blind (before seeing the question), earns
a small FIXED point value per tier, survives up to 2 wrong answers (3
starting lives) across MANY independent rounds. DOUBLE_OR_NOTHING never
hides the question, has no lives at all (one miss ends the run), and
its whole point is the explicit "bank now or double again" decision
after every single correct answer -- a real, distinct psychological/
strategic choice RISK_IT's tier-commit-then-forget shape never poses.

Reuses tools.director_v04.risk_it's real, already-certified draft_facts
question-building (_rows_for_tier/_build_tier_question) and safety_check
verbatim -- same real data, same real decoy discipline, new rules only.

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also").
Added CFB_SEASON_PASSING_DOUBLE_OR_NOTHING, reusing risk_it.py's own new
real CFB tiering (per-season national passing-yards rank, "which real
school" question) verbatim -- see risk_it.py's own module docstring for
why this proxy replaces draft_pick_overall for CFB.

Category variety pass (user feedback: "we don't need game modes based on
draft picks"). NFL_DRAFT_DOUBLE_OR_NOTHING now also draws, per round,
from risk_it.py's new real SEASON_PASSING category (real per-season
national passing-yards rank among real NFL QBs, "which real team did
this player play for" -- see risk_it.py's own module docstring). Which
category a given round uses is itself seeded/deterministic.

Two variants: NFL_DRAFT_DOUBLE_OR_NOTHING, CFB_SEASON_PASSING_DOUBLE_OR_NOTHING.
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
MECHANIC = "DOUBLE_OR_NOTHING"
VARIANTS = frozenset({"NFL_DRAFT_DOUBLE_OR_NOTHING", "CFB_SEASON_PASSING_DOUBLE_OR_NOTHING"})
BASE_POINTS = 100

# Tier escalates LOW -> MEDIUM -> HIGH then stays at HIGH (only 3 real
# tiers exist -- risk_it.py's own real draft_pick_overall ranges).
_TIER_SEQUENCE = ["LOW", "MEDIUM", "HIGH"]


def _tier_for_index(i: int) -> str:
    return _TIER_SEQUENCE[min(i, len(_TIER_SEQUENCE) - 1)]


def safety_check(c) -> dict:
    return risk_it.safety_check(c)


def generate_rounds(seed: str, variant: str, round_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    is_cfb = variant == "CFB_SEASON_PASSING_DOUBLE_OR_NOTHING"
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
        tier = _tier_for_index(i)
        if is_cfb:
            candidates = ["CFB"]
        else:
            cat_rng = engine_bootstrap.seeded(f"{seed}-don-cat-{i}")
            candidates = list(risk_it._NFL_CATEGORIES)
            cat_rng.shuffle(candidates)
        q = None
        for category in candidates:
            rows_by_tier_season, build_tier_question = category_data[category]
            q = build_tier_question(engine_bootstrap.seeded(f"{seed}-don-r{i}-{tier}-{category}"),
                                     rows_by_tier_season[tier])
            if q is not None:
                break
        if q is None:
            break
        rounds.append({"tier": tier, "prompt": q["prompt"], "correct_team": q["correct_team"],
                        "decoy_teams": q["decoy_teams"], "notes": q["notes"]})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real DOUBLE_OR_NOTHING rounds could be built "
            f"with a real, decoy-complete question; exported the maximum available rather than include a "
            f"fabricated or incomplete question."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_DOUBLE_OR_NOTHING": "Double or Nothing", "CFB_SEASON_PASSING_DOUBLE_OR_NOTHING": "Double or Nothing (CFB)"}


def build_package(seed: str, variant: str, round_count: int = 8) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP28:" + hashlib.sha256(
        f"DOUBLE_OR_NOTHING|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_team"]] + list(r["decoy_teams"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-don-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "tier": r["tier"], "prompt": r["prompt"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Answer the real question -- a correct answer banks or doubles your real "
                              "fictional points. After every correct answer, bank your points or risk them "
                              "all on the next, harder real question. One wrong answer loses everything.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds), "base_points": BASE_POINTS,
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
