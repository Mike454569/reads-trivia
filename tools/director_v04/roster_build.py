"""ROSTER_BUILD -- 40-Format Expansion pass, extended in the Finish-10-Formats
pass with real CFB support and a real, balanced FICTIONAL cost model.

Backs LINEUP_BUILDER (no budget -- construct a themed real lineup) and
AUCTION_DRAFT/CAP_CHALLENGE (a budget constrains which real players can be
picked). Generalizes tools/director_v04/live_weekly_fantasy_draft.py's
real, already-proven shape -- sequential slot-filling from a real, VISIBLE
eligible pool, no hidden answer, no player draftable twice -- with a
swappable per-variant pool-query function.

Real correction this pass (see fictional_game_value.py's own module
docstring for the full reasoning): AUCTION_DRAFT/CAP_CHALLENGE's DEFAULT
cost mode is now a real, balanced, deterministic FICTIONAL value derived
from certified stats (NFL: real career AV sum; CFB: real career yardage
sum) -- neither league needs real salary/NIL data. A real-NFL-contract
variant (NFL_AUCTION_DRAFT_REAL_CONTRACT) is kept as an explicit, clearly
labeled opt-in, never the default.

Real `flow` distinction (also new this pass), carried on every package as
`flow`:
  - SEQUENTIAL (AUCTION_DRAFT): the player picks one slot at a time, in
    slot order; each pick is immediately locked in and its cost
    immediately deducted -- cannot be undone.
  - FREE_SELECT (CAP_CHALLENGE): the player may select/deselect any open
    slot in any order, swapping picks freely; the budget/eligibility
    check is a live, running total, but nothing is LOCKED until a final
    `submit_lineup` action, which is the one point real over-cap/
    incomplete-roster rejection is authoritative.
Both flows share the exact same real pool-query functions and player data
-- only the interaction/lock-in shape differs, matching the format spec's
own "sequential acquisitions" vs "optimize under a ceiling" distinction.

Six real, disclosed variants:
  - NFL_2010S_OFFENSE_BUILDER (LINEUP_BUILDER, no budget): every real
    player with >=1 real start at a skill position (QB/RB/WR/TE) in any
    season 2010-2019 -- decade-wide, not scoped to one team.
  - CFB_SKILL_POSITION_BUILDER (LINEUP_BUILDER, no budget): every real CFB
    player with a real roster row at a skill position (cfb_roster_seasons_
    real, 32,550 distinct real players confirmed live this pass) -- the
    narrower, genuinely-supported CFB configuration this pass's own
    correction requires (a full 11-player CFB offense including 5 verified
    O-linemen remains MISSING_DATA -- no real CFB O-line data exists at
    all, per the original data audit -- but a skill-position-only build is
    real and fully supported, never blocked by that unrelated gap).
  - NFL_AUCTION_DRAFT (AUCTION_DRAFT, SEQUENTIAL flow, fictional cost):
    real players with an active resolved NFL contract row (for real
    identity/position only -- the COST itself is the fictional model, not
    the contract's real APY).
  - NFL_AUCTION_DRAFT_REAL_CONTRACT (AUCTION_DRAFT, SEQUENTIAL flow, REAL
    cost): explicit opt-in -- same real pool, cost = real APY.
  - CFB_AUCTION_DRAFT (AUCTION_DRAFT, SEQUENTIAL flow, fictional cost):
    real CFB skill-position players, cost = fictional model from real
    career yardage.
  - Any of the AUCTION_DRAFT variants above is reused UNCHANGED for
    CAP_CHALLENGE by generating with flow="FREE_SELECT" instead (see
    `build_package`'s own `flow` parameter) -- never a second pool/cost
    implementation.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import fictional_game_value as fgv  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.1"
MECHANIC = "ROSTER_BUILD"
VARIANTS = frozenset({
    "NFL_2010S_OFFENSE_BUILDER", "CFB_SKILL_POSITION_BUILDER",
    "NFL_AUCTION_DRAFT", "NFL_AUCTION_DRAFT_REAL_CONTRACT", "CFB_AUCTION_DRAFT",
})
_BUDGETED_VARIANTS = frozenset({"NFL_AUCTION_DRAFT", "NFL_AUCTION_DRAFT_REAL_CONTRACT", "CFB_AUCTION_DRAFT"})
_REAL_CONTRACT_VARIANTS = frozenset({"NFL_AUCTION_DRAFT_REAL_CONTRACT"})

ROSTER_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE"]
_REQUIRED_POSITIONS = frozenset({"QB", "RB", "WR", "TE"})
AUCTION_BUDGET = fgv.AUCTION_BUDGET  # real, clearly-labeled FICTIONAL in-game budget -- never a real salary cap


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "canonical_roster_seasons": safety.check_table_wide_safety(
            c, "canonical_roster_seasons", ["NFLVERSE_DATA", "NFLVERSE_ROSTERS"]
        ),
        "nfl_player_contracts": safety.check_table_wide_safety(c, "nfl_player_contracts", "NFLVERSE_DATA"),
        "cfb_roster_seasons_real": safety.check_table_wide_safety(
            c, "cfb_roster_seasons_real", ["SPORTSDATAVERSE_CFB", "READS_MASTER_KNOWLEDGE_FEED_2026_09"],
        ),
        # Real per-table status differs from the "SOURCE_BACKED" convention
        # most tables use -- confirmed live this pass: every row here is
        # SOURCE_BACKED_DERIVED, not SOURCE_BACKED.
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED",
        ),
    }


def _lineup_builder_pool(c) -> dict:
    rows = c.execute(
        "SELECT DISTINCT rs.player_id, p.display_name, rs.position "
        "FROM canonical_roster_seasons rs JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.season BETWEEN 2010 AND 2019 AND rs.starts > 0 "
        "AND rs.position IN ('QB','RB','WR','TE') AND rs.verification_status='SOURCE_BACKED'"
    ).fetchall()
    return {r["player_id"]: {"display_name": r["display_name"], "position": r["position"], "cost": None} for r in rows}


def _cfb_skill_position_pool(c) -> dict:
    rows = c.execute(
        "SELECT DISTINCT rs.cfb_player_id, p.display_name, rs.position "
        "FROM cfb_roster_seasons_real rs JOIN canonical_cfb_players p ON p.cfb_player_id = rs.cfb_player_id "
        "WHERE rs.position IN ('QB','RB','WR','TE') AND rs.verification_status='SOURCE_BACKED' "
        "AND p.display_name IS NOT NULL"
    ).fetchall()
    return {r["cfb_player_id"]: {"display_name": r["display_name"], "position": r["position"], "cost": None} for r in rows}


def _nfl_auction_pool(c, real_contract: bool) -> dict:
    if real_contract:
        rows = c.execute(
            "SELECT player_key, position, apy FROM nfl_player_contracts "
            "WHERE is_active=1 AND verification_status='SOURCE_BACKED' AND apy IS NOT NULL "
            "AND position IN ('QB','RB','WR','TE')"
        ).fetchall()
        names = {r["player_id"]: r["display_name"] for r in c.execute("SELECT player_id, display_name FROM canonical_players")}
        pool = {}
        for r in rows:
            display_name = names.get(r["player_key"])
            if not display_name:
                continue
            pool[r["player_key"]] = {"display_name": display_name, "position": r["position"], "cost": r["apy"]}
        return pool

    # Fictional cost mode (the real default): real player identity/position
    # from the contracts table (a real, already-resolved skill-position
    # pool), real COST from the fictional model keyed to real career AV --
    # never the contract's own real APY.
    contract_rows = c.execute(
        "SELECT DISTINCT player_key, position FROM nfl_player_contracts "
        "WHERE is_active=1 AND verification_status='SOURCE_BACKED' AND position IN ('QB','RB','WR','TE')"
    ).fetchall()
    names = {r["player_id"]: r["display_name"] for r in c.execute("SELECT player_id, display_name FROM canonical_players")}
    av_sums = {
        r["player_id"]: r["tot"] for r in c.execute(
            "SELECT player_id, SUM(av) tot FROM canonical_roster_seasons WHERE av IS NOT NULL "
            "AND verification_status='SOURCE_BACKED' GROUP BY player_id"
        ).fetchall()
    }
    pool = {}
    for r in contract_rows:
        display_name = names.get(r["player_key"])
        if not display_name:
            continue
        career_av = av_sums.get(r["player_key"], 0.0) or 0.0
        pool[r["player_key"]] = {
            "display_name": display_name, "position": r["position"], "cost": fgv.nfl_fictional_cost(career_av),
        }
    return pool


def _cfb_auction_pool(c) -> dict:
    roster_rows = c.execute(
        "SELECT DISTINCT rs.cfb_player_id, p.display_name, rs.position "
        "FROM cfb_roster_seasons_real rs JOIN canonical_cfb_players p ON p.cfb_player_id = rs.cfb_player_id "
        "WHERE rs.position IN ('QB','RB','WR','TE') AND rs.verification_status='SOURCE_BACKED' "
        "AND p.display_name IS NOT NULL"
    ).fetchall()
    yard_sums = {
        r["cfb_player_id"]: r["tot"] for r in c.execute(
            "SELECT cfb_player_id, SUM(COALESCE(passing_yards,0)+COALESCE(rushing_yards,0)+COALESCE(receiving_yards,0)) tot "
            "FROM cfb_player_season_stats_real WHERE verification_status='SOURCE_BACKED_DERIVED' GROUP BY cfb_player_id"
        ).fetchall()
    }
    pool = {}
    for r in roster_rows:
        career_yards = yard_sums.get(r["cfb_player_id"], 0.0) or 0.0
        pool[r["cfb_player_id"]] = {
            "display_name": r["display_name"], "position": r["position"], "cost": fgv.cfb_fictional_cost(career_yards),
        }
    return pool


def generate_pool(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_2010S_OFFENSE_BUILDER":
            pool = _lineup_builder_pool(c)
        elif variant == "CFB_SKILL_POSITION_BUILDER":
            pool = _cfb_skill_position_pool(c)
        elif variant in ("NFL_AUCTION_DRAFT", "NFL_AUCTION_DRAFT_REAL_CONTRACT"):
            pool = _nfl_auction_pool(c, real_contract=variant in _REAL_CONTRACT_VARIANTS)
        else:  # CFB_AUCTION_DRAFT
            pool = _cfb_auction_pool(c)
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


_GAME_TITLES = {
    "NFL_2010S_OFFENSE_BUILDER": "2010s Offense Builder",
    "CFB_SKILL_POSITION_BUILDER": "CFB Skill Position Builder",
    "NFL_AUCTION_DRAFT": "NFL Auction Draft",
    "NFL_AUCTION_DRAFT_REAL_CONTRACT": "NFL Auction Draft (Real Contracts)",
    "CFB_AUCTION_DRAFT": "CFB Auction Draft",
}


def build_package(seed: str, variant: str, *, flow: str = "SEQUENTIAL") -> dict:
    if flow not in ("SEQUENTIAL", "FREE_SELECT"):
        raise ValueError(f"flow must be 'SEQUENTIAL' or 'FREE_SELECT', got {flow!r}")
    result = generate_pool(seed, variant)
    package_id = "GGP13:" + hashlib.sha256(
        f"ROSTER_BUILD|{variant}|{flow}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    budgeted = variant in _BUDGETED_VARIANTS
    real_contract = variant in _REAL_CONTRACT_VARIANTS
    valid = bool(result["players"]) and not result["shortfall_reason"]

    if not budgeted:
        instructions = (
            f"Build a real roster ({', '.join(ROSTER_SLOTS)}) from real eligible players -- one real "
            f"player per slot, no player twice."
        )
    elif real_contract:
        instructions = (
            f"Build a real roster ({', '.join(ROSTER_SLOTS)}) using each player's REAL career-average "
            f"annual salary as their cost, under a fictional ${AUCTION_BUDGET:,} budget. Every dollar "
            f"figure is a real contract value; the budget itself is not a real salary cap."
        )
    elif flow == "SEQUENTIAL":
        instructions = (
            f"Draft a real roster ({', '.join(ROSTER_SLOTS)}) one slot at a time under a fictional "
            f"${AUCTION_BUDGET:,} budget. Each pick's cost is a fictional, deterministic value derived "
            f"from real career production -- locked in immediately, no player twice."
        )
    else:
        instructions = (
            f"Assemble a complete real roster ({', '.join(ROSTER_SLOTS)}) under a fictional "
            f"${AUCTION_BUDGET:,} cap. Freely select, swap, or remove picks -- nothing is locked until "
            f"you submit the finished lineup, which must be complete and within the cap."
        )

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "flow": flow,
        "game_title": _GAME_TITLES[variant] + (" -- Cap Challenge" if budgeted and flow == "FREE_SELECT" else ""),
        "game_instructions": instructions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "players": result["players"], "player_count": len(result["players"]),
        "by_position": result["by_position"], "roster_slots": list(ROSTER_SLOTS),
        "budgeted": budgeted, "budget_total": AUCTION_BUDGET if budgeted else None,
        "cost_model": ("REAL_CONTRACT" if real_contract else ("FICTIONAL" if budgeted else None)),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
