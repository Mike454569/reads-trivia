"""DRAFT_PICK_LADDER -- 75-Format Expansion (Wave 1), format #34 overall.

Real escalating pick-number identification: each round names a real
player and their real draft season, and asks the player to identify
their real overall draft pick number -- 4 multiple-choice options, the
real correct pick plus 3 real decoy picks that really belong to other
players drafted that SAME real season (never a fabricated pick number).
Real difficulty escalates by round position (reusing risk_it.py's own
real draft_pick_overall tiers): early rounds ask about real early, more
memorable picks; later rounds ask about real, more obscure late picks.

Deliberately distinct from every other draft_facts-based format this
pass: RISK_IT/THREE_STRIKES/DOUBLE_OR_NOTHING ask "which real TEAM
drafted this player" (team identification); FACT_OR_FAKE/REVERSE_TRIVIA
ask true/false or which-statement-is-true about a full draft fact.
DRAFT_PICK_LADDER is the only one asking the player to identify a real
NUMBER (the pick slot itself), matching the user's own spec example
("easy: No. 1 overall... later: Pick 117").

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also")
reviewed this format and honestly did NOT add a CFB variant: the entire
mechanic identifies a real NFL DRAFT PICK NUMBER, a concept that has no
meaning for a college player who was never drafted at all (the NFL Draft
happens only after a player leaves college). Every other draft_facts-
based format in this pass (RISK_IT/THREE_STRIKES/DOUBLE_OR_NOTHING/
FACT_OR_FAKE/REVERSE_TRIVIA/COMMON_LINK) had a genuine non-draft real CFB
substitute available; this one's whole premise is the pick number itself,
so no honest substitute exists -- matching risk_it.py's own earlier
precedent of declining rather than forcing a fabricated analog.

Single variant: NFL_DRAFT_PICK_LADDER.
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
MECHANIC = "DRAFT_PICK_LADDER"
VARIANTS = frozenset({"NFL_DRAFT_PICK_LADDER"})

_TIER_SEQUENCE = ["LOW", "MEDIUM", "HIGH"]


def _tier_for_index(i: int, round_count: int) -> str:
    third = max(1, round_count // 3)
    return _TIER_SEQUENCE[min(i // third, len(_TIER_SEQUENCE) - 1)]


def safety_check(c) -> dict:
    return risk_it.safety_check(c)


def _build_round(rng, rows_by_season: dict[int, list]) -> dict | None:
    seasons = list(rows_by_season.keys())
    rng.shuffle(seasons)
    for season in seasons:
        pool = rows_by_season[season]
        if len(pool) < 4:
            continue
        subject = rng.choice(pool)
        decoy_pool = [r for r in pool if r["draft_pick_overall"] != subject["draft_pick_overall"]]
        if len(decoy_pool) < 3:
            continue
        decoys = rng.sample(decoy_pool, 3)
        return {"player_name": subject["player_name"], "season": season,
                "correct_pick": subject["draft_pick_overall"],
                "decoy_picks": [d["draft_pick_overall"] for d in decoys],
                "notes": f"{subject['player_name']} was really pick #{subject['draft_pick_overall']} in the "
                         f"{season} NFL Draft (NFLVERSE_DATA, SOURCE_BACKED)."}
    return None


def generate_rounds(seed: str, variant: str, round_count: int = 9) -> dict:
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
        r = _build_round(engine_bootstrap.seeded(f"{seed}-dpl-r{i}-{tier}"), rows_by_tier_season[tier])
        if r is None:
            continue
        r["tier"] = tier
        rounds.append(r)

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real DRAFT_PICK_LADDER rounds could be built "
            f"with a real, decoy-complete pick set; exported the maximum available rather than include a "
            f"fabricated pick number."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_PICK_LADDER": "Draft Pick Ladder"}


def build_package(seed: str, variant: str, round_count: int = 9) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP36:" + hashlib.sha256(
        f"DRAFT_PICK_LADDER|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_pick"]] + list(r["decoy_picks"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-dpl-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": f"Pick #{candidates[src]}"} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "tier": r["tier"], "player_name": r["player_name"], "season": r["season"],
            "options": options, "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "A real player and their real draft season are named -- tap the real overall "
                              "pick number they were drafted with.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
