"""HIGHER_LOWER_STREAK -- Reliability Design Phase 6, real mechanic
template #5.

A real, server-authoritative rebuild. The existing `higherLower` mode in
app.js is entirely CLIENT-SIDE: every player's stat value is already
present in the static data files it loads (data/grid.js, data/higher-
lower-extra.js) before a single guess is made -- there is no server, no
private value, nothing preventing a browser devtools inspection of the
"hidden" next value. That fails this phase's own "never send an answer key
... before it is allowed to be revealed" requirement by construction, so
it is NOT reused here -- this is a real, new, server-authoritative
implementation, built from scratch on already-certified real tables (only
the CSS/interaction *pattern* from that existing mode is worth carrying
into a future frontend; none of its data path is safe to reuse).

Two real, disclosed variants -- team-season real win totals, same-domain,
tie-excluded by construction (every item in one sequence has a distinct
value, so no two compared items can ever tie):
  - NFL_TEAM_SEASON_WINS: `season_standings.wins` (NFLVERSE_DATA,
    SOURCE_BACKED -- the same table NFL_CHAMPIONSHIP/NFL_SUPER_BOWL
    already use).
  - CFB_TEAM_SEASON_WINS: `cfb_standings.total_wins`, FBS programs only
    (CFBD_API_LIVE, SOURCE_BACKED) -- same FBS-only reasoning as
    elimination.py's CFB variant (a non-FBS win total isn't a fair
    same-domain comparison against an FBS program).
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
MECHANIC = "HIGHER_LOWER_STREAK"
MIN_SEQUENCE_LENGTH = 8

VARIANTS = frozenset({"NFL_TEAM_SEASON_WINS", "CFB_TEAM_SEASON_WINS"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "season_standings": safety.check_table_wide_safety(c, "season_standings", "NFLVERSE_DATA"),
        "cfb_standings": safety.check_table_wide_safety(c, "cfb_standings", "CFBD_API_LIVE"),
    }


def _nfl_items(c, seed: str, sequence_length: int) -> list[dict]:
    rows = c.execute(
        "SELECT season, team_code, wins FROM season_standings "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' AND wins IS NOT NULL"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    order = list(rows)
    rng.shuffle(order)

    items, seen_values = [], set()
    for r in order:
        if len(items) >= sequence_length:
            break
        if r["wins"] in seen_values:
            continue  # tie-exclusion: every item's value is distinct from every other item's
        fr, err = resolve_franchise(c, r["team_code"], r["season"])
        if err or fr is None:
            continue
        seen_values.add(r["wins"])
        items.append({
            "label": f"{fr['full_name']} ({r['season']})", "_private_value": r["wins"],
            "_audit": {"season": r["season"], "team_code": r["team_code"], "franchise_id": fr["franchise_id"]},
        })
    return items


def _cfb_items(c, seed: str, sequence_length: int) -> list[dict]:
    rows = c.execute(
        "SELECT season, school_id, school_name_raw, total_wins FROM cfb_standings "
        "WHERE verification_status='SOURCE_BACKED' AND classification='fbs' AND total_wins IS NOT NULL"
    ).fetchall()
    school_names = {r["school_id"]: r["school_name"] for r in c.execute("SELECT school_id, school_name FROM schools")}
    rng = engine_bootstrap.seeded(seed)
    order = list(rows)
    rng.shuffle(order)

    items, seen_values = [], set()
    for r in order:
        if len(items) >= sequence_length:
            break
        if r["total_wins"] in seen_values:
            continue
        name = school_names.get(r["school_id"]) or r["school_name_raw"]
        seen_values.add(r["total_wins"])
        items.append({
            "label": f"{name} ({r['season']})", "_private_value": r["total_wins"],
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
        items = _nfl_items(c, seed, sequence_length) if variant == "NFL_TEAM_SEASON_WINS" \
            else _cfb_items(c, seed, sequence_length)
    finally:
        c.close()

    for i, item in enumerate(items):
        item["item_index"] = i

    shortfall_reason = None
    if len(items) < sequence_length:
        shortfall_reason = (
            f"Only {len(items)} of {sequence_length} requested real HIGHER_LOWER_STREAK items could be "
            f"built for variant={variant!r} with a genuinely distinct real win total each (tie-exclusion); "
            f"exported the maximum available rather than allow a tied comparison."
        )
    return {
        "items": items, "safety": safety_result, "shortfall_reason": shortfall_reason,
        "comparison_attribute": "real regular-season win total",
    }


def build_package(seed: str, variant: str, sequence_length: int = 12) -> dict:
    result = generate_sequence(seed, variant, sequence_length=sequence_length)
    package_id = "GGP8:" + hashlib.sha256(
        f"HIGHERLOWER|{variant}|{seed}|{sequence_length}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "NFL Wins Streak" if variant == "NFL_TEAM_SEASON_WINS" else "CFB Wins Streak",
        "game_instructions": f"Guess whether the next real team-season had a higher or lower "
                              f"{result['comparison_attribute']} than the one shown. One miss ends the streak.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if len(result["items"]) >= MIN_SEQUENCE_LENGTH else "FAILED",
        "sequence": result["items"], "sequence_length": len(result["items"]),
        "comparison_attribute": result["comparison_attribute"],
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
