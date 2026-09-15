"""GUESS_THE_RANKING -- 75-Format Expansion (Wave 1), format #29 overall.

Real ranking-identification trivia: each round names one real player from
a real, fixed, pre-sorted leaderboard (career passing yards, within this
Engine's real covered seasons) and asks the player to identify that
player's real rank on that leaderboard -- 4 multiple-choice options, the
real correct rank plus 3 other real ranks that really belong to other
real players on the same leaderboard (never a fabricated or out-of-range
rank).

Reuses tools.director_v04.leaderboard_climb's own real, already-
certified top-15 career-passing-yards query (_fetch_ladder) verbatim --
same real data, same real tie-check discipline, new rules only.

Deliberately distinct from LEADERBOARD_CLIMB (protected, 15-Format
Expansion): that format is a sequential climb comparing ADJACENT real
players two at a time, never revealing a rank NUMBER at all until the
climb ends. GUESS_THE_RANKING never compares two players against each
other -- it names ONE real player and asks for their real rank directly,
a genuinely different recall/estimation challenge (do you know exactly
where a player stands), with no climb, no persistent state, and no
elimination-on-miss at all (a plain single-shot round, closer in shape
to PICK_THE_IMPOSTOR/MISSING_PIECE than to LEADERBOARD_CLIMB).

Single variant: NFL_CAREER_PASSING_YARDS_RANKING.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import leaderboard_climb  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "GUESS_THE_RANKING"
VARIANTS = frozenset({"NFL_CAREER_PASSING_YARDS_RANKING"})


def safety_check(c) -> dict:
    return {"player_season_stats": leaderboard_climb.safety_check(c)["player_season_stats"]}


def generate_rounds(seed: str, variant: str, round_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        ladder = leaderboard_climb._fetch_ladder(c)
    finally:
        c.close()

    rounds = []
    if len(ladder) >= 4:
        rng = engine_bootstrap.seeded(seed)
        order = list(range(len(ladder)))
        rng.shuffle(order)
        for idx in order:
            if len(rounds) >= round_count:
                break
            subject = ladder[idx]
            decoy_pool = [r for r in ladder if r["rank"] != subject["rank"]]
            decoys = engine_bootstrap.seeded(f"{seed}-gtr-decoys-{idx}").sample(decoy_pool, min(3, len(decoy_pool)))
            if len(decoys) < 3:
                continue
            rounds.append({"label": subject["label"], "correct_rank": subject["rank"],
                            "decoy_ranks": [d["rank"] for d in decoys],
                            "notes": f"{subject['label']} really ranks #{subject['rank']} on this real "
                                     f"career-passing-yards leaderboard ({subject['value']} real yards) "
                                     f"(NFLVERSE_DATA, SOURCE_BACKED)."})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real GUESS_THE_RANKING rounds could be built "
            f"with a real, decoy-complete rank set; exported the maximum available rather than include a "
            f"fabricated rank."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_CAREER_PASSING_YARDS_RANKING": "Guess the Ranking"}


def build_package(seed: str, variant: str, round_count: int = 8) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP31:" + hashlib.sha256(
        f"GUESS_THE_RANKING|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_rank"]] + list(r["decoy_ranks"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-gtr-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": f"#{candidates[src]}"} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "label": r["label"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "A real player is named -- tap the real rank you think they hold on this real "
                              "career leaderboard.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
