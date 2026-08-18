"""SORTING_TIMELINE -- Reliability Design Phase 6, real mechanic template #4.

A real ordering game: N items sharing one real, verified, tie-free
orderable attribute. Built from scratch (no prior adapter existed) on
already-certified real tables.

Two real, disclosed variants:
  - NFL_DRAFT_PICK_ORDER: N real players from the SAME real NFL draft class
    (draft_facts, NFLVERSE_DATA, SOURCE_BACKED), ordered by their real
    `draft_pick_overall`. Tie-free by construction -- overall picks are
    unique within a draft class, so no tie-handling logic is needed or
    invented.
  - CFB_HEISMAN_YEAR_ORDER: N real Heisman Trophy winners (cfb_award_facts,
    SOURCE_BACKED_FROM_CFB_MASTER), ordered by real `award_year`. Tie-free
    by construction -- exactly one winner per year.
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
MECHANIC = "SORTING_TIMELINE"
MIN_ITEMS = 4
MAX_ITEMS = 6

VARIANTS = frozenset({"NFL_DRAFT_PICK_ORDER", "CFB_HEISMAN_YEAR_ORDER"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        "cfb_award_facts": safety.check_verification_status_safety(
            c, "cfb_award_facts", "READS_CFB_MASTER", "SOURCE_BACKED_FROM_CFB_MASTER",
            where_extra="award_name = 'Heisman Trophy'",
        ),
    }


def _nfl_draft_pick_order_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_pick_overall FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' "
        "AND draft_season IS NOT NULL AND draft_pick_overall IS NOT NULL "
        "ORDER BY draft_season, draft_pick_overall"
    ).fetchall()
    by_season: dict[int, list] = {}
    for r in rows:
        by_season.setdefault(r["draft_season"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    seasons = sorted(by_season.keys())
    rng.shuffle(seasons)

    rounds = []
    for season in seasons:
        if len(rounds) >= round_count:
            break
        players = by_season[season]
        if len(players) < item_count:
            continue
        picks = sorted(rng.sample(players, item_count), key=lambda p: p["draft_pick_overall"])
        if len({p["draft_pick_overall"] for p in picks}) != len(picks):
            continue  # unreachable given real draft data, but never trust silently
        rounds.append({
            "variant": "NFL_DRAFT_PICK_ORDER", "season": season,
            "prompt": f"Put these {season} NFL Draft picks in order, earliest overall selection first.",
            "items_in_order": [{"label": p["player_name"], "_audit": {"player_key": p["player_key"],
                                "draft_pick_overall": p["draft_pick_overall"]}} for p in picks],
            "notes": f"Real {season} NFL Draft order by overall pick number, NFLVERSE_DATA, SOURCE_BACKED.",
        })
    return rounds


def _cfb_heisman_year_order_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT award_year, player_name, school_name FROM cfb_award_facts "
        "WHERE verification_status='SOURCE_BACKED_FROM_CFB_MASTER' AND award_name='Heisman Trophy' "
        "AND player_name IS NOT NULL ORDER BY award_year"
    ).fetchall()
    if len(rows) < item_count:
        return []
    rng = engine_bootstrap.seeded(seed)
    rounds = []
    attempts = 0
    while len(rounds) < round_count and attempts < round_count * 5:
        attempts += 1
        sample = sorted(rng.sample(rows, item_count), key=lambda r: r["award_year"])
        if len({r["award_year"] for r in sample}) != len(sample):
            continue  # unreachable (one winner per year), defensive only
        rounds.append({
            "variant": "CFB_HEISMAN_YEAR_ORDER", "season": None,
            "prompt": "Put these Heisman Trophy winners in order, earliest year first.",
            "items_in_order": [{"label": f"{r['player_name']} ({r['school_name']})",
                                "_audit": {"award_year": r["award_year"]}} for r in sample],
            "notes": "Real Heisman Trophy winners ordered by real award year, cfb_award_facts, SOURCE_BACKED_FROM_CFB_MASTER.",
        })
    return rounds


def _finalize_round(round_index: int, raw: dict) -> dict:
    ordered = raw["items_in_order"]
    item_ids_in_order = [f"I{i}" for i in range(len(ordered))]
    shuffled_indices = list(range(len(ordered)))
    engine_bootstrap.seeded(f"shuffle-{round_index}-{raw.get('season')}").shuffle(shuffled_indices)
    items_shuffled = [{"item_id": item_ids_in_order[i], "label": ordered[i]["label"]} for i in shuffled_indices]
    return {
        "round_index": round_index, "variant": raw["variant"], "prompt": raw["prompt"],
        "items_shuffled": items_shuffled,
        "_private_correct_order": item_ids_in_order,
        "notes": raw["notes"],
        "_audit": {"season": raw.get("season"), "items": [it["_audit"] for it in ordered]},
    }


def generate_rounds(seed: str, variant: str, round_count: int = 5, item_count: int = 4) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    if not (MIN_ITEMS <= item_count <= MAX_ITEMS):
        raise ValueError(f"item_count must be in [{MIN_ITEMS}, {MAX_ITEMS}]")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_DRAFT_PICK_ORDER":
            raw_rounds = _nfl_draft_pick_order_rounds(c, seed, round_count, item_count)
        else:
            raw_rounds = _cfb_heisman_year_order_rounds(c, seed, round_count, item_count)
    finally:
        c.close()

    rounds = [_finalize_round(i, r) for i, r in enumerate(raw_rounds)]
    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real SORTING_TIMELINE rounds could be built "
            f"for variant={variant!r} with {item_count} items each, all genuinely tie-free; exported the "
            f"maximum available rather than include a tied or fabricated ordering."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


def build_package(seed: str, variant: str, round_count: int = 5, item_count: int = 4) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count, item_count=item_count)
    package_id = "GGP6:" + hashlib.sha256(f"SORTING|{variant}|{seed}|{round_count}|{item_count}".encode()).hexdigest()[:24]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "NFL Draft Order" if variant == "NFL_DRAFT_PICK_ORDER" else "Heisman Timeline",
        "game_instructions": "Put these real items in the correct order.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if result["rounds"] else "FAILED",
        "rounds": result["rounds"], "round_count": len(result["rounds"]),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
