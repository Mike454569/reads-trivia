"""COMMON_LINK -- 75-Format Expansion (Wave 1), format #36 overall.

Real shared-relationship identification: each round shows 3 real NFL
Draft picks (by name) that genuinely share one real attribute -- the
same real college, the same real draft season, or the same real drafting
team -- and asks the player to identify what connects them among 4 real
candidate statements. The correct statement names the real shared
attribute; the 3 decoy statements name other real, distinct values along
that same real dimension (other real colleges/seasons/teams that
genuinely appear in draft_facts, just not this trio's real shared one).

Reuses draft_facts.college (NFLVERSE_DATA, SOURCE_BACKED) -- a real
field no other format this pass has used yet -- alongside the same real
draft_season/draft_team fields RISK_IT and others already certified.

Deliberately distinct from PICK_THE_IMPOSTOR/MISSING_PIECE (protected,
15-Format Expansion): those formats work with real roster/draft-class
MEMBERSHIP (who was really on this team/school/class) and ask the player
to find the one that doesn't belong or is missing. COMMON_LINK never
asks about membership in a single group -- it shows 3 real players who
already, verifiably, share ONE real attribute and asks the player to
NAME which attribute that is, a genuinely different "identify the
relationship type" challenge (the user's own spec: "emphasizes graph
relationships rather than a hidden descriptive category").

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also", and
separately: "can every new format mode not be strictly about the draft").
Added CFB_SEASON_COMMON_LINK -- deliberately NOT draft-flavored (CFB
players aren't drafted): 3 real CFB players from a single season who
genuinely share the same real school, the same real season, or the same
real conference (cfb_player_season_stats_real + schools), same "identify
the relationship type" shape as the NFL variant.

Category variety pass (user feedback: "we don't need game modes based on
draft picks" -- all 3 of the NFL variant's original link types (college/
draft_season/draft_team) were really just 3 different fields of the same
draft_facts table, so every round was still "3 players who were drafted"
underneath). NFL_DRAFT_COMMON_LINK now also draws from a genuinely
different, non-draft real pool per round -- canonical_roster_seasons
(NFLVERSE_DATA, SOURCE_BACKED): 3 real players who shared the same real
team, the same real season, or the same real position, with no draft
concept involved at all. Which pool (DRAFT vs ROSTER) a round uses is
itself seeded/deterministic.

Two variants: NFL_DRAFT_COMMON_LINK, CFB_SEASON_COMMON_LINK.
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
MECHANIC = "COMMON_LINK"
VARIANTS = frozenset({"NFL_DRAFT_COMMON_LINK", "CFB_SEASON_COMMON_LINK"})

_LINK_TYPES = ("college", "draft_season", "draft_team")
_STATEMENT_TEMPLATES = {
    "college": lambda v: f"They all played college football at {v}.",
    "draft_season": lambda v: f"They were all drafted in the {v} NFL Draft.",
    "draft_team": lambda v: f"They were all drafted by the {v}.",
}

_CFB_LINK_TYPES = ("school", "season", "conference")
_CFB_STATEMENT_TEMPLATES = {
    "school": lambda v: f"They all played for {v}.",
    "season": lambda v: f"They all played in the {v} season.",
    "conference": lambda v: f"They all played in the {v}.",
}

_ROSTER_LINK_TYPES = ("team", "season", "position")
_ROSTER_STATEMENT_TEMPLATES = {
    "team": lambda v: f"They all played for the {v}.",
    "season": lambda v: f"They all played in the {v} season.",
    "position": lambda v: f"They all played {v}.",
}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED"),
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'"),
    }


def _fetch_rows(c) -> list[dict]:
    rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_team, college FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' "
        "AND draft_team IS NOT NULL AND college IS NOT NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def _group_by(rows: list[dict], link_type: str) -> dict:
    groups: dict = {}
    for r in rows:
        groups.setdefault(r[link_type], []).append(r)
    return groups


def _build_round(rng, rows: list[dict], groups_by_type: dict[str, dict]) -> dict | None:
    link_types = list(_LINK_TYPES)
    rng.shuffle(link_types)
    for link_type in link_types:
        groups = groups_by_type[link_type]
        eligible_values = [v for v, members in groups.items() if len(members) >= 3]
        if not eligible_values:
            continue
        rng.shuffle(eligible_values)
        value = eligible_values[0]
        trio = rng.sample(groups[value], 3)
        decoy_values = [v for v in groups if v != value and len(groups[v]) >= 1]
        if len(decoy_values) < 3:
            continue
        rng.shuffle(decoy_values)
        decoys = decoy_values[:3]
        template = _STATEMENT_TEMPLATES[link_type]
        return {
            "names": [r["player_name"] for r in trio], "correct_statement": template(value),
            "decoy_statements": [template(d) for d in decoys],
            "notes": f"These 3 real players really share the same real {link_type.replace('_', ' ')}: "
                     f"{value} (NFLVERSE_DATA, SOURCE_BACKED).",
        }
    return None


def _fetch_rows_roster(c) -> list[dict]:
    rows = c.execute(
        "SELECT rs.player_id, p.display_name AS player_name, rs.season, rs.team_code AS team, rs.position "
        "FROM canonical_roster_seasons rs JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA' AND rs.position IS NOT NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def _build_round_roster(rng, rows: list[dict], groups_by_type: dict[str, dict]) -> dict | None:
    link_types = list(_ROSTER_LINK_TYPES)
    rng.shuffle(link_types)
    for link_type in link_types:
        groups = groups_by_type[link_type]
        # Same real reason as the CFB dedup below: a player has one row
        # per season, so "team"/"position" pools can list the same real
        # person many times -- a trio must be 3 genuinely DISTINCT people.
        eligible_values = []
        for v, members in groups.items():
            distinct = {m["player_id"]: m for m in members}
            if len(distinct) >= 3:
                eligible_values.append(v)
        if not eligible_values:
            continue
        rng.shuffle(eligible_values)
        value = eligible_values[0]
        distinct_members = list({m["player_id"]: m for m in groups[value]}.values())
        trio = rng.sample(distinct_members, 3)
        decoy_values = [v for v in groups if v != value and len(groups[v]) >= 1]
        if len(decoy_values) < 3:
            continue
        rng.shuffle(decoy_values)
        decoys = decoy_values[:3]
        template = _ROSTER_STATEMENT_TEMPLATES[link_type]
        return {
            "names": [r["player_name"] for r in trio], "correct_statement": template(value),
            "decoy_statements": [template(d) for d in decoys],
            "notes": f"These 3 real players really share the same real {link_type}: "
                     f"{value} (NFLVERSE_DATA, SOURCE_BACKED).",
        }
    return None


def _fetch_rows_cfb(c) -> list[dict]:
    rows = c.execute(
        "SELECT s.cfb_player_id, s.player_name, s.season, sc.school_name AS school, s.conference "
        "FROM cfb_player_season_stats_real s JOIN schools sc ON sc.school_id = s.school_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED' AND s.source_id='SPORTSDATAVERSE_CFB' "
        "AND s.passing_yards > 1500 AND s.conference IS NOT NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def _build_round_cfb(rng, rows: list[dict], groups_by_type: dict[str, dict]) -> dict | None:
    link_types = list(_CFB_LINK_TYPES)
    rng.shuffle(link_types)
    for link_type in link_types:
        groups = groups_by_type[link_type]
        # A season-level table can list the same real player twice (once
        # per season) -- a trio must be 3 genuinely DISTINCT real players,
        # never the same real person counted twice.
        eligible_values = []
        for v, members in groups.items():
            distinct = {m["cfb_player_id"]: m for m in members}
            if len(distinct) >= 3:
                eligible_values.append(v)
        if not eligible_values:
            continue
        rng.shuffle(eligible_values)
        value = eligible_values[0]
        distinct_members = list({m["cfb_player_id"]: m for m in groups[value]}.values())
        trio = rng.sample(distinct_members, 3)
        decoy_values = [v for v in groups if v != value and len(groups[v]) >= 1]
        if len(decoy_values) < 3:
            continue
        rng.shuffle(decoy_values)
        decoys = decoy_values[:3]
        template = _CFB_STATEMENT_TEMPLATES[link_type]
        return {
            "names": [r["player_name"] for r in trio], "correct_statement": template(value),
            "decoy_statements": [template(d) for d in decoys],
            "notes": f"These 3 real CFB players really share the same real {link_type}: "
                     f"{value} (SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED).",
        }
    return None


def generate_rounds(seed: str, variant: str, round_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    is_cfb = variant == "CFB_SEASON_COMMON_LINK"
    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if is_cfb:
            rows = _fetch_rows_cfb(c)
            groups_by_type = {lt: _group_by(rows, lt) for lt in _CFB_LINK_TYPES}
        else:
            draft_rows = _fetch_rows(c)
            draft_groups = {lt: _group_by(draft_rows, lt) for lt in _LINK_TYPES}
            roster_rows = _fetch_rows_roster(c)
            roster_groups = {lt: _group_by(roster_rows, lt) for lt in _ROSTER_LINK_TYPES}
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        if is_cfb:
            rng = engine_bootstrap.seeded(f"{seed}-cl-r{i}")
            r = _build_round_cfb(rng, rows, groups_by_type)
        else:
            # Category variety pass: which real, independent pool a round
            # draws from (DRAFT vs ROSTER) is itself seeded/deterministic,
            # tried in a real fallback order if the chosen pool can't
            # build a round rather than silently dropping it.
            cat_rng = engine_bootstrap.seeded(f"{seed}-cl-cat-{i}")
            pools = ["DRAFT", "ROSTER"]
            cat_rng.shuffle(pools)
            r = None
            for pool_name in pools:
                rng = engine_bootstrap.seeded(f"{seed}-cl-r{i}-{pool_name}")
                if pool_name == "DRAFT":
                    r = _build_round(rng, draft_rows, draft_groups)
                else:
                    r = _build_round_roster(rng, roster_rows, roster_groups)
                if r is not None:
                    break
        if r is None:
            continue
        rounds.append(r)

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real COMMON_LINK rounds could be built with a "
            f"real, decoy-complete shared-attribute trio; exported the maximum available rather than "
            f"include a fabricated link."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_COMMON_LINK": "Common Link", "CFB_SEASON_COMMON_LINK": "Common Link (CFB)"}


def build_package(seed: str, variant: str, round_count: int = 8) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP38:" + hashlib.sha256(
        f"COMMON_LINK|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_statement"]] + list(r["decoy_statements"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-cl-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "names": r["names"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "3 real NFL Draft picks are named -- tap the 1 of 4 real statements that "
                              "correctly explains what connects them.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
