"""CATEGORY_ROULETTE -- 75-Format Expansion (Wave 1), format #35 overall.

Real random-category trivia: each round's real category (NFL Draft,
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
from tools.director_v04 import wager_mode  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "CATEGORY_ROULETTE"
VARIANTS = frozenset({"CATEGORY_ROULETTE_MIXED"})


def safety_check(c) -> dict:
    return wager_mode.safety_check(c)


def generate_rounds(seed: str, variant: str, round_count: int = 6) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        draft_rows = c.execute(
            "SELECT player_key, player_name, draft_season, draft_team FROM draft_facts "
            "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' AND draft_team IS NOT NULL"
        ).fetchall()
        draft_by_season: dict[int, list] = {}
        for r in draft_rows:
            draft_by_season.setdefault(r["draft_season"], []).append(r)
        heisman_rows = c.execute(
            "SELECT award_year, player_name, school_name FROM cfb_award_facts "
            "WHERE verification_status='SOURCE_BACKED_FROM_CFB_MASTER' AND award_name='Heisman Trophy' "
            "AND player_name IS NOT NULL"
        ).fetchall()
        sb_rows = c.execute(
            "SELECT season, winner_name_raw FROM nfl_championship_events WHERE winner_team_code IS NOT NULL"
        ).fetchall()
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        cat = wager_mode._CATEGORIES[i % len(wager_mode._CATEGORIES)]
        cat_rng = engine_bootstrap.seeded(f"{seed}-cr-r{i}")
        if cat == "NFL Draft":
            q = wager_mode._nfl_draft_question(cat_rng, draft_by_season)
        elif cat == "Heisman Winners":
            q = wager_mode._heisman_question(cat_rng, heisman_rows)
        else:
            q = wager_mode._super_bowl_question(cat_rng, sb_rows)
        if q is None:
            continue
        rounds.append({"category": cat, **q})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real CATEGORY_ROULETTE rounds could be built "
            f"with a real, decoy-complete question; exported the maximum available rather than include a "
            f"fabricated or incomplete question."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


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
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-cr-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "category": r["category"], "prompt": r["prompt"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Each round's real category is shown immediately -- read the real question "
                              "and tap the correct real answer.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
