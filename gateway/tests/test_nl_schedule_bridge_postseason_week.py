"""Creator/Game Quality Correction pass -- real bug fix regression test.

tools/director_v04/nl_schedule_bridge.py's resolve_current_week() used to
scope its NFL query to game_type='REG' only. Once every real regular-season
week's date was in the past, it fell through to "the last REG week" (e.g.
"18") FOREVER -- including during a real, live postseason -- silently
resolving to an already-finished regular-season week instead of the live
Wild Card/Divisional/Conference/Super Bowl slate. Confirmed directly against
the real database before fixing: every fully-completed real NFL season
(2022-2025) resolved to "18" before this fix; each one's real, actual last-
played week is a postseason game_type (its Super Bowl), never REG week 18
itself (a completed season's REG week 18 games are never its own most
recent games).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

# Real, fully-completed NFL seasons (confirmed live against the real
# database) -- every one of these has a real, played Super Bowl in the
# past relative to any time this test could plausibly run.
_COMPLETED_SEASONS = (2022, 2023, 2024, 2025)


@pytest.mark.parametrize("season", _COMPLETED_SEASONS)
def test_resolve_current_week_returns_postseason_code_not_stale_reg_week(season):
    from tools.director_v04 import nl_schedule_bridge as bridge

    c = engine_bootstrap.connect()
    try:
        week = bridge.resolve_current_week(c, "NFL", season)
    finally:
        c.close()
    assert week in ("WC", "DIV", "CON", "SB"), (
        f"season {season}: expected a real postseason game_type code (its actual last-played week), "
        f"got {week!r} -- the stale-REG-week bug is back if this is '18'."
    )


@pytest.mark.parametrize("season", _COMPLETED_SEASONS)
def test_resolved_postseason_week_produces_a_real_nonempty_slate(season):
    """The whole point of the fix: the resolved week must actually be
    usable by weekly_pickem.py's own slate query, not just a valid-looking
    string."""
    from tools.director_v04 import nl_schedule_bridge as bridge
    from tools.director_v04 import weekly_pickem

    c = engine_bootstrap.connect()
    try:
        week = bridge.resolve_current_week(c, "NFL", season)
        rows = weekly_pickem._nfl_slate_rows(c, season, week)
    finally:
        c.close()
    assert len(rows) >= 1, f"season {season}, week {week!r}: resolved week has zero real games"
