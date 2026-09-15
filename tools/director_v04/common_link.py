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

Single variant: NFL_DRAFT_COMMON_LINK.
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
VARIANTS = frozenset({"NFL_DRAFT_COMMON_LINK"})

_LINK_TYPES = ("college", "draft_season", "draft_team")
_STATEMENT_TEMPLATES = {
    "college": lambda v: f"They all played college football at {v}.",
    "draft_season": lambda v: f"They were all drafted in the {v} NFL Draft.",
    "draft_team": lambda v: f"They were all drafted by the {v}.",
}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {"draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA")}


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


def generate_rounds(seed: str, variant: str, round_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        rows = _fetch_rows(c)
    finally:
        c.close()

    groups_by_type = {lt: _group_by(rows, lt) for lt in _LINK_TYPES}

    rounds = []
    for i in range(round_count):
        r = _build_round(engine_bootstrap.seeded(f"{seed}-cl-r{i}"), rows, groups_by_type)
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


_GAME_TITLES = {"NFL_DRAFT_COMMON_LINK": "Common Link"}


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
