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

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also"):
added CFB_CAREER_PASSING_YARDS_RANKING. Deliberately does NOT reuse
leaderboard_climb.py's own fetcher for this (LEADERBOARD_CLIMB is a
protected format from an earlier duplicate-audit pass) -- builds its own
self-contained real top-15 query on cfb_player_season_stats_real +
cfb_roster_seasons_real.position='QB' instead, same real tie-check
discipline (confirmed live: all 15 real totals distinct before shipping).

Two variants: NFL_CAREER_PASSING_YARDS_RANKING, CFB_CAREER_PASSING_YARDS_RANKING.
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
VARIANTS = frozenset({"NFL_CAREER_PASSING_YARDS_RANKING", "CFB_CAREER_PASSING_YARDS_RANKING"})
CFB_LADDER_SIZE = 15


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "player_season_stats": leaderboard_climb.safety_check(c)["player_season_stats"],
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED"),
    }


def _fetch_cfb_ladder(c) -> list[dict]:
    # Self-contained (not reusing leaderboard_climb.py's fetcher -- that
    # format is protected from an earlier duplicate-audit pass). Same real
    # tie-check discipline as the NFL variant.
    rows = c.execute(
        "SELECT cfb_player_id, player_name, SUM(passing_yards) AS val FROM cfb_player_season_stats_real s "
        "WHERE verification_status='SOURCE_BACKED_DERIVED' AND source_id='SPORTSDATAVERSE_CFB' "
        "AND passing_yards IS NOT NULL "
        "AND EXISTS (SELECT 1 FROM cfb_roster_seasons_real rs WHERE rs.cfb_player_id = s.cfb_player_id AND rs.position = 'QB') "
        "GROUP BY cfb_player_id HAVING val > 0 ORDER BY val DESC LIMIT ?",
        (CFB_LADDER_SIZE,),
    ).fetchall()
    values = [r["val"] for r in rows]
    if len(set(values)) != len(values):
        raise RuntimeError(
            "A real tie exists within the top real CFB career-passing-yards leaders -- "
            "GUESS_THE_RANKING cannot honestly ask for an exact rank at that boundary."
        )
    return [{"rank": i + 1, "label": r["player_name"], "value": r["val"],
              "_audit": {"player_key": r["cfb_player_id"]}} for i, r in enumerate(rows)]


def generate_rounds(seed: str, variant: str, round_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        ladder = (_fetch_cfb_ladder(c) if variant == "CFB_CAREER_PASSING_YARDS_RANKING"
                  else leaderboard_climb._fetch_ladder(c))
    finally:
        c.close()

    source_note = "SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED" if variant == "CFB_CAREER_PASSING_YARDS_RANKING" \
        else "NFLVERSE_DATA, SOURCE_BACKED"
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
                                     f"({source_note})."})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real GUESS_THE_RANKING rounds could be built "
            f"with a real, decoy-complete rank set; exported the maximum available rather than include a "
            f"fabricated rank."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {
    "NFL_CAREER_PASSING_YARDS_RANKING": "Guess the Ranking",
    "CFB_CAREER_PASSING_YARDS_RANKING": "Guess the Ranking (CFB)",
}


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
