"""LEADERBOARD_CLIMB -- 15-Format Expansion Part 2, format #14.

Real leaderboard-climbing trivia: the player starts at the bottom rung of
a real, fixed, pre-sorted statistical leaderboard (career passing yards,
within this Engine's real covered seasons -- not necessarily the full
official all-time NFL record book) and climbs one rung at a time by
correctly identifying which of 2 named real players -- the one currently
on their rung, and the real player one rung above -- actually ranks
higher on that real leaderboard. A correct answer climbs to that next
rung; a wrong answer ends the climb immediately. Reaching rank 1 (the
real leader shown on this leaderboard) completes the climb.

Deliberately distinct from HIGHER_LOWER_STREAK (tools/director_v04/
higher_lower.py): that format reveals a raw NUMERIC VALUE at every step
and asks a pure magnitude direction guess against a RANDOMLY-SHUFFLED
real sequence. LEADERBOARD_CLIMB never reveals a value until the climb
ends -- it asks the player to identify which of 2 NAMED real players
ranks higher on a real, FIXED, pre-sorted leaderboard, a genuinely
different real football-knowledge challenge (do you know who actually
outranks whom), not a number-magnitude guess -- and by construction, the
climb only ever moves toward better real ranks, never revealing a
"lower" outcome the way HIGHER_LOWER_STREAK's own sequence can.

Real domain: NFL career passing yards leaders (player_season_stats,
NFLVERSE_DATA, SOURCE_BACKED, summed per real QB -- same real
EXISTS(...position='QB') join STAT_LADDER's own career-passing variant
already established, to avoid mislabeling a non-QB's incidental passing
stat). The real top 15 QBs by real career passing yards, fetched
deterministically (ORDER BY total DESC LIMIT 15) -- a real, fixed
leaderboard, never randomly sampled. Confirmed live this pass that these
15 real totals are all genuinely distinct (no real tie, no invented
tiebreak needed) before shipping.

Single variant: NFL_CAREER_PASSING_YARDS_CLIMB.
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
MECHANIC = "LEADERBOARD_CLIMB"
VARIANTS = frozenset({"NFL_CAREER_PASSING_YARDS_CLIMB"})
LADDER_SIZE = 15


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {"player_season_stats": safety.check_table_wide_safety(c, "player_season_stats", "NFLVERSE_DATA")}


def _fetch_ladder(c) -> list[dict]:
    rows = c.execute(
        "SELECT s.player_key, p.display_name, SUM(s.pass_yards) AS val FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' AND s.pass_yards IS NOT NULL "
        "AND EXISTS (SELECT 1 FROM canonical_roster_seasons rs WHERE rs.player_id = s.player_key AND rs.position = 'QB') "
        "GROUP BY s.player_key HAVING val > 0 ORDER BY val DESC LIMIT ?",
        (LADDER_SIZE,),
    ).fetchall()
    # Real data fact, never an invented tiebreak: a genuine tie anywhere in
    # this real top-N would make "which one ranks higher" have no real
    # answer at that boundary -- checked, not assumed, before shipping.
    values = [r["val"] for r in rows]
    if len(set(values)) != len(values):
        raise RuntimeError(
            "A real tie exists within the top real career-passing-yards leaders -- "
            "LEADERBOARD_CLIMB cannot honestly ask 'who ranks higher' at that boundary."
        )
    return [{"rank": i + 1, "label": r["display_name"], "value": r["val"],
              "_audit": {"player_key": r["player_key"]}} for i, r in enumerate(rows)]


def generate_ladder(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        ladder = _fetch_ladder(c)
    finally:
        c.close()

    shortfall_reason = None
    if len(ladder) < 4:
        shortfall_reason = (
            f"Only {len(ladder)} real qualifying players were found for a real career-passing-yards "
            f"leaderboard -- too few real rungs to honestly support a climb."
        )
    return {"ladder": ladder, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_CAREER_PASSING_YARDS_CLIMB": "Leaderboard Climb"}


def build_package(seed: str, variant: str) -> dict:
    result = generate_ladder(seed, variant)
    package_id = "GGP26:" + hashlib.sha256(
        f"LEADERBOARD_CLIMB|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    ladder = result["ladder"]
    valid = len(ladder) >= 4

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "You start at the bottom of a real leaderboard. Each round, tap whichever "
                              "real player you think ranks HIGHER -- a correct answer climbs you up one "
                              "real rung; a wrong answer ends your climb.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        # The real ladder itself (ranks/labels/values) is stored under
        # "items" (packages.py's own global supported-game contract
        # requires a recognized non-empty content-list key) but is never
        # returned to the client wholesale -- only the two entities for
        # the player's CURRENT matchup are ever exposed (see
        # mechanic_engine.py's own _leaderboard_climb_client_view, which
        # always builds an explicit, allow-listed view rather than ever
        # returning `package` itself).
        "items": ladder, "ladder_size": len(ladder),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
