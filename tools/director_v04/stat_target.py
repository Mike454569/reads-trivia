"""STAT_TARGET -- 75-Format Expansion (Wave 1), format #30 overall.

Real target-proximity trivia: each round shows a real target number (a
plausible round rushing-yards figure, e.g. "1,500 rushing yards") and 4
real candidate players -- each with a real single-season rushing total
(player_season_stats, NFLVERSE_DATA, SOURCE_BACKED). The player taps
whichever real candidate's real season total is CLOSEST to the target.
The target itself is just a reference number (never claimed to be any
specific player's real total); every candidate's real value is genuine,
and "closest" is always computed as a real, unambiguous distance (no two
real candidates in a round are ever equidistant from the target).

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also"):
added CFB_SEASON_RUSHING_YARDS_TARGET, built on cfb_player_season_stats_real
(78,651 rows, SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED, 2014-2025) --
6,518 real candidates with rushing_yards > 200, real max 2,599. Same
target ladder as the NFL variant (a real, plausible round-number range for
both leagues, not re-derived per league). player_name is already a direct
column on this table (no join needed, unlike the NFL variant's
player_season_stats + canonical_players join).
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
MECHANIC = "STAT_TARGET"
VARIANTS = frozenset({"NFL_SEASON_RUSHING_YARDS_TARGET", "CFB_SEASON_RUSHING_YARDS_TARGET"})
MIN_RUSH_YARDS = 200
_TARGETS = [800, 1000, 1200, 1500, 1800, 2000]


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "player_season_stats": safety.check_table_wide_safety(c, "player_season_stats", "NFLVERSE_DATA"),
        # check_table_wide_safety() is hardcoded to require exactly
        # verification_status='SOURCE_BACKED' -- cfb_player_season_stats_real
        # genuinely uses 'SOURCE_BACKED_DERIVED' instead (confirmed directly
        # against the real schema), so check_verification_status_safety()
        # (which takes the expected status value explicitly) is the correct
        # function here, not a weaker check.
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED"),
    }


def _fetch_pool(c, variant: str) -> list[dict]:
    if variant == "CFB_SEASON_RUSHING_YARDS_TARGET":
        rows = c.execute(
            "SELECT cfb_player_id, player_name, season, rushing_yards FROM cfb_player_season_stats_real "
            "WHERE verification_status='SOURCE_BACKED_DERIVED' AND source_id='SPORTSDATAVERSE_CFB' "
            "AND rushing_yards > ?",
            (MIN_RUSH_YARDS,),
        ).fetchall()
        return [{"label": f"{r['player_name']} ({r['season']})", "value": r["rushing_yards"],
                  "_audit": {"player_key": r["cfb_player_id"], "season": r["season"]}} for r in rows]
    rows = c.execute(
        "SELECT s.player_key, p.display_name, s.season, s.rush_yards FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' "
        "AND s.rush_yards > ?",
        (MIN_RUSH_YARDS,),
    ).fetchall()
    return [{"label": f"{r['display_name']} ({r['season']})", "value": r["rush_yards"],
              "_audit": {"player_key": r["player_key"], "season": r["season"]}} for r in rows]


def _build_round(rng, pool: list[dict], target: int) -> dict | None:
    if len(pool) < 4:
        return None
    candidates = rng.sample(pool, 4)
    distances = [abs(c["value"] - target) for c in candidates]
    if len(set(distances)) != len(distances):
        return None  # a genuine distance tie -- never guess a tiebreak, try another draw
    correct_idx = distances.index(min(distances))
    return {"target": target, "candidates": candidates, "correct_index": correct_idx}


def generate_rounds(seed: str, variant: str, round_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        pool = _fetch_pool(c, variant)
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        target = _TARGETS[i % len(_TARGETS)]
        r = None
        for attempt in range(10):
            r = _build_round(engine_bootstrap.seeded(f"{seed}-st-r{i}-{attempt}"), pool, target)
            if r is not None:
                break
        if r is None:
            continue
        rounds.append(r)

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real STAT_TARGET rounds could be built with a "
            f"real, unambiguous (no-tie) closest candidate; exported the maximum available rather than "
            f"invent a tiebreak."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {
    "NFL_SEASON_RUSHING_YARDS_TARGET": "Stat Target",
    "CFB_SEASON_RUSHING_YARDS_TARGET": "Stat Target (CFB)",
}
_SOURCE_NOTE = {
    "NFL_SEASON_RUSHING_YARDS_TARGET": "NFLVERSE_DATA, SOURCE_BACKED",
    "CFB_SEASON_RUSHING_YARDS_TARGET": "SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED",
}


def build_package(seed: str, variant: str, round_count: int = 8) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP32:" + hashlib.sha256(
        f"STAT_TARGET|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-st-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": r["candidates"][src]["label"]}
                   for pos, src in enumerate(order)]
        correct_pos = order.index(r["correct_index"])
        correct_candidate = r["candidates"][r["correct_index"]]
        rounds.append({
            "round_index": i, "target": r["target"], "options": options,
            "_answer_item_id": item_ids[correct_pos],
            "_notes": f"{correct_candidate['label']} really had {correct_candidate['value']} real rushing "
                      f"yards that season -- closest to the {r['target']}-yard target "
                      f"({_SOURCE_NOTE[variant]}).",
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "A real target rushing-yards number is shown -- tap whichever real player's "
                              "real single-season total came closest to it.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
