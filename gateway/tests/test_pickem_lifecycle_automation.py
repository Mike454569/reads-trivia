"""Priority-Zero Pick'em closeout: permanent, deterministic (frozen-clock)
regression coverage for the real weekly automation lifecycle -- schedule
ingestion, week resolution, per-game kickoff locking, automatic grading,
week/postseason rollover, and "a successful refresh reaches the player with
no manual publish step."

Root cause established live this pass (see the Pick'em Final Report): there
is no separate publish/cache/build layer to go stale -- get_pickem_view()
(gateway/services/public_pickem.py) and admin_pickem.pickem_health() both
call weekly_pickem.build_package()/live_game_statuses() fresh, every call,
directly against the `games`/`cfb_games_canonical` tables. The real,
observed production symptom (CFB Pick'em showing already-played games as
status UNKNOWN with no score) was the underlying refresh pipeline being
broken (root-owned directories, then a disk-full outage, fixed elsewhere
this pass) -- NOT a hidden slate-caching bug. These tests prove that
architecture holds by construction, using synthetic rows for a clearly
fake season (2099) that can never collide with real data, and a frozen
clock so no assertion depends on the real wall clock.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v02 import mechanic_engine  # noqa: E402
from tools.director_v04 import nl_schedule_bridge, weekly_pickem  # noqa: E402
from tools.data_refresh import _pickem_status  # noqa: E402
from gateway.services import admin_pickem, public_pickem  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

_TEST_SEASON = 2099  # far enough in the future to never collide with any real season on file


@pytest.fixture
def frozen_clock(monkeypatch):
    """Patches the `datetime` name every real Pick'em-lifecycle module
    imports (`from datetime import datetime, timezone` -- confirmed
    identical import shape in all 5 modules touched here) to a frozen
    subclass whose .now() always returns the given instant, regardless of
    the real wall clock. Real datetime.datetime otherwise, so isoformat/
    arithmetic/comparisons all behave normally."""
    def _freeze(instant: datetime):
        class _Frozen(datetime):
            @classmethod
            def now(cls, tz=None):
                return instant
        for mod in (nl_schedule_bridge, weekly_pickem, admin_pickem, public_pickem, _pickem_status, mechanic_engine):
            monkeypatch.setattr(mod, "datetime", _Frozen)
        return instant
    return _freeze


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


@pytest.fixture
def nfl_games():
    """Insert/cleanup helper for synthetic NFL `games` rows, season 2099."""
    inserted_ids: list[str] = []
    c = engine_bootstrap.connect()

    def _insert(game_id, *, week, game_type="REG", game_date, game_time="13:00",
                home_team="KC", away_team="BUF", home_score=None, away_score=None, status="SCHEDULED"):
        c.execute(
            "INSERT OR REPLACE INTO games(game_id, season, game_type, week, game_date, game_time, "
            "home_team, away_team, home_score, away_score, status, source_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,'NFLVERSE_DATA')",
            (game_id, _TEST_SEASON, game_type, week, game_date, game_time,
             home_team, away_team, home_score, away_score, status),
        )
        c.commit()
        inserted_ids.append(game_id)

    yield _insert
    for gid in inserted_ids:
        c.execute("DELETE FROM games WHERE game_id=?", (gid,))
    c.commit()
    c.close()


@pytest.fixture
def cfb_games():
    """Insert/cleanup helper for synthetic CFB `cfb_games_canonical` rows,
    season 2099. Uses 2 real school_ids (FK-safe even though this
    connection doesn't enforce FKs by default) and the real, approved
    SPORTSDATAVERSE_CFB source_id."""
    inserted_ids: list[str] = []
    c = engine_bootstrap.connect()

    def _insert(game_id, *, week, season_type="regular", game_date,
                home_school_id="CFB_SCHOOL_ABILENE_CHRISTIAN", away_school_id="CFB_SCHOOL_ADAMS_STATE",
                home_score=None, away_score=None, status="SCHEDULED",
                is_playoff=0, playoff_round=None):
        c.execute(
            "INSERT OR REPLACE INTO cfb_games_canonical(game_id, season, week, game_date, "
            "home_school_id, away_school_id, home_score, away_score, status, season_type, "
            "is_playoff, playoff_round, source_id, verification_status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'SPORTSDATAVERSE_CFB','SOURCE_BACKED')",
            (game_id, _TEST_SEASON, week, game_date, home_school_id, away_school_id,
             home_score, away_score, status, season_type, is_playoff, playoff_round),
        )
        c.commit()
        inserted_ids.append(game_id)

    yield _insert
    for gid in inserted_ids:
        c.execute("DELETE FROM cfb_games_canonical WHERE game_id=?", (gid,))
    c.commit()
    c.close()


# --- Scenario A: upcoming week is real and reachable with zero manual action --

def test_scenario_a_nfl_upcoming_week_available_automatically(frozen_clock, nfl_games):
    now = datetime(2099, 9, 4, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    nfl_games("2099_01_TEST_A", week=1, game_date=_iso(now + timedelta(days=3)))

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, "NFL", _TEST_SEASON)
    finally:
        c.close()
    assert week == "1"
    pkg = weekly_pickem.build_package("test-a-nfl", "NFL_WEEKLY_PICKEM", _TEST_SEASON, week)
    assert pkg["qa_status"] == "PASSED"
    assert any(g["game_id"] == "2099_01_TEST_A" for g in pkg["games"])


def test_scenario_a_cfb_upcoming_week_available_automatically(frozen_clock, cfb_games):
    now = datetime(2099, 8, 25, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    cfb_games("5099001", week=1, game_date=(now + timedelta(days=2)).isoformat())

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, "CFB", _TEST_SEASON)
    finally:
        c.close()
    assert week == "1"


# --- Scenario B: a schedule change (kickoff moves) reaches the player automatically --

def test_scenario_b_kickoff_change_reflected_with_no_republish(frozen_clock, nfl_games):
    now = datetime(2099, 9, 4, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    nfl_games("2099_01_TEST_B", week=1, game_date=_iso(now + timedelta(days=3)), game_time="13:00")

    pkg1 = weekly_pickem.build_package("test-b", "NFL_WEEKLY_PICKEM", _TEST_SEASON, "1")
    statuses1 = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", ["2099_01_TEST_B"])
    kickoff_before = statuses1["2099_01_TEST_B"]["kickoff_utc"]

    # A real upstream reschedule -- exactly what a normal refresh UPSERT does,
    # nothing Pick'em-specific.
    nfl_games("2099_01_TEST_B", week=1, game_date=_iso(now + timedelta(days=3)), game_time="20:00")

    statuses2 = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", ["2099_01_TEST_B"])
    kickoff_after = statuses2["2099_01_TEST_B"]["kickoff_utc"]
    assert kickoff_after != kickoff_before, "a real kickoff change must be reflected with no separate republish step"
    # Same real pick identity (game_id unchanged) -- existing picks would
    # still be attached to the correct game.
    assert weekly_pickem.build_package("test-b", "NFL_WEEKLY_PICKEM", _TEST_SEASON, "1")["games"][0]["game_id"] == "2099_01_TEST_B"


# --- Scenario C: partial gameday -- early games graded, late games still open --

def test_scenario_c_partial_gameday_grades_only_finished_games(frozen_clock, nfl_games):
    now = datetime(2099, 9, 14, 20, 0, tzinfo=timezone.utc)  # mid-Sunday
    frozen_clock(now)
    # Early game: kicked off well in the past, real final score on file.
    nfl_games("2099_01_TEST_C_EARLY", week=1, game_date=_iso(now - timedelta(hours=6)),
              game_time="13:00", home_score=27, away_score=20)
    # Late game: still hours away.
    nfl_games("2099_01_TEST_C_LATE", week=1, game_date=_iso(now + timedelta(hours=4)), game_time="20:20")

    statuses = weekly_pickem.live_game_statuses(
        "NFL_WEEKLY_PICKEM", ["2099_01_TEST_C_EARLY", "2099_01_TEST_C_LATE"])
    assert statuses["2099_01_TEST_C_EARLY"]["status"] == "FINAL"
    assert statuses["2099_01_TEST_C_EARLY"]["winner_code"] == "KC"
    assert statuses["2099_01_TEST_C_LATE"]["status"] == "SCHEDULED"


def test_scenario_c_late_game_pick_still_accepted_early_game_pick_rejected(frozen_clock, nfl_games):
    from tools.director_v02 import mechanic_engine

    now = datetime(2099, 9, 14, 20, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    nfl_games("2099_01_TEST_C2_EARLY", week=1, game_date=_iso(now - timedelta(hours=6)),
              game_time="13:00", home_score=27, away_score=20)
    nfl_games("2099_01_TEST_C2_LATE", week=1, game_date=_iso(now + timedelta(hours=4)), game_time="20:20")

    pkg = weekly_pickem.build_package("test-c2", "NFL_WEEKLY_PICKEM", _TEST_SEASON, "1")
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission(
            "WEEKLY_PICKEM", pkg, {"picks": {}}, {"game_id": "2099_01_TEST_C2_EARLY", "predicted_winner": "KC"})
    # The late game (still hours from kickoff) must remain pickable.
    mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, {"picks": {}}, {"game_id": "2099_01_TEST_C2_LATE", "predicted_winner": "KC"})


# --- Scenario D: week rollover happens automatically ------------------------

def test_scenario_d_nfl_week_rolls_over_once_week_one_fully_concludes(frozen_clock, nfl_games):
    now = datetime(2099, 9, 15, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    nfl_games("2099_01_TEST_D", week=1, game_date=_iso(now - timedelta(days=3)), home_score=20, away_score=10)
    nfl_games("2099_02_TEST_D", week=2, game_date=_iso(now + timedelta(days=4)))

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, "NFL", _TEST_SEASON)
    finally:
        c.close()
    assert week == "2", "once week 1's last real game has passed, week 2 must become current automatically"


def test_scenario_d_cfb_week_rolls_over_once_week_one_fully_concludes(frozen_clock, cfb_games):
    now = datetime(2099, 9, 8, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    cfb_games("5099010", week=1, game_date=(now - timedelta(days=3)).isoformat(), home_score=30, away_score=14)
    cfb_games("5099011", week=2, game_date=(now + timedelta(days=4)).isoformat())

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, "CFB", _TEST_SEASON)
    finally:
        c.close()
    assert week == "2"


# --- Scenario E: postseason rollover happens automatically ------------------

def test_scenario_e_nfl_rolls_into_postseason_automatically(frozen_clock, nfl_games):
    now = datetime(2100, 1, 12, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    nfl_games("2099_18_TEST_E", week=18, game_date=_iso(now - timedelta(days=20)), home_score=24, away_score=17)
    nfl_games("2099_WC_TEST_E", week=19, game_type="WC", game_date=_iso(now + timedelta(days=2)))

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, "NFL", _TEST_SEASON)
    finally:
        c.close()
    assert week == "WC", "once the real regular season concludes, the real live Wild Card week must resolve automatically"


def test_scenario_e_cfb_rolls_into_cfp_automatically(frozen_clock, cfb_games):
    now = datetime(2100, 1, 5, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    cfb_games("5099020", week=15, game_date=(now - timedelta(days=30)).isoformat(), home_score=21, away_score=10)
    cfb_games("5099021", week=1, season_type="postseason", is_playoff=1, playoff_round="semifinal",
              game_date=(now + timedelta(days=3)).isoformat())

    c = engine_bootstrap.connect()
    try:
        week = nl_schedule_bridge.resolve_current_week(c, "CFB", _TEST_SEASON)
    finally:
        c.close()
    assert week == "CFP_SEMIFINAL"


# --- Scenario F: a successful refresh reaches the player with NO manual publish step --

def test_scenario_f_a_refreshed_score_appears_with_no_manual_publish_step(frozen_clock, nfl_games):
    """The single most important regression this closeout produces: proves,
    end to end, that there is no separate publish/rebuild/cache step
    between a game row being updated (exactly what a real refresh does)
    and a real player-facing call (get_pickem_view's own underlying
    function) reflecting it."""
    now = datetime(2099, 9, 14, 22, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    nfl_games("2099_01_TEST_F", week=1, game_date=_iso(now - timedelta(hours=8)), game_time="13:00")

    before = public_pickem.get_pickem_view(league="NFL", season=_TEST_SEASON, week="1", client_id=None)
    before_game = next(g for g in before["view"]["games"] if g["game_id"] == "2099_01_TEST_F")
    assert before_game["status"] != "FINAL"

    # Simulate exactly what a real refresh's UPSERT does: write the real
    # final score. No other action taken -- no rebuild call, no cache
    # clear, nothing Pick'em-specific.
    nfl_games("2099_01_TEST_F", week=1, game_date=_iso(now - timedelta(hours=8)), game_time="13:00",
              home_score=31, away_score=24)

    after = public_pickem.get_pickem_view(league="NFL", season=_TEST_SEASON, week="1", client_id=None)
    after_game = next(g for g in after["view"]["games"] if g["game_id"] == "2099_01_TEST_F")
    assert after_game["status"] == "FINAL", (
        "a real refreshed score must reach the real public Pick'em view with no manual publish/rebuild step"
    )


# --- Scenario G: a failed refresh never corrupts the last valid slate -------

def test_scenario_g_failed_refresh_never_empties_or_corrupts_the_existing_slate(frozen_clock, nfl_games, monkeypatch):
    """A refresh FAILING (recorded in refresh_runs) must never itself delete
    or blank out real game rows already on file -- build_package() reads
    the games table directly and has no dependency on refresh_runs at all,
    so a failed run's own game data is untouched, still fully playable."""
    now = datetime(2099, 9, 4, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    nfl_games("2099_01_TEST_G", week=1, game_date=_iso(now + timedelta(days=3)))

    from gateway.services import admin_refresh
    monkeypatch.setattr(admin_refresh, "refresh_status", lambda: {
        "nfl": {"games": {"status": "FAILED_RESTORED", "finished_at": None}},
        "cfb": {"games": {"status": "FAILED_RESTORED", "finished_at": None}},
    })

    pkg = weekly_pickem.build_package("test-g", "NFL_WEEKLY_PICKEM", _TEST_SEASON, "1")
    assert pkg["qa_status"] == "PASSED"
    assert any(g["game_id"] == "2099_01_TEST_G" for g in pkg["games"]), (
        "a failed refresh_runs record must never corrupt or empty an already-valid slate"
    )

    health = admin_pickem._league_pickem_health("NFL")
    assert health["status"] == "REFRESH_FAILED", "health must surface the real failure, not hide it"
    assert health["slate_game_count"] >= 1, "health's own failure detection must not itself blank the slate"


# --- Health endpoint: real stale-game detection -----------------------------

def test_health_detects_a_stale_locked_game_directly(frozen_clock, cfb_games, monkeypatch):
    """The exact real production symptom found this pass: a game well past
    its own kickoff (plus the disclosed grace window) with no real score
    yet must be surfaced as STALE, directly, from the per-game data --
    not inferred only from refresh age."""
    now = datetime(2099, 9, 7, 12, 0, tzinfo=timezone.utc)
    frozen_clock(now)
    cfb_games("5099030", week=1, game_date=(now - timedelta(hours=20)).isoformat())  # long past kickoff, no score

    from gateway.services import admin_refresh
    monkeypatch.setattr(admin_refresh, "refresh_status", lambda: {
        "nfl": {"games": {"status": "SUCCESS", "finished_at": now.isoformat()}},
        "cfb": {"games": {"status": "SUCCESS", "finished_at": now.isoformat()}},
    })

    health = admin_pickem._league_pickem_health("CFB")
    assert health["stale_locked_count"] >= 1
    assert health["status"] == "STALE"


def test_slate_out_of_sync_is_structurally_unreachable_in_this_architecture():
    """Permanent regression guard for the exact scenario Part P0.6 asks
    for: 'games successfully refreshes but Pick'em indefinitely continues
    serving the old slate.' Proven here by source inspection -- both real
    callers (the public route and the health check) call
    weekly_pickem.build_package()/live_game_statuses() directly, with no
    cache layer or separate publish artifact in between, so this failure
    mode cannot occur without a future architecture change reintroducing
    caching (at which point this test should start failing, on purpose)."""
    import inspect

    public_src = inspect.getsource(public_pickem.get_pickem_view)
    assert "build_package" in public_src or "_build_package" in public_src
    health_src = inspect.getsource(admin_pickem._league_pickem_health)
    assert "build_package" in health_src
    # Both real callers must derive the slate live -- neither may read from
    # a stored/cached package object instead of calling the builder.
    for src in (public_src, health_src):
        assert "packages.get_package" not in src
        assert "cached_package" not in src
