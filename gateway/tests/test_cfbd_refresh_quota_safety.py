"""Regression guard for a real bug found while wiring the 5 CFBD-dependent
CFB refresh scripts (betting lines, postseason games, PBP, rankings,
standings) into production: CFBD is a metered, PAID API (free tier: 1000
calls/month), unlike every other source in this codebase. The Gateway's
admin dispatcher always calls a refresh function with NO arguments
(run_fn_for() returns the bare function, scheduled via Netlify cron with no
season parameter) -- so `seasons=None` (the no-args default) must mean
"just the current season," never a full 2002-present resweep, or a weekly
schedule would burn hundreds of real paid API calls for historical data
that never changes.

A second, more dangerous bug came from fixing the first one carelessly:
three of the five scripts (betting_lines/rankings/standings) DELETE-and-
republish per run, and their delete logic originally branched on the
ORIGINAL `seasons is not None` check -- after narrowing the fetch to just
the current season, a no-args call would still take the "DELETE
WHERE source_id=?" (delete EVERYTHING for this source) branch, silently
wiping every prior season's real, already-imported history on every
scheduled run while only re-fetching one season back. The post-refresh
`min_row_count_floor` sanity check would have caught this (triggering an
automatic restore-from-backup), but that's a safety net catching a bug, not
a fix -- every scheduled run would fail and restore, forever.

This test suite does NOT invoke any of the five real run_*_refresh()
functions -- doing so would hit CFBD's live, metered API and cost real
quota on every test run, which this project treats as a real resource
(see _cfbd_client.py's own module docstring). Instead it verifies, at the
source level, that both fixes are actually present -- a real regression
guard against either bug being silently reintroduced by a future edit, not
a network-touching integration test.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CFBD_SCRIPTS = [
    "cfb_betting_lines_refresh",
    "cfb_games_postseason_refresh",
    "cfb_pbp_refresh",
    "cfb_rankings_refresh",
    "cfb_standings_refresh",
]
DELETE_SCOPED_SCRIPTS = ["cfb_betting_lines_refresh", "cfb_rankings_refresh", "cfb_standings_refresh"]


def _source(name: str) -> str:
    return (REPO_ROOT / "tools" / "data_refresh" / f"{name}.py").read_text()


def test_every_cfbd_script_defaults_to_current_season_only_not_full_resweep():
    for name in CFBD_SCRIPTS:
        src = _source(name)
        assert "target_seasons = seasons if seasons is not None else [MAX_SEASON_ATTEMPT]" in src, (
            f"{name}.py must default a no-args call to the CURRENT season only -- "
            f"CFBD is a metered API and a scheduled no-args call must never re-sweep "
            f"the full historical range."
        )
        # The dangerous prior default -- a real regression guard, not just
        # checking the fix is present but that the bug's exact old shape
        # (a no-args call silently expanding to the full historical range)
        # hasn't come back.
        assert "seasons if seasons is not None else list(range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1))" not in src


def test_delete_scoped_cfbd_scripts_never_wipe_full_history_on_a_no_args_call():
    for name in DELETE_SCOPED_SCRIPTS:
        src = _source(name)
        # The real bug: a branch keyed on the ORIGINAL `seasons` parameter
        # (not `target_seasons`) that deletes every row for this source_id
        # with no season filter at all -- exactly the shape a no-args
        # scheduled call would have hit after narrowing the fetch to one
        # season but leaving the delete unscoped.
        forbidden = re.compile(r"else:\s*\n\s*c\.execute\(\"DELETE FROM \w+ WHERE source_id=\?\"")
        assert not forbidden.search(src), (
            f"{name}.py has an unscoped 'delete everything for this source' branch -- "
            f"a no-args scheduled call (current season only) would wipe every prior "
            f"season's real, already-imported history."
        )
        # The real fix: delete is always scoped to target_seasons (an
        # executemany over one row per target season), regardless of
        # whether the caller passed an explicit seasons list.
        assert "WHERE source_id=? AND season=?" in src
        assert "[(SOURCE_ID, s) for s in target_seasons]" in src


def test_cfbd_scripts_are_wired_into_the_admin_dispatcher():
    """The other half of "finishing the phase" -- these scripts existing on
    disk with correct internal logic doesn't matter if nothing can ever
    call them in production. See gateway/tests/test_admin_refresh.py's own
    test_run_fn_for_covers_engine_gap_audit_continuation_cfbd_datasets for
    the full check; this is a narrower guard that the five dataset keys
    specifically resolve to the five CFBD-key-dependent modules."""
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from gateway.services import admin_refresh
    from tools.data_refresh import (
        cfb_betting_lines_refresh, cfb_games_postseason_refresh, cfb_pbp_refresh,
        cfb_rankings_refresh, cfb_standings_refresh,
    )

    expected = {
        "cfb_betting_lines": cfb_betting_lines_refresh.run_cfb_betting_lines_refresh,
        "cfb_games_postseason": cfb_games_postseason_refresh.run_cfb_games_postseason_refresh,
        "cfb_pbp": cfb_pbp_refresh.run_cfb_pbp_refresh,
        "cfb_rankings": cfb_rankings_refresh.run_cfb_rankings_refresh,
        "cfb_standings": cfb_standings_refresh.run_cfb_standings_refresh,
    }
    for key, fn in expected.items():
        assert admin_refresh.run_fn_for(key) is fn
