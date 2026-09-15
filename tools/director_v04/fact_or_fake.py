"""FACT_OR_FAKE -- 75-Format Expansion (Wave 1), format #28 overall.

Real true/false judgment: each round shows one real NFL Draft statement
("<Team> drafted <Player> in the <Season> NFL Draft with pick #<N>.").
Half the rounds (deterministically, per-seed) are shown VERBATIM (a real,
true fact); the other half swap in a DIFFERENT real team that drafted a
DIFFERENT real player that same real draft class -- a provably false
statement by real entity substitution, never a fabricated or randomly-
altered number (per the user's own spec: "False statements must be
provably false. Prefer verified contradictions/entity substitutions
rather than random number manipulation."). The player taps TRUE or FAKE.

Reuses tools.director_v04.risk_it's own real, already-certified
draft_facts query pattern (same table, same real season-grouping) rather
than a second, possibly-diverging copy of that data logic.

Single variant: NFL_DRAFT_FACT_OR_FAKE.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import risk_it  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "FACT_OR_FAKE"
VARIANTS = frozenset({"NFL_DRAFT_FACT_OR_FAKE"})


def safety_check(c) -> dict:
    return risk_it.safety_check(c)


def _rows_by_season(c) -> dict[int, list]:
    rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_team, draft_pick_overall FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' AND draft_team IS NOT NULL"
    ).fetchall()
    by_season: dict[int, list] = {}
    for r in rows:
        by_season.setdefault(r["draft_season"], []).append(r)
    return by_season


def _statement_for(row) -> str:
    return (f"The {row['draft_team']} drafted {row['player_name']} in the {row['draft_season']} "
            f"NFL Draft with pick #{row['draft_pick_overall']}.")


def _build_round(rng, by_season: dict[int, list], make_true: bool) -> dict | None:
    seasons = list(by_season.keys())
    rng.shuffle(seasons)
    for season in seasons:
        pool = by_season[season]
        if len(pool) < 2:
            continue
        subject = rng.choice(pool)
        if make_true:
            return {"statement": _statement_for(subject), "is_true": True,
                    "notes": f"Real, verbatim {season} NFL Draft fact (NFLVERSE_DATA, SOURCE_BACKED)."}
        other_teams = [r for r in pool if r["draft_team"] != subject["draft_team"]]
        if not other_teams:
            continue
        fake_team_row = rng.choice(other_teams)
        fake_row = dict(subject)
        fake_row["draft_team"] = fake_team_row["draft_team"]
        return {
            "statement": _statement_for(fake_row), "is_true": False,
            "notes": f"Provably false by real entity substitution: {subject['draft_team']} really drafted "
                     f"{subject['player_name']} in {season} (pick #{subject['draft_pick_overall']}) -- "
                     f"{fake_team_row['draft_team']} really drafted a different real player with that class's "
                     f"real pick #{fake_team_row['draft_pick_overall']} instead (NFLVERSE_DATA, SOURCE_BACKED).",
        }
    return None


def generate_rounds(seed: str, variant: str, round_count: int = 10) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        by_season = _rows_by_season(c)
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        make_true = (i % 2 == 0)  # deterministic 50/50 split, never a coin flip that could skew a short run
        r = _build_round(engine_bootstrap.seeded(f"{seed}-fof-r{i}"), by_season, make_true)
        if r is None:
            continue
        rounds.append(r)

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real FACT_OR_FAKE rounds could be built with a "
            f"real, provably-true-or-false statement; exported the maximum available rather than include a "
            f"fabricated one."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_FACT_OR_FAKE": "Fact or Fake"}


def build_package(seed: str, variant: str, round_count: int = 10) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP30:" + hashlib.sha256(
        f"FACT_OR_FAKE|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = [{"round_index": i, "statement": r["statement"], "_is_true": r["is_true"], "_notes": r["notes"]}
              for i, r in enumerate(result["rounds"])]

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Read the real statement -- tap TRUE if it's a real, verbatim fact, or FAKE if "
                              "it's been altered.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
