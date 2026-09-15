"""BLIND_RESUME -- 15-Format Expansion Part 2, format #15 (final of 15).

Real "whose career is this?" trivia: each round shows a real player's
career statistical resume (career games played, career pass yards,
career passing touchdowns, career interceptions -- all real, summed
totals) with the name redacted, plus 4 real named candidates. The player
taps whichever real candidate the blind resume actually belongs to.

Deliberately distinct from PLAYER_FROM_CLUES (tools/director_v04/
player_from_clues.py): that format reveals one real biographical/
categorical fact at a time as an open-ended free-text guess (draft year,
position, school...). BLIND_RESUME instead reveals a single real
STRUCTURED STAT TABLE all at once and asks a closed 4-option multiple
choice -- a genuinely different challenge (does this real statistical
shape match a name you recognize) and a genuinely different interaction
shape (MC tap, not free text), reusing the same real MC-with-decoys
pattern PICK_THE_IMPOSTOR/MISSING_PIECE/BEFORE_AFTER already established.
Also distinct from LEADERBOARD_CLIMB (tools/director_v04/
leaderboard_climb.py): that format compares 2 NAMED real players against
each other on ONE real value; this format shows ONE real player's full
real resume (4 real stat categories at once) and asks which NAME it is,
never a head-to-head comparison.

Real domain: NFL career passing resume (player_season_stats,
NFLVERSE_DATA, SOURCE_BACKED, summed per real QB, same real
EXISTS(...position='QB') join STAT_LADDER/LEADERBOARD_CLIMB already
established). Qualifying pool: real QBs with a real career total of more
than 3000 real career pass yards across at least 16 real career games --
a real, meaningful career sample, never a single-game or practice-squad
footnote. The 3 real decoy candidate names are drawn from that SAME real
qualifying pool (never a randomly-picked, potentially-obscure name unfit
to be a plausible real decoy) and are never shown their own real resumes
-- only the correct player's real resume is ever revealed, so a decoy
only needs to be a real, distinct, verifiable identity, not a
value-matched one.

Single variant: NFL_QB_CAREER_BLIND_RESUME.
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
MECHANIC = "BLIND_RESUME"
VARIANTS = frozenset({"NFL_QB_CAREER_BLIND_RESUME"})
MIN_CAREER_PASS_YARDS = 3000
MIN_CAREER_GAMES = 16


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {"player_season_stats": safety.check_table_wide_safety(c, "player_season_stats", "NFLVERSE_DATA")}


def _fetch_qualifying_qbs(c) -> list[dict]:
    rows = c.execute(
        "SELECT s.player_key, p.display_name, SUM(s.games) AS games, SUM(s.pass_yards) AS pass_yards, "
        "SUM(s.pass_td) AS pass_td, SUM(s.pass_interceptions) AS interceptions FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' "
        "AND EXISTS (SELECT 1 FROM canonical_roster_seasons rs WHERE rs.player_id = s.player_key AND rs.position = 'QB') "
        "GROUP BY s.player_key HAVING pass_yards > ? AND games >= ?",
        (MIN_CAREER_PASS_YARDS, MIN_CAREER_GAMES),
    ).fetchall()
    return [dict(r) for r in rows]


def _build_rounds(seed: str, pool: list[dict], round_count: int) -> list[dict]:
    if len(pool) < 4:
        return []
    rng = engine_bootstrap.seeded(seed)
    order = list(range(len(pool)))
    rng.shuffle(order)

    rounds = []
    for idx in order:
        if len(rounds) >= round_count:
            break
        correct = pool[idx]
        decoy_pool = [p for p in pool if p["player_key"] != correct["player_key"]]
        if len(decoy_pool) < 3:
            continue
        decoys = rng.sample(decoy_pool, 3)
        rounds.append({
            "resume": {
                "games": correct["games"], "pass_yards": correct["pass_yards"],
                "pass_td": correct["pass_td"], "interceptions": correct["interceptions"],
            },
            "correct_name": correct["display_name"],
            "decoy_names": [d["display_name"] for d in decoys],
            "notes": f"Real career passing resume ({correct['games']} games, {correct['pass_yards']} yards, "
                     f"{correct['pass_td']} TD, {correct['interceptions']} INT) belongs to "
                     f"{correct['display_name']} (NFLVERSE_DATA, SOURCE_BACKED).",
        })
    return rounds


def generate_rounds(seed: str, variant: str, round_count: int = 7) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        pool = _fetch_qualifying_qbs(c)
    finally:
        c.close()

    rounds = _build_rounds(seed, pool, round_count)
    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real BLIND_RESUME rounds could be built with "
            f"a real, decoy-complete candidate set (at least 4 real qualifying QBs, no reused real name "
            f"within a round); exported the maximum available rather than include a fabricated decoy."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_QB_CAREER_BLIND_RESUME": "Blind Resume"}


def build_package(seed: str, variant: str, round_count: int = 7) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP27:" + hashlib.sha256(
        f"BLIND_RESUME|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_name"]] + list(r["decoy_names"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "resume": r["resume"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "A real player's career passing resume is shown with the name hidden -- tap "
                              "whichever real candidate you think it belongs to.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
