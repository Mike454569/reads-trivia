"""HEAD_TO_HEAD_DUEL -- 15-Format Expansion Part 2, format #3.

Two real players shown side by side; the player taps whichever they think
has the higher real value on one real, verified statistical total. Reuses
the same real data sources and tie-avoidance discipline already
established by STAT_LADDER (tools/director_v04/sorting.py) -- the same 3
real stat categories, just compared pairwise (2 items) instead of ranked
(4-6 items).

Real data, 3 variants:
  - NFL_SEASON_RUSHING_YARDS_DUEL: 2 real NFL players' real rushing yards
    in the SAME real season (player_season_stats, NFLVERSE_DATA,
    SOURCE_BACKED).
  - NFL_CAREER_PASSING_TD_DUEL: 2 real NFL quarterbacks' real career
    passing touchdown totals (player_season_stats summed per player,
    restricted to a real QB roster season the same way STAT_LADDER's own
    career-passing-TD variant is, to avoid mislabeling a non-QB's
    incidental trick-play stat).
  - CFB_CAREER_RUSHING_YARDS_DUEL: 2 real CFB players' real career rushing
    yards (cfb_player_season_stats_real, SPORTSDATAVERSE_CFB,
    SOURCE_BACKED_DERIVED).

Every round is resampled until the two real values are genuinely distinct
-- a real tie is never silently broken or invented a winner for; same
discipline STAT_LADDER's own resampling already established.

Values are kept server-private until evaluate() runs (same discipline
every other mechanic's package uses) -- revealed to the player only in the
post-answer result, as real evidence for the real outcome.
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
MECHANIC = "PAIRWISE_COMPARE"
VARIANTS = frozenset({
    "NFL_SEASON_RUSHING_YARDS_DUEL", "NFL_CAREER_PASSING_TD_DUEL", "CFB_CAREER_RUSHING_YARDS_DUEL",
})

_PROMPTS = {
    "NFL_SEASON_RUSHING_YARDS_DUEL": "Who had more real rushing yards that season?",
    "NFL_CAREER_PASSING_TD_DUEL": "Who threw more real career passing touchdowns?",
    "CFB_CAREER_RUSHING_YARDS_DUEL": "Who has more real career rushing yards?",
}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "player_season_stats": safety.check_table_wide_safety(c, "player_season_stats", "NFLVERSE_DATA"),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED",
        ),
    }


def _nfl_season_rushing_yards_duel_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.season, s.player_key, p.display_name, s.rush_yards AS val FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' "
        "AND s.rush_yards IS NOT NULL AND s.rush_yards > 0"
    ).fetchall()
    by_season: dict[int, list] = {}
    for r in rows:
        by_season.setdefault(r["season"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    seasons = sorted(by_season.keys())
    rng.shuffle(seasons)

    rounds = []
    for season in seasons:
        if len(rounds) >= round_count:
            break
        players = by_season[season]
        if len(players) < 2:
            continue
        pair = None
        for _ in range(8):
            candidate = rng.sample(players, 2)
            if candidate[0]["val"] != candidate[1]["val"]:
                pair = candidate
                break
        if pair is None:
            continue  # this season's real draw kept tying -- resample, never invent a winner
        rounds.append({
            "variant": "NFL_SEASON_RUSHING_YARDS_DUEL", "season": season,
            "entity_a": {"label": pair[0]["display_name"], "value": pair[0]["val"],
                         "_audit": {"player_key": pair[0]["player_key"], "season": season}},
            "entity_b": {"label": pair[1]["display_name"], "value": pair[1]["val"],
                         "_audit": {"player_key": pair[1]["player_key"], "season": season}},
            "notes": f"Real {season} NFL rushing yards, NFLVERSE_DATA, SOURCE_BACKED.",
        })
    return rounds


def _nfl_career_passing_td_duel_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.player_key, p.display_name, SUM(s.pass_td) AS val FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' AND s.pass_td IS NOT NULL "
        "AND EXISTS (SELECT 1 FROM canonical_roster_seasons rs WHERE rs.player_id = s.player_key AND rs.position = 'QB') "
        "GROUP BY s.player_key HAVING val > 0"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    pool = list(rows)
    rng.shuffle(pool)

    rounds = []
    attempts = 0
    while len(rounds) < round_count and attempts < round_count * 10 and len(pool) >= 2:
        attempts += 1
        pair = rng.sample(pool, 2)
        if pair[0]["val"] == pair[1]["val"]:
            continue  # real quarterbacks who happen to share the exact same career total -- resample
        rounds.append({
            "variant": "NFL_CAREER_PASSING_TD_DUEL", "season": None,
            "entity_a": {"label": pair[0]["display_name"], "value": pair[0]["val"],
                         "_audit": {"player_key": pair[0]["player_key"]}},
            "entity_b": {"label": pair[1]["display_name"], "value": pair[1]["val"],
                         "_audit": {"player_key": pair[1]["player_key"]}},
            "notes": "Real career passing touchdown totals, summed from player_season_stats, "
                     "NFLVERSE_DATA, SOURCE_BACKED.",
        })
    return rounds


def _cfb_career_rushing_yards_duel_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.cfb_player_id, p.display_name, SUM(s.rushing_yards) AS val FROM cfb_player_season_stats_real s "
        "JOIN canonical_cfb_players p ON p.cfb_player_id = s.cfb_player_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED' AND s.rushing_yards IS NOT NULL "
        "GROUP BY s.cfb_player_id HAVING val > 0"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    pool = list(rows)
    rng.shuffle(pool)

    rounds = []
    attempts = 0
    while len(rounds) < round_count and attempts < round_count * 10 and len(pool) >= 2:
        attempts += 1
        pair = rng.sample(pool, 2)
        if pair[0]["val"] == pair[1]["val"]:
            continue
        rounds.append({
            "variant": "CFB_CAREER_RUSHING_YARDS_DUEL", "season": None,
            "entity_a": {"label": pair[0]["display_name"], "value": pair[0]["val"],
                         "_audit": {"cfb_player_id": pair[0]["cfb_player_id"]}},
            "entity_b": {"label": pair[1]["display_name"], "value": pair[1]["val"],
                         "_audit": {"cfb_player_id": pair[1]["cfb_player_id"]}},
            "notes": "Real career rushing yard totals, summed from cfb_player_season_stats_real, "
                     "SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED.",
        })
    return rounds


def generate_rounds(seed: str, variant: str, round_count: int = 5) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_SEASON_RUSHING_YARDS_DUEL":
            raw_rounds = _nfl_season_rushing_yards_duel_rounds(c, seed, round_count)
        elif variant == "NFL_CAREER_PASSING_TD_DUEL":
            raw_rounds = _nfl_career_passing_td_duel_rounds(c, seed, round_count)
        else:  # CFB_CAREER_RUSHING_YARDS_DUEL
            raw_rounds = _cfb_career_rushing_yards_duel_rounds(c, seed, round_count)
    finally:
        c.close()

    shortfall_reason = None
    if len(raw_rounds) < round_count:
        shortfall_reason = (
            f"Only {len(raw_rounds)} of {round_count} requested real HEAD_TO_HEAD_DUEL rounds could be built "
            f"for variant={variant!r} with two genuinely distinct real values each; exported the maximum "
            f"available rather than include a tied or fabricated winner."
        )
    return {"rounds": raw_rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {
    "NFL_SEASON_RUSHING_YARDS_DUEL": "Rushing Duel", "NFL_CAREER_PASSING_TD_DUEL": "Passing TD Duel",
    "CFB_CAREER_RUSHING_YARDS_DUEL": "CFB Rushing Duel",
}


def build_package(seed: str, variant: str, round_count: int = 5) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP18:" + hashlib.sha256(
        f"HEAD_TO_HEAD_DUEL|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        winner = "A" if r["entity_a"]["value"] > r["entity_b"]["value"] else "B"
        rounds.append({
            "round_index": i, "prompt": _PROMPTS[variant],
            "entity_a": {"entity_id": "A", "label": r["entity_a"]["label"]},
            "entity_b": {"entity_id": "B", "label": r["entity_b"]["label"]},
            # Real values kept server-private (_prefixed) until evaluate()
            # runs -- same discipline every other mechanic's package uses.
            "_answer": winner,
            "_value_a": r["entity_a"]["value"], "_value_b": r["entity_b"]["value"],
            "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Tap whichever real player you think has the higher real value -- "
                              "the real numbers are revealed once you answer.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
