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

A 4th variant, NFL_CAREER_QB_BEST_OF_SEVEN (format BEST_OF_SEVEN_DUEL,
15-Format Expansion Part 2, format #4), reuses this same PAIRWISE_COMPARE
taxonomy for a real multi-category duel: the SAME 2 real NFL quarterbacks
compared across up to 7 real distinct career totals (passing yards,
passing touchdowns, completions, attempts, interceptions thrown, rushing
yards, PPR fantasy points -- every real career column this Engine has for
a QB, honestly capped at however many exist, never padded to a fake 7th).
Any category where the two real quarterbacks are genuinely tied is
dropped entirely rather than assigned an invented winner -- pairs with
fewer than 3 real distinguishing categories left are rejected and
resampled. The real overall match outcome (who won more of the real
categories, or a genuine tie) is computed once at generation time from
real data alone -- independent of the player's own picks -- and revealed
as `_match_summary` only after the final round is answered.
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
    "NFL_CAREER_QB_BEST_OF_SEVEN",
})

_PROMPTS = {
    "NFL_SEASON_RUSHING_YARDS_DUEL": "Who had more real rushing yards that season?",
    "NFL_CAREER_PASSING_TD_DUEL": "Who threw more real career passing touchdowns?",
    "CFB_CAREER_RUSHING_YARDS_DUEL": "Who has more real career rushing yards?",
    # NFL_CAREER_QB_BEST_OF_SEVEN has no single fixed prompt -- each round
    # carries its own real category-specific prompt (see
    # _nfl_career_qb_best_of_seven_rounds), so this key is intentionally
    # absent here; build_package() falls back to a round's own "prompt".
}

# --- BEST_OF_SEVEN_DUEL (NFL_CAREER_QB_BEST_OF_SEVEN) -----------------------
# Every real career column this Engine has for a QB -- honestly capped at
# 7, never padded with an invented 8th. (col, human label) pairs.
_QB_CAREER_CATEGORIES = [
    ("pass_yards", "career passing yards"),
    ("pass_td", "career passing touchdowns"),
    ("pass_completions", "career pass completions"),
    ("pass_attempts", "career pass attempts"),
    ("pass_interceptions", "career interceptions thrown"),
    ("rush_yards", "career rushing yards"),
    ("fantasy_points_ppr", "career PPR fantasy points"),
]


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


