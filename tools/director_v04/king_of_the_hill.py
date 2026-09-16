"""KING_OF_THE_HILL -- 75-Format Expansion (Wave 1), format #27 overall.

Real persistent-champion gauntlet: one real NFL team-season starts as
champion. Each round, the player predicts whether the current CHAMPION or
the next real CHALLENGER has the higher real win total that real season.
A correct prediction resolves the real matchup honestly: if the champion
really did have more real wins, it stays champion and its real
"consecutive defenses" count increments; if the challenger really had
more real wins, the challenger becomes the new real champion and
defenses reset to 0. A wrong prediction ends the run immediately.

Reuses tools.director_v04.higher_lower's own real, already-certified
season_standings query (_nfl_items) verbatim -- same real data, same
real tie-exclusion-by-construction discipline (every item's real win
total is distinct from every other item's, so no comparison can ever
tie), new rules only.

Deliberately distinct from LEADERBOARD_CLIMB (protected, 15-Format
Expansion): LEADERBOARD_CLIMB moves through a FIXED, PRE-SORTED real
leaderboard -- the next comparison is always deterministically the next-
better real rank, so a correct run only ever climbs monotonically.
KING_OF_THE_HILL compares the champion against a RANDOM, unsorted
sequence of real challengers -- the champion can survive an arbitrarily
long or short real gauntlet purely based on how strong each random real
challenger happens to be, and getting dethroned is a real possibility at
any point, not a guaranteed eventual outcome of climbing toward a known
top. Also distinct from HIGHER_LOWER_STREAK: that format has no
persistent "champion" concept at all, just a plain sequential streak
against the next item in a shuffled real sequence.

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also"):
added CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL, reusing higher_lower.py's own
already-certified `_cfb_items()` verbatim (cfb_standings.total_wins, FBS
programs only, CFBD_API_LIVE/SOURCE_BACKED) -- zero new data work, same
real tie-exclusion-by-construction discipline as the NFL variant.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import higher_lower  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "KING_OF_THE_HILL"
VARIANTS = frozenset({"NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL", "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL"})
SEQUENCE_LENGTH = 16


def safety_check(c) -> dict:
    full = higher_lower.safety_check(c)
    return {"season_standings": full["season_standings"], "cfb_standings": full["cfb_standings"]}


def generate_items(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        items = (higher_lower._cfb_items(c, seed, SEQUENCE_LENGTH)
                 if variant == "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL"
                 else higher_lower._nfl_items(c, seed, SEQUENCE_LENGTH))
    finally:
        c.close()

    league_label = "CFB" if variant == "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL" else "NFL"
    shortfall_reason = None
    if len(items) < 4:
        shortfall_reason = (
            f"Only {len(items)} real, distinct-win-total {league_label} team-seasons were found -- too few "
            f"real challengers to honestly support a King of the Hill run."
        )
    return {"items": items, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {
    "NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL": "King of the Hill",
    "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL": "King of the Hill (CFB)",
}


def build_package(seed: str, variant: str) -> dict:
    result = generate_items(seed, variant)
    package_id = "GGP29:" + hashlib.sha256(
        f"KING_OF_THE_HILL|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    items = result["items"]
    valid = len(items) >= 4
    league_label = "CFB" if variant == "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL" else "NFL"

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": f"One real {league_label} team-season is the champion. Predict whether the "
                              "champion or the next real challenger really had more real wins that season -- "
                              "a correct prediction keeps the gauntlet going (the real winner becomes/stays "
                              "champion); a wrong prediction ends your run.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "items": [{"label": it["label"], "value": it["_private_value"]} for it in items],
        "item_count": len(items),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
