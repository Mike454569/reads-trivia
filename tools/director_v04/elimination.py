"""ELIMINATION_SURVIVAL -- Reliability Design Phase 6, real mechanic
template #6.

A real true/false category-membership survival sequence: one wrong answer
ends the run (one-miss elimination, the spec's baseline rule). Built from
scratch (no prior adapter existed) on already-certified real tables.
Escalating difficulty reuses the same real, disclosed recency heuristic
already established by `tools/quiz_export/adapters/lineup.py` (more recent
= easier to recognize) -- items are ordered most-recent-first within each
sequence, never a claim of empirically-validated difficulty.

Two real, disclosed variants:
  - NFL_SUPER_BOWL_CHAMPION_SURVIVAL: "Did the {team} win the Super Bowl
    following the {season} season?" True membership = `season_standings.
    playoff_result = 'WonSB'` (SOURCE_BACKED, the same table NFL_SUPER_BOWL/
    NFL_CHAMPIONSHIP already use). False membership = any other real
    (season, team_code) row -- including a team that made the playoffs but
    didn't win, or missed the playoffs entirely; every example is a real,
    verified row, never a fabricated "false" team-season.
  - CFB_NATIONAL_CHAMPION_SURVIVAL: "Did {school} win the national
    championship in {season}?" True membership = the real
    `CFB_NATIONAL_CHAMPION` relationship (SOURCE_BACKED_FROM_CFB_MASTER).
    False membership = any other real FBS (school, season) row from
    `cfb_standings` (classification='fbs' only -- comparing an FBS
    championship claim against a real Division-II/III program would be a
    structurally unfair/misleading category test, so non-FBS rows are
    excluded outright, not silently included).
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

# Bumped 1.0 -> 1.1 in the Final Technical Risk Cleanup pass: the Final
# Player-Facing Stress Test pass changed _nfl_super_bowl_items()'s real
# candidate-selection logic (excluding unresolved-season rows) without
# bumping this constant, which is what let a stale pre-fix package_id
# collide with newly-fixed content under the same seed -- see
# package_id's own comment below for the general fix.
PACKAGE_SCHEMA_VERSION = "1.1"
MECHANIC = "ELIMINATION_SURVIVAL"
MIN_SEQUENCE_LENGTH = 8

VARIANTS = frozenset({"NFL_SUPER_BOWL_CHAMPION_SURVIVAL", "CFB_NATIONAL_CHAMPION_SURVIVAL"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "season_standings": safety.check_table_wide_safety(c, "season_standings", "NFLVERSE_DATA"),
        "cfb_standings": safety.check_table_wide_safety(c, "cfb_standings", "CFBD_API_LIVE"),
    }


def _nfl_super_bowl_items(c, seed: str, sequence_length: int) -> list[dict]:
    rows = c.execute(
        "SELECT season, team_code, playoff_result FROM season_standings "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' ORDER BY season DESC"
    ).fetchall()
    # Final Player-Facing Stress Test pass: a real, found bug -- NULL
    # playoff_result is NOT the same fact for every season. For a real,
    # COMPLETED season it correctly means "missed the playoffs" (a real,
    # verified false-membership example -- most of a season's 32 real rows
    # are legitimately NULL this way, e.g. 2020's real playoff-missers).
    # But season_standings also carries 32 real placeholder rows for the
    # CURRENT, not-yet-played season (every playoff_result NULL because no
    # games have happened yet, not because those teams "missed the
    # playoffs") -- treating those as real false examples asked a player
    # "did the {2026 team} win the Super Bowl" as if that were an already-
    # resolved historical fact. Detected generically (never a hardcoded
    # year that would go stale every season): a season only counts as
    # resolved if at least one real row for it has a non-NULL
    # playoff_result at all -- a season with zero non-NULL rows has
    # genuinely not been played out yet.
    resolved_seasons = {r["season"] for r in rows if r["playoff_result"] is not None}
    rows = [r for r in rows if r["season"] in resolved_seasons]
    true_rows = [r for r in rows if r["playoff_result"] == "WonSB"]
    false_rows = [r for r in rows if r["playoff_result"] != "WonSB"]
    if len(true_rows) < sequence_length // 4 or len(false_rows) < sequence_length // 2:
        return []

    rng = engine_bootstrap.seeded(seed)
    half_true = max(2, sequence_length // 3)
    chosen_true = rng.sample(true_rows, min(half_true, len(true_rows)))
    chosen_false = rng.sample(false_rows, sequence_length - len(chosen_true))
    combined = chosen_true + chosen_false
    combined.sort(key=lambda r: -r["season"])  # most-recent-first == easier-first (disclosed heuristic)

    items = []
    for r in combined:
        fr, err = resolve_franchise(c, r["team_code"], r["season"])
        if err or fr is None:
            continue
        items.append({
            "prompt": f"Did the {fr['full_name']} win the Super Bowl following the {r['season']} season?",
            "_private_membership": r["playoff_result"] == "WonSB",
            "_audit": {"season": r["season"], "team_code": r["team_code"], "franchise_id": fr["franchise_id"],
                       "playoff_result": r["playoff_result"]},
        })
    return items


def _cfb_national_champion_items(c, seed: str, sequence_length: int) -> list[dict]:
    champ_rows = c.execute(
        "SELECT subject_id AS school_id, object_id AS season FROM relationships "
        "WHERE predicate='CFB_NATIONAL_CHAMPION' AND verification_status='SOURCE_BACKED_FROM_CFB_MASTER'"
    ).fetchall()
    champion_pairs = {(r["school_id"], int(r["season"])) for r in champ_rows}

    standings_rows = c.execute(
        "SELECT season, school_id, school_name_raw FROM cfb_standings "
        "WHERE verification_status='SOURCE_BACKED' AND classification='fbs' AND school_id IS NOT NULL"
    ).fetchall()
    school_names = {r["school_id"]: r["school_name"] for r in c.execute("SELECT school_id, school_name FROM schools")}

    true_rows = [r for r in standings_rows if (r["school_id"], r["season"]) in champion_pairs]
    false_rows = [r for r in standings_rows if (r["school_id"], r["season"]) not in champion_pairs]
    if len(true_rows) < sequence_length // 4 or len(false_rows) < sequence_length // 2:
        return []

    rng = engine_bootstrap.seeded(seed)
    half_true = max(2, sequence_length // 3)
    chosen_true = rng.sample(true_rows, min(half_true, len(true_rows)))
    chosen_false = rng.sample(false_rows, sequence_length - len(chosen_true))
    combined = chosen_true + chosen_false
    combined.sort(key=lambda r: -r["season"])

    items = []
    for r in combined:
        school_name = school_names.get(r["school_id"]) or r["school_name_raw"]
        items.append({
            "prompt": f"Did {school_name} win the national championship in {r['season']}?",
            "_private_membership": (r["school_id"], r["season"]) in champion_pairs,
            "_audit": {"season": r["season"], "school_id": r["school_id"]},
        })
    return items


def generate_sequence(seed: str, variant: str, sequence_length: int = 12) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    if sequence_length < MIN_SEQUENCE_LENGTH:
        raise ValueError(f"sequence_length must be >= {MIN_SEQUENCE_LENGTH}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_SUPER_BOWL_CHAMPION_SURVIVAL":
            items = _nfl_super_bowl_items(c, seed, sequence_length)
        else:
            items = _cfb_national_champion_items(c, seed, sequence_length)
    finally:
        c.close()

    for i, item in enumerate(items):
        item["item_index"] = i

    shortfall_reason = None
    if len(items) < sequence_length:
        shortfall_reason = (
            f"Only {len(items)} of {sequence_length} requested real ELIMINATION_SURVIVAL items could be "
            f"built for variant={variant!r} with real qualified true and false examples; exported the "
            f"maximum available rather than fabricate a membership answer."
        )
    return {"items": items, "safety": safety_result, "shortfall_reason": shortfall_reason}


def build_package(seed: str, variant: str, sequence_length: int = 12) -> dict:
    result = generate_sequence(seed, variant, sequence_length=sequence_length)
    package_id = "GGP7:" + hashlib.sha256(
        f"ELIMINATION|{variant}|{seed}|{sequence_length}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "Super Bowl Champion Survival" if variant == "NFL_SUPER_BOWL_CHAMPION_SURVIVAL" else "National Champion Survival",
        "game_instructions": "One miss ends the run. Answer True or False for each real team-season.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if len(result["items"]) >= MIN_SEQUENCE_LENGTH else "FAILED",
        "sequence": result["items"], "sequence_length": len(result["items"]),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
