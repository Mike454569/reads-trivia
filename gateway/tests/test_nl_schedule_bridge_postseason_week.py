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


# --- Player-reported real bug: NFL showed "Week 2" while Week 1 was still
# in progress (user confirmed real-world: today 2026-09-11, real Week 1
# games run 2026-09-09 through 2026-09-14 -- only the Thursday opener had
# been played). resolve_current_week()'s NFL branch tested only
# first_date, so the instant the Thursday game's date passed, it treated
# the WHOLE week as over and jumped to Week 2 while 14 of 16 real games
# were still ahead. The CFB branch already had the correct "not yet
# concluded" (last_date-based) test for this exact bug class -- this locks
# in the NFL branch now matching it. CFB's own behavior is deliberately
# NOT touched or asserted here (the user was explicit CFB's week detection
# is already correct) -- see test_resolve_current_week_uses_last_date_not_
# first_date_for_cfb_too's sibling coverage elsewhere if that ever needs
# its own lock-in test.

def test_resolve_current_week_nfl_uses_last_date_not_first_date():
    """Direct, real-data reproduction of the reported bug: a real NFL week
    whose first game has already been played but whose last game has not
    must NOT be treated as concluded."""
    from tools.director_v04 import nl_schedule_bridge as bridge

    c = engine_bootstrap.connect()
    try:
        candidates = bridge._nfl_week_candidates(c, 2026)
    finally:
        c.close()
    week1 = next((cand for cand in candidates if cand[0] == "1"), None)
    assert week1 is not None, "real NFL 2026 Week 1 schedule rows are missing from this database"
    _, first_date, last_date = week1
    assert first_date < last_date, (
        "this test needs a real week whose games span multiple real days to mean anything -- "
        f"got first_date == last_date == {first_date!r}"
    )

    import datetime as _dt
    from unittest import mock

    # Pin "today" to a real date after Week 1's first game but before its
    # last one -- the exact real-world condition the user hit.
    pinned_today = _dt.datetime.fromisoformat(first_date).replace(tzinfo=_dt.timezone.utc) + _dt.timedelta(days=1)
    assert pinned_today.strftime("%Y-%m-%d") < last_date, "pinned date must still be before Week 1 concludes"

    class _FixedDatetime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return pinned_today

    c = engine_bootstrap.connect()
    try:
        with mock.patch.object(bridge, "datetime", _FixedDatetime):
            week = bridge.resolve_current_week(c, "NFL", 2026)
    finally:
        c.close()
    assert week == "1", f"expected Week 1 (still in progress), got {week!r} -- the first_date-only bug is back"
