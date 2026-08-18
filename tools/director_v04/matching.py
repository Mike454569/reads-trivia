"""MATCHING -- Reliability Design Phase 6, real mechanic template #3.

A real N:N pairing game: left items are real entities, right items are
their real counterparts, shuffled. No adapter or public route existed for
this mechanic before Phase 6 -- built from scratch on top of already-
certified real tables (never a new/unverified data source).

Two real, disclosed variants:
  - NFL_DRAFT_CLASS_MATCH: within one real NFL draft class (draft_facts,
    NFLVERSE_DATA, SOURCE_BACKED -- the same table NFL_DRAFT/DRAFTED_BY
    already uses), match each of N real players to the real team that
    drafted him. One player per team is selected per round (the earliest
    real pick for that team, deterministic) specifically so no two left
    items can honestly map to the same right item -- the spec's "no
    duplicate item that creates multiple indistinguishable solutions" rule,
    enforced structurally, not just checked after the fact.
  - CFB_HEISMAN_SCHOOL_MATCH: N real Heisman Trophy winners (cfb_award_facts,
    91 rows, SOURCE_BACKED_FROM_CFB_MASTER -- the same table CFB_HEISMAN/
    WON_HEISMAN already uses) matched to their real school. Winners are
    chosen with distinct schools within one round for the same reason.

Server-private vs. client-safe split lives in tools/director_v02/
mechanic_engine.py (this module only ever returns the full, private round
-- it never decides what a client sees).
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters.draft import resolve_franchise  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "MATCHING"
MIN_PAIRS = 4
MAX_PAIRS = 6

VARIANTS = frozenset({"NFL_DRAFT_CLASS_MATCH", "CFB_HEISMAN_SCHOOL_MATCH"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        "cfb_award_facts": safety.check_verification_status_safety(
            c, "cfb_award_facts", "READS_CFB_MASTER", "SOURCE_BACKED_FROM_CFB_MASTER",
            where_extra="award_name = 'Heisman Trophy'",
        ),
    }


def _nfl_draft_class_rounds(c, seed: str, round_count: int, pair_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_team, draft_pick_overall "
        "FROM draft_facts WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' "
        "AND draft_season IS NOT NULL AND draft_team IS NOT NULL AND draft_pick_overall IS NOT NULL "
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
        # One player per team -- earliest real pick, deterministic, structurally
        # prevents two left items resolving to the identical right item.
        first_pick_by_team: dict[str, object] = {}
        for p in players:  # already ordered by draft_pick_overall ascending
            first_pick_by_team.setdefault(p["draft_team"], p)
        team_codes = sorted(first_pick_by_team.keys())
        if len(team_codes) < pair_count:
            continue
        rng.shuffle(team_codes)
        chosen_codes = team_codes[:pair_count]

        pairs = []
        ok = True
        for code in chosen_codes:
            p = first_pick_by_team[code]
            franchise, err = resolve_franchise(c, code, season)
            if err or franchise is None:
                ok = False
                break
            pairs.append({"left_label": p["player_name"], "right_label": franchise["full_name"],
                          "_audit": {"player_key": p["player_key"], "draft_pick_overall": p["draft_pick_overall"],
                                     "team_code": code, "franchise_id": franchise["franchise_id"]}})
        if not ok or len({p["right_label"] for p in pairs}) != len(pairs):
            continue  # a franchise-name collision (rare realignment edge case) -- skip, never fudge

        rng.shuffle(pairs)  # left-side display order
        rounds.append({
            "variant": "NFL_DRAFT_CLASS_MATCH", "season": season,
            "prompt": f"Match each {season} NFL Draft pick to the real team that drafted him.",
            "pairs": pairs,
            "notes": f"Real {season} NFL Draft picks (earliest selection per team), NFLVERSE_DATA, SOURCE_BACKED.",
        })
    return rounds


def _cfb_heisman_school_rounds(c, seed: str, round_count: int, pair_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT award_year, player_name, school_name, school_id FROM cfb_award_facts "
        "WHERE verification_status='SOURCE_BACKED_FROM_CFB_MASTER' AND award_name='Heisman Trophy' "
        "AND player_name IS NOT NULL AND school_name IS NOT NULL ORDER BY award_year"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    order = list(range(len(rows)))
    rng.shuffle(order)

    rounds = []
    used_start = 0
    # Deterministic sliding-window sampling over the real 91-winner list --
    # each window is checked for distinct schools (a school can win the
    # Heisman more than once, in different years) before being accepted.
    attempts = 0
    while len(rounds) < round_count and attempts < len(rows) * 2:
        attempts += 1
        window_start = order[used_start % len(order)]
        used_start += 1
        candidates = rows[max(0, window_start - pair_count * 3): window_start + pair_count * 3] or rows
        rng.shuffle(candidates)
        pairs, seen_schools = [], set()
        for r in candidates:
            if r["school_name"] in seen_schools:
                continue
            seen_schools.add(r["school_name"])
            pairs.append({"left_label": f"{r['player_name']} ({r['award_year']})", "right_label": r["school_name"],
                          "_audit": {"award_year": r["award_year"], "school_id": r["school_id"]}})
            if len(pairs) == pair_count:
                break
        if len(pairs) < pair_count:
            continue
        rng.shuffle(pairs)
        rounds.append({
            "variant": "CFB_HEISMAN_SCHOOL_MATCH", "season": None,
            "prompt": "Match each real Heisman Trophy winner to the school he played for.",
            "pairs": pairs,
            "notes": "Real Heisman Trophy winners, cfb_award_facts, SOURCE_BACKED_FROM_CFB_MASTER.",
        })
    return rounds


def _finalize_round(round_index: int, raw: dict) -> dict:
    left_items = [{"item_id": f"L{i}", "label": p["left_label"]} for i, p in enumerate(raw["pairs"])]
    right_order = list(range(len(raw["pairs"])))
    right_items = [{"item_id": f"R{i}", "label": raw["pairs"][i]["right_label"]} for i in right_order]
    answer_key = {f"L{i}": f"R{i}" for i in range(len(raw["pairs"]))}
    return {
        "round_index": round_index, "variant": raw["variant"], "prompt": raw["prompt"],
        "left_items": left_items, "right_items": right_items,
        "_private_answer_key": answer_key,
        "notes": raw["notes"],
        "_audit": {"season": raw.get("season"), "pairs": [p["_audit"] for p in raw["pairs"]]},
    }


def generate_rounds(seed: str, variant: str, round_count: int = 5, pair_count: int = 4) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    if not (MIN_PAIRS <= pair_count <= MAX_PAIRS):
        raise ValueError(f"pair_count must be in [{MIN_PAIRS}, {MAX_PAIRS}]")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_DRAFT_CLASS_MATCH":
            raw_rounds = _nfl_draft_class_rounds(c, seed, round_count, pair_count)
        else:
            raw_rounds = _cfb_heisman_school_rounds(c, seed, round_count, pair_count)
    finally:
        c.close()

    rounds = [_finalize_round(i, r) for i, r in enumerate(raw_rounds)]
    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real MATCHING rounds could be built for "
            f"variant={variant!r} with {pair_count} pairs each, without any duplicate-solution risk; "
            f"exported the maximum available rather than reuse a right-side item or loosen the "
            f"distinct-team/distinct-school requirement."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


def build_package(seed: str, variant: str, round_count: int = 5, pair_count: int = 4) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count, pair_count=pair_count)
    package_id = "GGP5:" + hashlib.sha256(f"MATCHING|{variant}|{seed}|{round_count}|{pair_count}".encode()).hexdigest()[:24]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "Matching" if variant == "NFL_DRAFT_CLASS_MATCH" else "CFB Heisman Matching",
        "game_instructions": "Match each item on the left to its real counterpart on the right.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if result["rounds"] else "FAILED",
        "rounds": result["rounds"], "round_count": len(result["rounds"]),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
