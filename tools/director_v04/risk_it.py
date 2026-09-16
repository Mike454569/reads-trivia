"""RISK_IT -- 15-Format Expansion Part 2, format #11.

Real risk-vs-reward trivia: before each round, the player picks a real
risk tier (LOW/MEDIUM/HIGH) sight-unseen -- before any question content
is revealed -- which sets both the real stakes (points on a correct
answer) and the real difficulty of the question drawn for that tier.

Difficulty is a real, verifiable proxy, never an invented rating: real
NFL Draft `draft_pick_overall` (draft_facts, NFLVERSE_DATA,
SOURCE_BACKED). An early real pick is a more famous, more recognizable
real player (LOW risk, picks 1-10, 1 point); a middling real pick is
less familiar (MEDIUM risk, picks 11-100, 2 points); a late real pick is
a genuinely obscure real player (HIGH risk, picks 101+, 3 points).

Domain: "which real NFL team drafted this real player" -- 4 real
multiple-choice options (the real correct team, plus 3 real decoy teams
that each really drafted a DIFFERENT real player in that exact same real
draft class -- every decoy is itself a real, verifiable fact, just not
the answer to this question).

A wrong answer at any tier costs one of the player's 3 real starting
lives; the run ends when lives reach 0 or after round_count rounds,
whichever comes first. Two-step interaction per round (choose a tier,
then answer that tier's real question) -- same real navigation-then-
leaf-question shape BRANCH_STATE already established, reused here rather
than inventing a second pattern for "commit before you see it."

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also"):
added CFB_SEASON_PASSING_RISK_IT. This pass's own earlier finding still
stands -- no real draft-style overall-pick ranking exists for CFB
players -- so a DIFFERENT real, verifiable recognizability proxy is used
instead: each real player's real rank on that season's real national
passing-yards leaderboard (rank 1 = that season's real national leader,
most recognizable; rank 40+ = a genuinely obscure real season, least
recognizable), computed with a real SQL window function over
cfb_player_season_stats_real +
cfb_roster_seasons_real.position='QB', never an invented rating. Domain
is "which real SCHOOL did this real player play for" (not "drafted by"
-- CFB players aren't drafted), decoys are 3 other real players' real
schools from that same real season.

Two variants: NFL_DRAFT_RISK_IT, CFB_SEASON_PASSING_RISK_IT.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "RISK_IT"
VARIANTS = frozenset({"NFL_DRAFT_RISK_IT", "CFB_SEASON_PASSING_RISK_IT"})
STARTING_LIVES = 3

_TIER_RANGES = {"LOW": (1, 10), "MEDIUM": (11, 100), "HIGH": (101, 300)}
_TIER_POINTS = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

# Real per-season national passing-yards RANK among real CFB QBs (1 =
# that season's real leader) stands in for draft_pick_overall's real
# recognizability proxy -- CFB has no draft-style pick number at all.
_CFB_TIER_RANGES = {"LOW": (1, 10), "MEDIUM": (11, 40), "HIGH": (41, 999)}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED"),
    }


def _rows_for_tier(c, lo: int, hi: int) -> list:
    return c.execute(
        "SELECT player_key, player_name, draft_season, draft_team, draft_pick_overall FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' "
        "AND draft_pick_overall BETWEEN ? AND ? AND draft_team IS NOT NULL",
        (lo, hi),
    ).fetchall()


def _rows_for_tier_cfb(c, lo: int, hi: int) -> list:
    return c.execute(
        "SELECT cfb_player_id AS player_key, player_name, season AS draft_season, school_name AS draft_team, "
        "rk AS draft_pick_overall FROM ("
        "  SELECT s.cfb_player_id, s.player_name, s.season, sc.school_name, "
        "  RANK() OVER (PARTITION BY s.season ORDER BY s.passing_yards DESC) AS rk "
        "  FROM cfb_player_season_stats_real s "
        "  JOIN cfb_roster_seasons_real rs ON rs.season=s.season AND rs.school_id=s.school_id "
        "  AND rs.cfb_player_id=s.cfb_player_id "
        "  JOIN schools sc ON sc.school_id = s.school_id "
        "  WHERE s.verification_status='SOURCE_BACKED_DERIVED' AND s.source_id='SPORTSDATAVERSE_CFB' "
        "  AND rs.position='QB' AND s.passing_yards >= 300"
        ") WHERE rk BETWEEN ? AND ?",
        (lo, hi),
    ).fetchall()


def _build_tier_question(rng, rows_by_season: dict) -> dict | None:
    seasons = list(rows_by_season.keys())
    if not seasons:
        return None
    rng.shuffle(seasons)
    for season in seasons:
        pool = rows_by_season[season]
        if len(pool) < 1:
            continue
        correct = rng.choice(pool)
        other_teams_pool = [r for r in pool if r["draft_team"] != correct["draft_team"]]
        if len(other_teams_pool) < 3:
            continue
        decoy_rows = rng.sample(other_teams_pool, 3)
        # Real decoy teams must themselves be genuinely distinct from each
        # other (never show the same real team twice as if it were 2
        # different options).
        decoy_teams = []
        seen = {correct["draft_team"]}
        for r in decoy_rows:
            if r["draft_team"] in seen:
                continue
            seen.add(r["draft_team"])
            decoy_teams.append(r["draft_team"])
        if len(decoy_teams) < 3:
            continue
        return {
            "prompt": f"Which real team drafted {correct['player_name']} in the {season} NFL Draft "
                      f"(pick #{correct['draft_pick_overall']})?",
            "correct_team": correct["draft_team"], "decoy_teams": decoy_teams[:3],
            "notes": f"Real {season} NFL Draft, pick #{correct['draft_pick_overall']}: "
                     f"{correct['player_name']} to {correct['draft_team']} (NFLVERSE_DATA, SOURCE_BACKED).",
        }
    return None


def _build_tier_question_cfb(rng, rows_by_season: dict) -> dict | None:
    seasons = list(rows_by_season.keys())
    if not seasons:
        return None
    rng.shuffle(seasons)
    for season in seasons:
        pool = rows_by_season[season]
        if len(pool) < 1:
            continue
        correct = rng.choice(pool)
        other_teams_pool = [r for r in pool if r["draft_team"] != correct["draft_team"]]
        if len(other_teams_pool) < 3:
            continue
        decoy_rows = rng.sample(other_teams_pool, 3)
        decoy_teams = []
        seen = {correct["draft_team"]}
        for r in decoy_rows:
            if r["draft_team"] in seen:
                continue
            seen.add(r["draft_team"])
            decoy_teams.append(r["draft_team"])
        if len(decoy_teams) < 3:
            continue
        return {
            "prompt": f"Which real school did {correct['player_name']} play for in the {season} season "
                      f"(real #{correct['draft_pick_overall']} in national passing yards that season)?",
            "correct_team": correct["draft_team"], "decoy_teams": decoy_teams[:3],
            "notes": f"Real {season} season, #{correct['draft_pick_overall']} in national passing yards: "
                     f"{correct['player_name']} at {correct['draft_team']} "
                     f"(SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED).",
        }
    return None


def generate_rounds(seed: str, variant: str, round_count: int = 7) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    is_cfb = variant == "CFB_SEASON_PASSING_RISK_IT"
    tier_ranges = _CFB_TIER_RANGES if is_cfb else _TIER_RANGES
    rows_for_tier = _rows_for_tier_cfb if is_cfb else _rows_for_tier
    build_tier_question = _build_tier_question_cfb if is_cfb else _build_tier_question

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        rows_by_tier_season: dict[str, dict[int, list]] = {}
        for tier, (lo, hi) in tier_ranges.items():
            by_season: dict[int, list] = {}
            for r in rows_for_tier(c, lo, hi):
                by_season.setdefault(r["draft_season"], []).append(r)
            rows_by_tier_season[tier] = by_season
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        tiers = {}
        ok = True
        for tier in ("LOW", "MEDIUM", "HIGH"):
            q = build_tier_question(engine_bootstrap.seeded(f"{seed}-r{i}-{tier}"), rows_by_tier_season[tier])
            if q is None:
                ok = False
                break
            tiers[tier] = q
        if not ok:
            continue
        rounds.append({"tiers": tiers})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real RISK_IT rounds could be built with a "
            f"real, decoy-complete question at all 3 real risk tiers; exported the maximum available "
            f"rather than include a tier with a fabricated or incomplete question."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_RISK_IT": "Risk It", "CFB_SEASON_PASSING_RISK_IT": "Risk It (CFB)"}


def build_package(seed: str, variant: str, round_count: int = 7) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP23:" + hashlib.sha256(
        f"RISK_IT|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        tiers = {}
        for tier, q in r["tiers"].items():
            candidates = [q["correct_team"]] + list(q["decoy_teams"])
            order = list(range(4))
            engine_bootstrap.seeded(f"{seed}-shuffle-{i}-{tier}").shuffle(order)
            item_ids = ["A", "B", "C", "D"]
            options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
            correct_pos = order.index(0)
            tiers[tier] = {
                "points": _TIER_POINTS[tier], "prompt": q["prompt"], "options": options,
                "_answer_item_id": item_ids[correct_pos], "_notes": q["notes"],
            }
        rounds.append({"round_index": i, "tiers": tiers})

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Pick a real risk tier before you see the question -- LOW is easier and worth "
                              "less, HIGH is a real obscure " + ("season" if variant == "CFB_SEASON_PASSING_RISK_IT" else "pick")
                              + " worth more. A wrong answer costs a life.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds), "starting_lives": STARTING_LIVES,
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
