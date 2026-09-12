"""ROSTER_BUILD -- 40-Format Expansion pass, new mechanic template.

Backs LINEUP_BUILDER (no budget -- construct a themed real lineup) and
AUCTION_DRAFT/CAP_CHALLENGE (a real dollar budget constrains which real
players can be picked). Generalizes tools/director_v04/
live_weekly_fantasy_draft.py's real, already-proven shape -- sequential
slot-filling from a real, VISIBLE eligible pool, no hidden answer, no
player draftable twice -- with a swappable per-variant pool-query function
and an optional real per-player cost, instead of that module's fixed
schedule-driven (season, week) pool. Same real discipline that module's own
docstring establishes: this is a roster CONSTRUCTION exercise, never a
scored/"best" contest, unless an explicit real ranking model backs a
specific variant (none does here) -- validity is "every pick real, eligible
for its slot, not already drafted, and (if budgeted) within the remaining
real budget."

Two real, disclosed variants:
  - NFL_2010S_OFFENSE_BUILDER (LINEUP_BUILDER): eligible pool = every real
    player with >=1 real start (canonical_roster_seasons.starts > 0) at a
    skill position (QB/RB/WR/TE) in ANY season 2010-2019 -- a real,
    decade-wide pool, not scoped to one team (matching the format's own
    "Best 2010s offense" example). No budget.
  - NFL_AUCTION_DRAFT (AUCTION_DRAFT / CAP_CHALLENGE): eligible pool = every
    real player with an active, resolved contract (nfl_player_contracts,
    is_active=1, SOURCE_BACKED) at a skill position, with a real
    `apy` (average per year) dollar cost. Budget is a clearly-labeled
    FICTIONAL in-game number ($50,000,000) -- never presented as a real
    salary cap -- but every player's COST is a genuine real dollar figure,
    never fabricated (per the format's own explicit "do NOT present these
    as real salaries unless actual salary data is being used" instruction
    -- real salary data backs every cost here).
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
MECHANIC = "ROSTER_BUILD"
VARIANTS = frozenset({"NFL_2010S_OFFENSE_BUILDER", "NFL_AUCTION_DRAFT"})

ROSTER_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE"]
FLEX_ELIGIBLE_POSITIONS: frozenset[str] = frozenset()  # no FLEX slot in this roster shape
_REQUIRED_POSITIONS = frozenset({"QB", "RB", "WR", "TE"})
AUCTION_BUDGET = 50_000_000  # real, clearly-labeled FICTIONAL in-game budget -- never a real salary cap


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "canonical_roster_seasons": safety.check_table_wide_safety(
            c, "canonical_roster_seasons", ["NFLVERSE_DATA", "NFLVERSE_ROSTERS"]
        ),
        "nfl_player_contracts": safety.check_table_wide_safety(c, "nfl_player_contracts", "NFLVERSE_DATA"),
    }


def _lineup_builder_pool(c) -> dict:
    rows = c.execute(
        "SELECT DISTINCT rs.player_id, p.display_name, rs.position "
        "FROM canonical_roster_seasons rs JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.season BETWEEN 2010 AND 2019 AND rs.starts > 0 "
        "AND rs.position IN ('QB','RB','WR','TE') AND rs.verification_status='SOURCE_BACKED'"
    ).fetchall()
    return {r["player_id"]: {"display_name": r["display_name"], "position": r["position"], "cost": None} for r in rows}


def _auction_draft_pool(c) -> dict:
    rows = c.execute(
        "SELECT player_key, position, apy, team_code FROM nfl_player_contracts "
        "WHERE is_active=1 AND verification_status='SOURCE_BACKED' AND apy IS NOT NULL "
        "AND position IN ('QB','RB','WR','TE')"
    ).fetchall()
    names = {r["player_id"]: r["display_name"] for r in c.execute("SELECT player_id, display_name FROM canonical_players")}
    pool = {}
    for r in rows:
        display_name = names.get(r["player_key"])
        if not display_name:
            continue
        pool[r["player_key"]] = {
            "display_name": display_name, "position": r["position"], "cost": r["apy"], "team_code": r["team_code"],
        }
    return pool


def generate_pool(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        pool = _lineup_builder_pool(c) if variant == "NFL_2010S_OFFENSE_BUILDER" else _auction_draft_pool(c)
    finally:
        c.close()

    players = [
        {"player_id": pid, "display_name": e["display_name"], "position": e["position"], "cost": e.get("cost")}
        for pid, e in pool.items()
    ]
    rng = engine_bootstrap.seeded(seed)
    players.sort(key=lambda p: p["player_id"])
    rng.shuffle(players)

    by_position: dict[str, int] = {}
    for p in players:
        by_position[p["position"]] = by_position.get(p["position"], 0) + 1
    missing = sorted(pos for pos in _REQUIRED_POSITIONS if by_position.get(pos, 0) == 0)
    shortfall_reason = None
    if not players:
        shortfall_reason = f"No real eligible players found for variant={variant!r}."
    elif missing:
        shortfall_reason = f"No real eligible players at position(s) {missing} -- refusing to generate an incompletable roster."

    return {"players": players, "by_position": by_position, "safety": safety_result, "shortfall_reason": shortfall_reason}


def build_package(seed: str, variant: str) -> dict:
    result = generate_pool(seed, variant)
    package_id = "GGP13:" + hashlib.sha256(
        f"ROSTER_BUILD|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    budgeted = variant == "NFL_AUCTION_DRAFT"
    valid = bool(result["players"]) and not result["shortfall_reason"]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "2010s Offense Builder" if variant == "NFL_2010S_OFFENSE_BUILDER" else "NFL Auction Draft",
        "game_instructions": (
            f"Build a real roster ({', '.join(ROSTER_SLOTS)}) from real 2010s starters -- one real player "
            f"per slot, no player twice."
        ) if not budgeted else (
            f"Build a real roster ({', '.join(ROSTER_SLOTS)}) using each player's real career-average "
            f"annual salary as their cost, under a fictional ${AUCTION_BUDGET:,} budget. Every dollar "
            f"figure is real; the budget itself is not a real salary cap."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "players": result["players"], "player_count": len(result["players"]),
        "by_position": result["by_position"], "roster_slots": list(ROSTER_SLOTS),
        "budgeted": budgeted, "budget_total": AUCTION_BUDGET if budgeted else None,
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
