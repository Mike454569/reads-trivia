"""Real-DB certification for Story Factory gameplay reach.

This does not deploy or expose anything. It executes the same package builders
used by Creator/internal gameplay and reports whether verified story-backed
content actually reaches each compatible game shell.
"""
from __future__ import annotations

import json
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v04 import (
    category_roulette,
    double_or_nothing,
    fact_or_fake,
    risk_it,
    strategy_arcade,
    three_strikes,
    wager_mode,
    drive_progression,
)
from tools.director_v02 import mechanic_engine
from tools.director_v05 import lore_package
from tools.director_v05.story_factory_health import story_factory_health


def _story_round_count(package):
    count = 0
    for r in package.get("rounds") or []:
        notes = str(r.get("_notes") or "")
        category = str(r.get("category") or "")
        if notes.startswith("Verified story-backed") or category == "Football Lore":
            count += 1
        tiers = r.get("tiers") or {}
        for tier in tiers.values():
            if str(tier.get("_notes") or "").startswith("Verified story-backed"):
                count += 1
    diag = package.get("_diagnostics") or {}
    for q in package.get("questions") or []:
        if str(q.get("id") or "").startswith(("qstory", "qlore")) and q.get("source") == "STORY_FACTORY":
            count += 1
    count = max(
        count,
        int(diag.get("story_rounds") or 0),
        int(diag.get("story_high_risk_rounds") or 0),
        int(diag.get("story_questions_used") or 0),
    )
    return count


def _run(name, fn):
    try:
        package = fn()
    except Exception as exc:
        return {
            "game": name,
            "status": "ERROR",
            "story_rounds": 0,
            "reason": type(exc).__name__ + ":" + str(exc),
        }
    story = _story_round_count(package)
    return {
        "game": name,
        "status": "PASSED" if package.get("qa_status") == "PASSED" else "FAILED",
        "story_rounds": story,
        "story_reached_game": story > 0,
        "round_count": int(package.get("round_count") or len(package.get("rounds") or [])),
        "shortfall_reason": package.get("shortfall_reason"),
    }


def certify_story_game_reach(*, seed="story-reach-cert"):
    c = engine_bootstrap.connect()
    try:
        health = story_factory_health(c)
    finally:
        c.close()

    cases = [
        ("Wager Mode", lambda: wager_mode.build_package(seed+"-wager", "WAGER_MODE_MIXED", round_count=9)),
        ("Category Roulette", lambda: category_roulette.build_package(seed+"-roulette", "CATEGORY_ROULETTE_MIXED", round_count=9)),
        ("Risk It NFL", lambda: risk_it.build_package(seed+"-risk-nfl", "NFL_DRAFT_RISK_IT", round_count=9)),
        ("Risk It CFB", lambda: risk_it.build_package(seed+"-risk-cfb", "CFB_SEASON_PASSING_RISK_IT", round_count=9)),
        ("Three Strikes NFL", lambda: three_strikes.build_package(seed+"-3s-nfl", "NFL_DRAFT_THREE_STRIKES", round_count=12)),
        ("Three Strikes CFB", lambda: three_strikes.build_package(seed+"-3s-cfb", "CFB_SEASON_PASSING_THREE_STRIKES", round_count=12)),
        ("Double or Nothing NFL", lambda: double_or_nothing.build_package(seed+"-don-nfl", "NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=9)),
        ("Double or Nothing CFB", lambda: double_or_nothing.build_package(seed+"-don-cfb", "CFB_SEASON_PASSING_DOUBLE_OR_NOTHING", round_count=9)),
        ("Fact or Fake NFL", lambda: fact_or_fake.build_package(seed+"-fof-nfl", "NFL_DRAFT_FACT_OR_FAKE", round_count=12)),
        ("Fact or Fake CFB", lambda: fact_or_fake.build_package(seed+"-fof-cfb", "CFB_GAME_RESULT_FACT_OR_FAKE", round_count=12)),
        ("Perfect Drive NFL", lambda: drive_progression.build_package(
            seed+"-drive-nfl", "NFL_DRAFT_PERFECT_DRIVE", mode="YARDAGE",
            question_pools=mechanic_engine.VARIANTS["DRIVE_PROGRESSION"]["NFL_DRAFT_PERFECT_DRIVE"]["question_pools"],
            question_count=12,
        )),
        ("Perfect Drive CFB", lambda: drive_progression.build_package(
            seed+"-drive-cfb", "CFB_HEISMAN_PERFECT_DRIVE", mode="YARDAGE",
            question_pools=mechanic_engine.VARIANTS["DRIVE_PROGRESSION"]["CFB_HEISMAN_PERFECT_DRIVE"]["question_pools"],
            question_count=12,
        )),
        ("Goal Line Stand NFL", lambda: drive_progression.build_package(
            seed+"-gls-nfl", "NFL_DRAFT_GOAL_LINE_STAND", mode="DOWNS",
            question_pools=mechanic_engine.VARIANTS["DRIVE_PROGRESSION"]["NFL_DRAFT_GOAL_LINE_STAND"]["question_pools"],
            question_count=12,
        )),
        ("Goal Line Stand CFB", lambda: drive_progression.build_package(
            seed+"-gls-cfb", "CFB_HEISMAN_GOAL_LINE_STAND", mode="DOWNS",
            question_pools=mechanic_engine.VARIANTS["DRIVE_PROGRESSION"]["CFB_HEISMAN_GOAL_LINE_STAND"]["question_pools"],
            question_count=12,
        )),
        ("Deep Lore", lambda: lore_package.build_package(
            seed=seed+"-deep-lore", target_count=9, difficulty="hard"
        )),
    ]

    # All Strategy Arcade variants share Category Roulette -> Deep Ball as
    # their real question source, so certify every actual registered variant.
    for variant in sorted(strategy_arcade.VARIANTS):
        cases.append((
            "Strategy Arcade / " + variant,
            lambda v=variant: strategy_arcade.build_package(
                seed+"-strategy-"+v.lower(), v, round_count=24
            ),
        ))

    results = [_run(name, fn) for name, fn in cases]
    reached = [r for r in results if r.get("story_reached_game")]
    errors = [r for r in results if r["status"] == "ERROR"]

    # An empty story question pool is a corpus readiness failure, not a code
    # reach failure. Report it distinctly so the real bottleneck is obvious.
    ready_questions = int(health.get("ready_for_bank") or 0)
    corpus_ready = ready_questions > 0

    return {
        "certification": "STORY_GAME_REACH",
        "corpus_ready": corpus_ready,
        "ready_story_questions": ready_questions,
        "games_tested": len(results),
        "games_with_story_content": len(reached),
        "reach_fraction": round(len(reached) / max(1, len(results)), 4),
        "errors": errors,
        "results": results,
        "factory_health": health,
        "promotion_ready": (
            corpus_ready
            and not errors
            and len(reached) >= max(8, len(results) // 2)
        ),
    }


def main():
    print(json.dumps(certify_story_game_reach(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