def _nfl_career_qb_best_of_seven_rounds(c, seed: str) -> tuple[list[dict], dict | None]:
    # fantasy_points_ppr is a real float column -- ROUND(...,2) avoids
    # exposing raw SQLite float-summation artifacts (e.g. 1772.3400000000001)
    # as if they were exact data; every other category here is a real
    # integer total and needs no rounding.
    cols_sql = ", ".join(
        f"COALESCE(ROUND(SUM(s.{col}), 2), 0) AS {col}" if col == "fantasy_points_ppr"
        else f"COALESCE(SUM(s.{col}), 0) AS {col}"
        for col, _ in _QB_CAREER_CATEGORIES
    )
    rows = c.execute(
        f"SELECT s.player_key, p.display_name, {cols_sql} FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' "
        "AND EXISTS (SELECT 1 FROM canonical_roster_seasons rs WHERE rs.player_id = s.player_key AND rs.position = 'QB') "
        "GROUP BY s.player_key HAVING pass_yards > 0"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    pool = list(rows)
    rng.shuffle(pool)

    attempts = 0
    while attempts < 40 and len(pool) >= 2:
        attempts += 1
        a, b = rng.sample(pool, 2)
        # A real tie in a category (e.g. equal career interceptions) has no
        # real "who had more" answer -- dropped entirely, never assigned an
        # invented winner. Never resampled per-category (these are the same
        # 2 real quarterbacks' real totals -- there is nothing to resample);
        # instead the whole PAIR is rejected below if too many of its real
        # categories turn out tied.
        categories = [(col, label, a[col], b[col]) for col, label in _QB_CAREER_CATEGORIES if a[col] != b[col]]
        if len(categories) < 3:
            continue  # not enough real distinguishing categories for this real pair -- try another
        rounds = []
        for col, label, va, vb in categories:
            rounds.append({
                "prompt": f"Who had more real {label}?",
                "entity_a": {"label": a["display_name"], "value": va,
                             "_audit": {"player_key": a["player_key"], "category": col}},
                "entity_b": {"label": b["display_name"], "value": vb,
                             "_audit": {"player_key": b["player_key"], "category": col}},
                "notes": f"Real {label}, summed from player_season_stats, NFLVERSE_DATA, SOURCE_BACKED.",
            })
        wins_a = sum(1 for _, _, va, vb in categories if va > vb)
        wins_b = len(categories) - wins_a
        winner = "A" if wins_a > wins_b else ("B" if wins_b > wins_a else "TIE")
        match_summary = {
            "entity_a_label": a["display_name"], "entity_b_label": b["display_name"],
            "wins_a": wins_a, "wins_b": wins_b, "categories_played": len(categories), "winner": winner,
        }
        return rounds, match_summary
    return [], None


def generate_rounds(seed: str, variant: str, round_count: int = 5) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    match_summary = None
    try:
        safety_result = safety_check(c)
        if variant == "NFL_SEASON_RUSHING_YARDS_DUEL":
            raw_rounds = _nfl_season_rushing_yards_duel_rounds(c, seed, round_count)
        elif variant == "NFL_CAREER_PASSING_TD_DUEL":
            raw_rounds = _nfl_career_passing_td_duel_rounds(c, seed, round_count)
        elif variant == "CFB_CAREER_RUSHING_YARDS_DUEL":
            raw_rounds = _cfb_career_rushing_yards_duel_rounds(c, seed, round_count)
        else:  # NFL_CAREER_QB_BEST_OF_SEVEN -- round_count is ignored (governed
            # by however many real, genuinely distinct categories the chosen
            # real pair actually has, honestly capped at 7 -- see
            # _nfl_career_qb_best_of_seven_rounds).
            raw_rounds, match_summary = _nfl_career_qb_best_of_seven_rounds(c, seed)
    finally:
        c.close()

    min_expected = 3 if variant == "NFL_CAREER_QB_BEST_OF_SEVEN" else round_count
    shortfall_reason = None
    if len(raw_rounds) < min_expected:
        shortfall_reason = (
            f"Only {len(raw_rounds)} of {min_expected} required real PAIRWISE_COMPARE rounds could be built "
            f"for variant={variant!r} with genuinely distinct real values each; exported the maximum "
            f"available rather than include a tied or fabricated winner."
        )
    return {"rounds": raw_rounds, "safety": safety_result, "shortfall_reason": shortfall_reason,
            "match_summary": match_summary}


_GAME_TITLES = {
    "NFL_SEASON_RUSHING_YARDS_DUEL": "Rushing Duel", "NFL_CAREER_PASSING_TD_DUEL": "Passing TD Duel",
    "CFB_CAREER_RUSHING_YARDS_DUEL": "CFB Rushing Duel", "NFL_CAREER_QB_BEST_OF_SEVEN": "QB Best of Seven",
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
            "round_index": i, "prompt": r.get("prompt") or _PROMPTS.get(variant),
            "entity_a": {"entity_id": "A", "label": r["entity_a"]["label"]},
            "entity_b": {"entity_id": "B", "label": r["entity_b"]["label"]},
            # Real values kept server-private (_prefixed) until evaluate()
            # runs -- same discipline every other mechanic's package uses.
            "_answer": winner,
            "_value_a": r["entity_a"]["value"], "_value_b": r["entity_b"]["value"],
            "_notes": r["notes"],
        })

    is_best_of_seven = variant == "NFL_CAREER_QB_BEST_OF_SEVEN"
    package = {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": (
            "Tap whichever real quarterback you think had more in each real category -- most categories "
            "won takes the duel." if is_best_of_seven else
            "Tap whichever real player you think has the higher real value -- "
            "the real numbers are revealed once you answer."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
    if result.get("match_summary"):
        package["_match_summary"] = result["match_summary"]
    return package
