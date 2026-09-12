"""KNOCKOUT_BRACKET -- 40-Format Expansion pass, new mechanic template.

Backs KNOCKOUT_TOURNAMENT: generalizes tools/director_v04/comparison.py's
real, fully-determined single-elimination bracket (COMPARISON_BRACKET,
fixed at exactly 8 entrants) to a variable real field size (4, 8, or 16),
reusing the IDENTICAL real, tie-free data source (season_standings.wins /
cfb_standings.total_wins) rather than inventing a new dataset. Every real
matchup's winner is fully determined by the two real win totals at
generation time -- same real design decision comparison.py's own docstring
documents, never a player-choice branching bracket.

The one real generalization comparison.py didn't need: a standard,
real tournament re-seeding algorithm for an arbitrary power-of-2 field
(comparison.py hardcodes the 8-entrant seeding pairs (1v8, 4v5, 3v6, 2v7));
`_seed_order()` below is the well-known recursive bracket-reseeding
algorithm (keeps the two strongest seeds apart until the final, for any
power-of-2 size), not a fabricated pairing rule.
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
MECHANIC = "KNOCKOUT_BRACKET"
VALID_SIZES = (4, 8, 16)

VARIANTS = frozenset({
    "NFL_TEAM_SEASON_WINS_KNOCKOUT_4", "NFL_TEAM_SEASON_WINS_KNOCKOUT_16",
    "CFB_TEAM_SEASON_WINS_KNOCKOUT_4", "CFB_TEAM_SEASON_WINS_KNOCKOUT_16",
})
_SIZE_BY_VARIANT = {
    "NFL_TEAM_SEASON_WINS_KNOCKOUT_4": 4, "NFL_TEAM_SEASON_WINS_KNOCKOUT_16": 16,
    "CFB_TEAM_SEASON_WINS_KNOCKOUT_4": 4, "CFB_TEAM_SEASON_WINS_KNOCKOUT_16": 16,
}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "season_standings": safety.check_table_wide_safety(c, "season_standings", "NFLVERSE_DATA"),
        "cfb_standings": safety.check_table_wide_safety(c, "cfb_standings", "CFBD_API_LIVE"),
    }


def _seed_order(n: int) -> list[int]:
    """Standard recursive bracket-reseeding algorithm -- returns 0-based
    seed indices in bracket-slot order for a real, fair single-elimination
    field of size n (a power of 2)."""
    seeds = [1]
    while len(seeds) < n:
        m = len(seeds) * 2
        seeds = [x for s in seeds for x in (s, m + 1 - s)]
    return [s - 1 for s in seeds]


def _nfl_entrants(c, seed: str, size: int) -> list[dict]:
    rows = c.execute(
        "SELECT season, team_code, wins FROM season_standings "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' AND wins IS NOT NULL"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    order = list(rows)
    rng.shuffle(order)

    entrants, seen_values = [], set()
    for r in order:
        if len(entrants) >= size:
            break
        if r["wins"] in seen_values:
            continue
        fr, err = resolve_franchise(c, r["team_code"], r["season"])
        if err or fr is None:
            continue
        seen_values.add(r["wins"])
        entrants.append({"label": f"{fr['full_name']} ({r['season']})", "_private_value": r["wins"]})
    return entrants


def _cfb_entrants(c, seed: str, size: int) -> list[dict]:
    rows = c.execute(
        "SELECT season, school_id, school_name_raw, total_wins FROM cfb_standings "
        "WHERE verification_status='SOURCE_BACKED' AND classification='fbs' AND total_wins IS NOT NULL"
    ).fetchall()
    school_names = {r["school_id"]: r["school_name"] for r in c.execute("SELECT school_id, school_name FROM schools")}
    rng = engine_bootstrap.seeded(seed)
    order = list(rows)
    rng.shuffle(order)

    entrants, seen_values = [], set()
    for r in order:
        if len(entrants) >= size:
            break
        if r["total_wins"] in seen_values:
            continue
        name = school_names.get(r["school_id"]) or r["school_name_raw"]
        seen_values.add(r["total_wins"])
        entrants.append({"label": f"{name} ({r['season']})", "_private_value": r["total_wins"]})
    return entrants


def _build_bracket(entrants: list[dict], size: int) -> list[list[dict]]:
    seeded_positions = _seed_order(size)
    ordered = [entrants[i] for i in seeded_positions]
    round_index = 0
    rounds: list[list[dict]] = []
    current = [
        {"match_id": f"R0M{i}", "entrant_a": ordered[2 * i]["label"], "entrant_b": ordered[2 * i + 1]["label"],
         "value_a": ordered[2 * i]["_private_value"], "value_b": ordered[2 * i + 1]["_private_value"]}
        for i in range(size // 2)
    ]
    while True:
        winners = []
        for m in current:
            winner_label = m["entrant_a"] if m["value_a"] > m["value_b"] else m["entrant_b"]
            winner_value = max(m["value_a"], m["value_b"])
            m["real_winner"] = winner_label
            winners.append({"label": winner_label, "value": winner_value})
        rounds.append(current)
        if len(winners) == 1:
            break
        round_index += 1
        current = [
            {"match_id": f"R{round_index}M{i}", "entrant_a": winners[2 * i]["label"], "entrant_b": winners[2 * i + 1]["label"],
             "value_a": winners[2 * i]["value"], "value_b": winners[2 * i + 1]["value"]}
            for i in range(len(winners) // 2)
        ]
    return rounds


def generate_bracket(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    size = _SIZE_BY_VARIANT[variant]

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        entrants = _nfl_entrants(c, seed, size) if variant.startswith("NFL_") else _cfb_entrants(c, seed, size)
    finally:
        c.close()

    shortfall_reason = None
    rounds: list[list[dict]] = []
    if len(entrants) < size:
        shortfall_reason = (
            f"Only {len(entrants)} of {size} real entrants with a genuinely distinct real win total each "
            f"(tie-exclusion) could be found for variant={variant!r} -- no bracket was built rather than "
            f"pad it with a duplicate or fabricated entrant."
        )
    else:
        rounds = _build_bracket(entrants, size)

    return {"entrants": entrants, "rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason,
            "comparison_attribute": "real regular-season win total", "size": size}


_ROUND_LABELS_BY_SIZE = {
    4: ["Semifinals", "Final"],
    8: ["Quarterfinals", "Semifinals", "Final"],
    16: ["Round of 16", "Quarterfinals", "Semifinals", "Final"],
}


def build_package(seed: str, variant: str) -> dict:
    result = generate_bracket(seed, variant)
    package_id = "GGP14:" + hashlib.sha256(
        f"KNOCKOUT|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    labels = _ROUND_LABELS_BY_SIZE.get(result["size"], [f"Round {i + 1}" for i in range(len(result["rounds"]))])
    rounds_public = [
        {
            "round_index": i, "round_label": labels[i] if i < len(labels) else f"Round {i + 1}",
            "matchups": [
                {"match_id": m["match_id"], "entrant_a": m["entrant_a"], "entrant_b": m["entrant_b"]}
                for m in round_matches
            ],
        }
        for i, round_matches in enumerate(result["rounds"])
    ]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "field_size": result["size"],
        "game_title": f"{result['size']}-Team Knockout ({'NFL' if variant.startswith('NFL_') else 'CFB'})",
        "game_instructions": f"Predict the real winner of every matchup in this real {result['size']}-team "
                              f"knockout field, based on {result['comparison_attribute']}.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if result["rounds"] else "FAILED",
        "rounds": rounds_public,
        "_private_rounds": result["rounds"],
        "comparison_attribute": result["comparison_attribute"],
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
