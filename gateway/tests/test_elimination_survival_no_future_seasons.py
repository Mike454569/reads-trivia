"""Final Player-Facing Stress Test pass: a real, found defect --
ELIMINATION_SURVIVAL's NFL_SUPER_BOWL_CHAMPION_SURVIVAL variant was asking
players "Did the {team} win the Super Bowl following the {season} season?"
about the CURRENT, not-yet-played NFL season, as if that were an already-
resolved historical fact. Root cause: season_standings carries real
placeholder rows for the current season (one per team, playoff_result
NULL because no games have been played yet) -- for a real COMPLETED
season, NULL correctly means "missed the playoffs" (a real, valid false-
membership example), but for the current unplayed season it means "not
yet determined", a fundamentally different fact. Fixed by only
considering seasons that have at least one real non-NULL playoff_result
row at all -- a season with zero resolved rows hasn't been played out
yet, detected generically (never a hardcoded year)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import elimination  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _current_unresolved_nfl_season(c) -> int | None:
    """The real, live check: the most recent season in season_standings
    that has zero non-NULL playoff_result rows (i.e. hasn't been played
    out), if any. Mirrors the production logic independently so this test
    doesn't just re-check the same code path it's meant to guard."""
    seasons = [r["season"] for r in c.execute("SELECT DISTINCT season FROM season_standings").fetchall()]
    for season in seasons:
        resolved = c.execute(
            "SELECT COUNT(*) FROM season_standings WHERE season=? AND playoff_result IS NOT NULL", (season,)
        ).fetchone()[0]
        if resolved == 0:
            return season
    return None


def test_no_unresolved_season_ever_appears_in_a_generated_sequence():
    c = engine_bootstrap.connect()
    try:
        unresolved_season = _current_unresolved_nfl_season(c)
    finally:
        c.close()
    if unresolved_season is None:
        pytest.skip("no currently-unresolved NFL season in this database snapshot -- nothing to guard against right now")

    result = elimination.generate_sequence(
        seed="test-no-future-season", variant="NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10,
    )
    seasons_used = {item["_audit"]["season"] for item in result["items"]}
    assert unresolved_season not in seasons_used, (
        f"generated sequence asked about season {unresolved_season}, which has zero real resolved "
        f"playoff outcomes -- this presents an undetermined future fact as a resolved historical one"
    )


def test_nfl_super_bowl_survival_still_generates_a_real_sequence():
    """The fix must not empty out the whole real candidate pool -- NULL
    rows for genuinely completed seasons (real "missed the playoffs"
    facts) must still count as valid false examples."""
    result = elimination.generate_sequence(
        seed="test-still-generates", variant="NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10,
    )
    assert len(result["items"]) == 10
    assert any(item["_private_membership"] for item in result["items"])
    assert any(not item["_private_membership"] for item in result["items"])
