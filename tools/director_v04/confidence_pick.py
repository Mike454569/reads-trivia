"""CONFIDENCE_PICK -- 15-Format Expansion Part 2, format #13.

Real NFL confidence-pool pick'em: reuses WEEKLY_PICKEM's own real,
live-graded weekly slate (tools/director_v04/weekly_pickem.py) for the
exact same real games and the exact same real per-game kickoff-lock and
live-grading discipline -- this format adds nothing to how a game's real
winner is determined. It layers one real, classic confidence-pool rule
on top: each confidence value from 1 to N (N = the real number of games
in the slate) must be assigned to exactly one real game's pick, no
repeats. A correct pick earns real points equal to its confidence value;
an incorrect pick earns 0. Final score is the sum across all real graded
picks.

Real per-game truth is NOT settled at generation time (most of a real
week's games haven't been played yet) -- same real "recompute live on
every call, never cache a result" discipline WEEKLY_PICKEM's own module
docstring establishes, reused verbatim via
weekly_pickem.live_game_statuses().

Single variant: NFL_CONFIDENCE_PICK. Reuses NFL_WEEKLY_PICKEM's own real
slate-fetching and current-week resolution (tools/director_v04/
nl_schedule_bridge.py's resolve_current_week(), the same real function
gateway/services/public_pickem.py's own production route already uses).
CFB is not offered yet -- cfb_games_canonical's own real week-labeling
quirks (already disclosed in weekly_pickem.py's own module docstring:
regular-season, bowls, and CFP games can share the same literal `week`
value) make an honest CFB confidence slate a separate, not-yet-attempted
scope.
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
MECHANIC = "CONFIDENCE_PICK"
VARIANTS = frozenset({"NFL_CONFIDENCE_PICK"})
MIN_GAMES_FOR_SLATE = 2  # a confidence ranking needs at least 2 real games to be meaningful


def _resolve_week(season, week):
    from tools.director_v04 import nl_schedule_bridge

    resolved_season = season if season is not None else datetime.now(timezone.utc).year
    resolved_week = week
    if resolved_week is None:
        c = engine_bootstrap.connect()
        try:
            resolved_week = nl_schedule_bridge.resolve_current_week(c, "NFL", resolved_season)
        finally:
            c.close()
    return resolved_season, resolved_week


def build_package(seed: str, variant: str, season: int | None = None, week=None) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    from tools.director_v04 import weekly_pickem

    resolved_season, resolved_week = _resolve_week(season, week)
    package_id = "GGP25:" + hashlib.sha256(
        f"CONFIDENCE_PICK|{variant}|{resolved_season}|{resolved_week}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]

    if resolved_week is None:
        return {
            "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
            "domain_variant": variant, "season": resolved_season, "week": None,
            "game_title": "Confidence Pick", "game_instructions": "",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "qa_status": "FAILED", "games": [], "game_count": 0, "max_confidence": 0,
            "production_safety": {},
            "shortfall_reason": f"No real NFL schedule exists yet for {resolved_season} to resolve a "
                                 f"current week from.",
            "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
        }

    slate_pkg = weekly_pickem.build_package(seed, "NFL_WEEKLY_PICKEM", resolved_season, resolved_week)
    games = slate_pkg["games"]
    n = len(games)
    valid = slate_pkg["qa_status"] == "PASSED" and n >= MIN_GAMES_FOR_SLATE

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "season": resolved_season, "week": resolved_week,
        "game_title": "Confidence Pick",
        "game_instructions": f"Pick every real game's winner, then assign each pick a unique real "
                              f"confidence value from 1 to {n} -- your highest-confidence picks are worth "
                              f"the most points if correct.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "games": games, "game_count": n, "max_confidence": n,
        "production_safety": slate_pkg["production_safety"],
        "shortfall_reason": None if valid else (
            slate_pkg["shortfall_reason"] or
            f"Only {n} real game(s) are scheduled for {resolved_season} week {resolved_week} -- a "
            f"confidence ranking needs at least {MIN_GAMES_FOR_SLATE} to be meaningful."
        ),
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
