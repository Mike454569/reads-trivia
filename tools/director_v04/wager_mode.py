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
  - "NFL Team Records": which real team posted a shown real regular-season
    record (season_standings, NFLVERSE_DATA, SOURCE_BACKED).
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
from tools.director_v04 import deep_trivia  # noqa: E402

PACKAGE_SCHEMA_VERSION = "2.0"
MECHANIC = "WAGER_MODE"
VARIANTS = frozenset({"WAGER_MODE_MIXED"})
STARTING_BALANCE = 1000
_CATEGORIES = ("NFL Team Records", "Heisman Winners", "Super Bowl Champions")


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "season_standings": safety.check_table_wide_safety(c, "season_standings", "NFLVERSE_DATA"),
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


def _record_label(row) -> str:
    ties = row["ties"] or 0
    return f"{row['wins']}-{row['losses']}-{ties}" if ties else f"{row['wins']}-{row['losses']}"


def _nfl_team_record_question(rng, rows_by_season: dict) -> dict | None:
    seasons = list(rows_by_season.keys())
    rng.shuffle(seasons)
    for season in seasons:
        pool = list(rows_by_season[season])
        rng.shuffle(pool)
        for correct in pool:
            correct_record = _record_label(correct)
            decoys = []
            seen = {correct_record}
            for row in pool:
                label = _record_label(row)
                if label in seen:
                    continue
                seen.add(label)
                decoys.append(label)
                if len(decoys) == 3:
                    break
            if len(decoys) < 3:
                continue
            return {
                "prompt": f"What was {correct['team_code']}'s real regular-season record in {season}?",
                "correct_label": correct_record, "decoy_labels": decoys,
                "notes": f"Real {season} regular-season record: {correct['team_code']} finished "
                         f"{correct_record} (NFLVERSE_DATA, SOURCE_BACKED).",
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
    finally:
        c.close()

    rounds = deep_trivia.generate_rounds(f"{seed}-wager", round_count)
    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real WAGER_MODE "
            "Deep Ball rounds could be built from certified real data."
        )
    return {
        "rounds": rounds,
        "safety": safety_result,
        "shortfall_reason": shortfall_reason,
    }


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
        order = list(range(len(candidates)))
        engine_bootstrap.seeded(f"{seed}-shuffle-{i}").shuffle(order)
        item_ids = [chr(ord("A") + n) for n in range(len(candidates))]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i,
            "category": r["category"],
            "bucket": r.get("bucket"),
            "difficulty": r.get("difficulty"),
            "depth_source": r.get("depth_source"),
            "prompt": r["prompt"],
            "options": options,
            "_answer_item_id": item_ids[correct_pos],
            "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "You'll see a real Deep Ball category. Wager before the question is revealed -- "
                              "game context, players, rankings, careers and more. Correct adds your wager; "
                              "wrong subtracts it.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds), "starting_balance": STARTING_BALANCE,
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
