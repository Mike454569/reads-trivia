"""WAGER_MODE -- 15-Format Expansion Part 2, format #12.

Real Jeopardy-style category wagering: each round shows only a real
category name (never the question itself), the player wagers any real
fictional-point amount from 0 up to their current running balance, and
only then is the real question revealed. A correct answer adds the real
wager to the balance; a wrong answer subtracts it. The run ends when the
real balance reaches 0 or after round_count rounds, whichever comes
first -- same real "ends early" discipline RISK_IT's own life system
already established, reused here for a continuous wager instead of a
discrete life.

Real 2-step interaction per round (place a wager, then answer) -- same
real navigation-then-leaf-question shape BRANCH_STATE/RISK_IT already
established.

3 real categories, each reusing an already-certified real table from
elsewhere in this Engine's own mechanics (never a new, unverified query
pattern):
  - "NFL Draft": which real team drafted this real player (draft_facts,
    NFLVERSE_DATA, SOURCE_BACKED -- same table RISK_IT uses).
  - "Heisman Winners": which real school did this real Heisman winner
    play for (cfb_award_facts, SOURCE_BACKED_FROM_CFB_MASTER -- same
    table SORTING_TIMELINE's own CFB_HEISMAN_YEAR_ORDER variant uses).
  - "Super Bowl Champions": which real team won the Super Bowl following
    this real season (nfl_championship_events, WIKIPEDIA_STRUCTURED_
    SECONDARY -- same table GUESS_THE_SEASON uses).

Fictional currency only (a real starting balance of 1000 points, plainly
a game score, never real money) -- same disclosure discipline
AUCTION_DRAFT/CAP_CHALLENGE's own "fictional cost" already established
for this Engine's other wagering-adjacent formats.

Single variant for now: WAGER_MODE_MIXED (all 3 real categories,
randomly assigned per round).
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
MECHANIC = "WAGER_MODE"
VARIANTS = frozenset({"WAGER_MODE_MIXED"})
STARTING_BALANCE = 1000
_CATEGORIES = ("NFL Draft", "Heisman Winners", "Super Bowl Champions")


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        "cfb_award_facts": safety.check_verification_status_safety(
            c, "cfb_award_facts", "READS_CFB_MASTER", "SOURCE_BACKED_FROM_CFB_MASTER",
            where_extra="award_name = 'Heisman Trophy'",
        ),
        "nfl_championship_events": safety.check_verification_status_safety(
            c, "nfl_championship_events", "WIKIPEDIA_STRUCTURED", "WIKIPEDIA_STRUCTURED_SECONDARY",
        ),
    }


def _nfl_draft_question(rng, rows_by_season: dict) -> dict | None:
    seasons = list(rows_by_season.keys())
    if not seasons:
        return None
    rng.shuffle(seasons)
    for season in seasons:
        pool = rows_by_season[season]
        correct = rng.choice(pool)
        other_teams_pool = [r for r in pool if r["draft_team"] != correct["draft_team"]]
        decoy_teams = list({r["draft_team"] for r in other_teams_pool})
        if len(decoy_teams) < 3:
            continue
        rng.shuffle(decoy_teams)
        return {
            "prompt": f"Which real team drafted {correct['player_name']} in the {season} NFL Draft?",
            "correct_label": correct["draft_team"], "decoy_labels": decoy_teams[:3],
            "notes": f"Real {season} NFL Draft: {correct['player_name']} to {correct['draft_team']} "
                     f"(NFLVERSE_DATA, SOURCE_BACKED).",
        }
    return None


def _heisman_question(rng, rows: list) -> dict | None:
    if len(rows) < 4:
        return None
    pool = list(rows)
    rng.shuffle(pool)
    correct = pool[0]
    other_schools_pool = [r for r in pool[1:] if r["school_name"] != correct["school_name"]]
    decoy_schools = list({r["school_name"] for r in other_schools_pool})
    if len(decoy_schools) < 3:
        return None
    rng.shuffle(decoy_schools)
    return {
        "prompt": f"Which real school did {correct['award_year']} Heisman winner {correct['player_name']} play for?",
        "correct_label": correct["school_name"], "decoy_labels": decoy_schools[:3],
        "notes": f"Real {correct['award_year']} Heisman Trophy winner {correct['player_name']}, "
                 f"{correct['school_name']} (READS_CFB_MASTER, SOURCE_BACKED_FROM_CFB_MASTER).",
    }


def _super_bowl_question(rng, rows: list) -> dict | None:
    if len(rows) < 4:
        return None
    pool = list(rows)
    rng.shuffle(pool)
    correct = pool[0]
    other_winners_pool = [r for r in pool[1:] if r["winner_name_raw"] != correct["winner_name_raw"]]
    decoy_winners = list({r["winner_name_raw"] for r in other_winners_pool})
    if len(decoy_winners) < 3:
        return None
    rng.shuffle(decoy_winners)
    return {
        "prompt": f"Which real team won the Super Bowl following the {correct['season']} NFL season?",
        "correct_label": correct["winner_name_raw"], "decoy_labels": decoy_winners[:3],
        "notes": f"Real {correct['season']} season Super Bowl champion: {correct['winner_name_raw']} "
                 f"(WIKIPEDIA_STRUCTURED, WIKIPEDIA_STRUCTURED_SECONDARY).",
    }


def generate_rounds(seed: str, variant: str, round_count: int = 5) -> dict:
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
        # Cycles through all 3 real categories in a real, deterministic
        # (seed-dependent) rotation rather than a fully independent random
        # pick each round -- guarantees round_count >= 3 sessions see
        # every real category at least once, never all-one-category by chance.
        cat = _CATEGORIES[i % len(_CATEGORIES)]
        cat_rng = engine_bootstrap.seeded(f"{seed}-r{i}")
        if cat == "NFL Draft":
            q = _nfl_draft_question(cat_rng, draft_by_season)
        elif cat == "Heisman Winners":
            q = _heisman_question(cat_rng, heisman_rows)
        else:
            q = _super_bowl_question(cat_rng, sb_rows)
        if q is None:
            continue
        rounds.append({"category": cat, **q})

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real WAGER_MODE rounds could be built with a "
            f"real, decoy-complete question; exported the maximum available rather than include a "
            f"fabricated or incomplete question."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"WAGER_MODE_MIXED": "Wager Mode"}


def build_package(seed: str, variant: str, round_count: int = 5) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP24:" + hashlib.sha256(
        f"WAGER_MODE|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_label"]] + list(r["decoy_labels"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-shuffle-{i}").shuffle(order)
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
        "game_instructions": "You'll see only a real category. Wager any amount of your fictional balance, "
                              "then the real question is revealed -- a correct answer adds your wager, a "
                              "wrong answer subtracts it.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds), "starting_balance": STARTING_BALANCE,
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
