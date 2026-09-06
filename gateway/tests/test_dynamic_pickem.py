"""Dynamic Weekly Pick'em pass -- real-DB coverage for the new persistent
per-user picks store, the public Gateway routes, the admin POSTPONED/
CANCELED override, and the kickoff-based lock that replaces the old
FINAL-only check. Same real-DB, no-mocking discipline as
test_weekly_pickem.py.

Two kinds of real writes happen in this file, both cleaned up
deterministically:
  1. `pickem_picks` rows -- always written under a `pytest-` prefixed
     client_id, deleted in an autouse fixture after every test.
  2. A handful of synthetic, clearly-fake `games` rows (season=2099, a
     season no real schedule will ever use) -- needed because the
     kickoff-lock/POSTPONED/CANCELED behaviors require a REAL row in an
     exact, otherwise-transient state (kickoff already passed with no
     score; or a status this pass's admin override can set) that no real
     historical/current row can be relied on to stably sit in as a test
     fixture. Inserted and deleted within each test that needs one --
     never left behind, never touching any real team's real schedule.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

_EASTERN = ZoneInfo("America/New_York")

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

_SYNTHETIC_SEASON = 2099  # real, but a season no real schedule/refresh will ever populate
_TEST_CLIENT_PREFIX = "pytest-pickem-"


@pytest.fixture(autouse=True)
def _cleanup_pickem_picks():
    yield
    c = engine_bootstrap.connect()
    try:
        c.execute("DELETE FROM pickem_picks WHERE client_id LIKE ?", (f"{_TEST_CLIENT_PREFIX}%",))
        c.commit()
    finally:
        c.close()


@pytest.fixture
def synthetic_nfl_game():
    """Inserts one throwaway `games` row, deletes it (and any status the
    test may have set) on teardown -- never a real team's real schedule."""
    from tools.data_refresh.pickem_schema_migration import ensure_pickem_schema

    game_id = "TEST_PICKEM_SYNTH_GAME"
    c = engine_bootstrap.connect()
    try:
        ensure_pickem_schema(c)
        c.execute("DELETE FROM games WHERE game_id=?", (game_id,))
        c.commit()
    finally:
        c.close()

    def _insert(*, kickoff_offset: timedelta, home_score=None, away_score=None, status=None):
        # games.game_date/game_time are stored as real, plain calendar
        # date + Eastern-local clock time (nflverse's own convention,
        # confirmed directly -- see _pickem_status.nfl_kickoff_utc's own
        # docstring), NOT UTC -- must convert the intended UTC kickoff
        # instant to Eastern before formatting, or nfl_kickoff_utc() will
        # reconvert Eastern->UTC a second time and land on the wrong
        # instant entirely (a real bug this exact mistake would hide).
        kickoff_utc = datetime.now(timezone.utc) + kickoff_offset
        kickoff_eastern = kickoff_utc.astimezone(_EASTERN)
        c = engine_bootstrap.connect()
        try:
            c.execute(
                "INSERT INTO games(game_id, season, game_type, week, game_date, game_time, "
                "away_team, home_team, home_score, away_score, status, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (game_id, _SYNTHETIC_SEASON, "REG", "1", kickoff_eastern.strftime("%Y-%m-%d"),
                 kickoff_eastern.strftime("%H:%M"),
                 "AWY", "HME", home_score, away_score, status, datetime.now(timezone.utc).isoformat()),
            )
            c.commit()
        finally:
            c.close()
        return game_id

    yield _insert

    c = engine_bootstrap.connect()
    try:
        c.execute("DELETE FROM games WHERE game_id=?", (game_id,))
        c.commit()
    finally:
        c.close()


# --- pickem_store.py: real persistence / duplicate prevention / isolation --

def test_pickem_store_roundtrip():
    from tools.director_v04 import pickem_store
    client_id = _TEST_CLIENT_PREFIX + "roundtrip"
    pickem_store.upsert_pick(client_id=client_id, league="NFL", season=2025, week="1",
                              game_id="REAL_GAME_A", predicted_winner="KC")
    picks = pickem_store.picks_for(client_id=client_id, league="NFL", season=2025, week="1")
    assert picks["REAL_GAME_A"]["predicted_winner"] == "KC"


def test_pickem_store_duplicate_pick_upserts_never_creates_a_second_row():
    from tools.director_v04 import pickem_store
    client_id = _TEST_CLIENT_PREFIX + "dup"
    pickem_store.upsert_pick(client_id=client_id, league="NFL", season=2025, week="1",
                              game_id="REAL_GAME_B", predicted_winner="KC")
    pickem_store.upsert_pick(client_id=client_id, league="NFL", season=2025, week="1",
                              game_id="REAL_GAME_B", predicted_winner="BUF")  # changed pick, same game

    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT predicted_winner FROM pickem_picks WHERE client_id=? AND league=? AND season=? AND week=? AND game_id=?",
            (client_id, "NFL", 2025, "1", "REAL_GAME_B"),
        ).fetchall()
    finally:
        c.close()
    assert len(rows) == 1  # the real, structural composite-PK guarantee -- never a second row
    assert rows[0]["predicted_winner"] == "BUF"  # the change took effect


def test_pickem_store_isolated_by_week_and_client():
    from tools.director_v04 import pickem_store
    client_a = _TEST_CLIENT_PREFIX + "iso-a"
    client_b = _TEST_CLIENT_PREFIX + "iso-b"
    pickem_store.upsert_pick(client_id=client_a, league="NFL", season=2025, week="1",
                              game_id="REAL_GAME_C", predicted_winner="KC")
    pickem_store.upsert_pick(client_id=client_a, league="NFL", season=2025, week="2",
                              game_id="REAL_GAME_D", predicted_winner="BUF")

    week1 = pickem_store.picks_for(client_id=client_a, league="NFL", season=2025, week="1")
    week2 = pickem_store.picks_for(client_id=client_a, league="NFL", season=2025, week="2")
    other_client = pickem_store.picks_for(client_id=client_b, league="NFL", season=2025, week="1")

    assert "REAL_GAME_C" in week1 and "REAL_GAME_D" not in week1  # no cross-week bleed
    assert "REAL_GAME_D" in week2 and "REAL_GAME_C" not in week2
    assert other_client == {}  # no cross-client bleed


def test_pickem_store_rejects_malformed_client_id():
    from tools.director_v04 import pickem_store
    with pytest.raises(pickem_store.InvalidClientId):
        pickem_store.upsert_pick(client_id="a b!", league="NFL", season=2025, week="1",
                                  game_id="X", predicted_winner="KC")


# --- Public Gateway routes ---------------------------------------------------

def test_public_pickem_current_week_two_choices_only_no_leakage(client):
    r = client.get("/v1/public/pickem/NFL")
    assert r.status_code == 200
    body = r.json()
    assert body["view"]["game_count"] >= 1
    for g in body["view"]["games"]:
        assert g["home_team_code"] and g["away_team_code"]
        if g["status"] != "FINAL":
            assert "winner" not in g and "home_score" not in g


def test_public_pickem_pick_roundtrip_persists_and_returns_on_refetch(client):
    view = client.get("/v1/public/pickem/NFL").json()["view"]
    scheduled_game = next(g for g in view["games"] if g["status"] == "SCHEDULED")
    client_id = _TEST_CLIENT_PREFIX + "route-roundtrip"
    season, week = view["season"], view["week"]

    sub = client.post(
        f"/v1/public/pickem/nfl/{season}/{week}/pick",
        json={"client_id": client_id, "game_id": scheduled_game["game_id"], "predicted_winner": scheduled_game["home_team_code"]},
    )
    assert sub.status_code == 200
    assert sub.json()["status"] == "SAVED"

    refetched = client.get(f"/v1/public/pickem/nfl/{season}/{week}", params={"client_id": client_id}).json()
    entry = next(g for g in refetched["view"]["games"] if g["game_id"] == scheduled_game["game_id"])
    assert entry["your_pick"] == scheduled_game["home_team_code"]
    assert entry["outcome"] == "PENDING"


def test_public_pickem_pick_rejects_invalid_team(client):
    view = client.get("/v1/public/pickem/NFL").json()["view"]
    game = view["games"][0]
    r = client.post(
        f"/v1/public/pickem/nfl/{view['season']}/{view['week']}/pick",
        json={"client_id": _TEST_CLIENT_PREFIX + "invalid", "game_id": game["game_id"], "predicted_winner": "NOT_A_REAL_TEAM"},
    )
    assert r.status_code == 400


def test_public_pickem_unknown_league_is_invalid_mode(client):
    r = client.get("/v1/public/pickem/XFL")
    assert r.status_code == 400


def test_public_pickem_disabled_by_master_switch(client, monkeypatch):
    from gateway.services import public_pickem
    monkeypatch.setattr(public_pickem.config, "PUBLIC_GAME_ENABLED", False)
    r = client.get("/v1/public/pickem/NFL")
    assert r.status_code == 503


# --- Kickoff-based lock (replaces the old FINAL-only check) -----------------

def test_pick_is_rejected_once_kickoff_has_passed_even_with_no_final_score_yet(synthetic_nfl_game):
    from tools.director_v02 import mechanic_engine
    game_id = synthetic_nfl_game(kickoff_offset=timedelta(hours=-3))  # kicked off 3h ago, real data-lag/in-progress shape
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=_SYNTHETIC_SEASON, week="1", seed="t-kickoff-lock")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    with pytest.raises(mechanic_engine.MechanicError, match="kicked off"):
        mechanic_engine.evaluate_submission(
            "WEEKLY_PICKEM", pkg, progress, {"game_id": game_id, "predicted_winner": "HME"})


def test_pick_is_accepted_before_kickoff(synthetic_nfl_game):
    from tools.director_v02 import mechanic_engine
    game_id = synthetic_nfl_game(kickoff_offset=timedelta(hours=3))  # kicks off in 3h
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=_SYNTHETIC_SEASON, week="1", seed="t-kickoff-open")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    result, _ = mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, progress, {"game_id": game_id, "predicted_winner": "HME"})
    assert result["status"] == "PENDING"


# --- Admin POSTPONED/CANCELED override + VOID grading ------------------------

def test_admin_can_mark_a_game_canceled_and_it_is_excluded_from_grading(synthetic_nfl_game):
    from tools.director_v02 import mechanic_engine
    from gateway.services import admin_pickem
    game_id = synthetic_nfl_game(kickoff_offset=timedelta(hours=3))
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=_SYNTHETIC_SEASON, week="1", seed="t-cancel")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    _, progress = mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, progress, {"game_id": game_id, "predicted_winner": "HME"})

    admin_pickem.set_game_status(league="NFL", game_id=game_id, status="CANCELED", reason="pytest coverage")

    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress)
    entry = next(g for g in view["games"] if g["game_id"] == game_id)
    assert entry["status"] == "CANCELED"
    assert entry["outcome"] == "VOID"
    assert view["graded_count"] == 0  # never counted against the player
    assert view["correct_count"] == 0
    assert view["completed"] is True  # the only real game in this slate is voided -- nothing left to grade


def test_canceled_game_never_accepts_a_new_pick(synthetic_nfl_game):
    from tools.director_v02 import mechanic_engine
    from gateway.services import admin_pickem
    game_id = synthetic_nfl_game(kickoff_offset=timedelta(hours=3))
    admin_pickem.set_game_status(league="NFL", game_id=game_id, status="CANCELED", reason="pytest coverage")

    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=_SYNTHETIC_SEASON, week="1", seed="t-cancel-lock")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    with pytest.raises(mechanic_engine.MechanicError, match="canceled"):
        mechanic_engine.evaluate_submission(
            "WEEKLY_PICKEM", pkg, progress, {"game_id": game_id, "predicted_winner": "HME"})


def test_postponed_game_preserves_pick_and_stays_open_until_its_current_kickoff(synthetic_nfl_game):
    """Requirement: a postponed game's pick is preserved, not voided, and
    the pick stays open until whatever the game's CURRENT real kickoff is
    -- never permanently locked just because it was postponed once."""
    from tools.director_v02 import mechanic_engine
    from gateway.services import admin_pickem
    game_id = synthetic_nfl_game(kickoff_offset=timedelta(hours=3))
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=_SYNTHETIC_SEASON, week="1", seed="t-postponed")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    _, progress = mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, progress, {"game_id": game_id, "predicted_winner": "HME"})

    admin_pickem.set_game_status(league="NFL", game_id=game_id, status="POSTPONED", reason="pytest coverage")

    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress)
    entry = next(g for g in view["games"] if g["game_id"] == game_id)
    assert entry["status"] == "POSTPONED"
    assert entry["outcome"] == "PENDING"  # preserved, never voided just for being postponed
    assert entry["your_pick"] == "HME"

    # Still open -- its (unchanged, still-future) kickoff hasn't passed.
    _, progress2 = mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, progress, {"game_id": game_id, "predicted_winner": "AWY"})
    assert progress2["picks"][game_id]["predicted_winner"] == "AWY"


# --- Pick'em Automation pass: /v1/admin/pickem/health -----------------------

def test_pickem_health_requires_admin(client):
    r = client.get("/v1/admin/pickem/health")
    assert r.status_code == 401


def test_pickem_health_reports_both_leagues(client, auth_headers):
    r = client.get("/v1/admin/pickem/health", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    for league_key, league_code in (("nfl", "NFL"), ("cfb", "CFB")):
        entry = body[league_key]
        assert entry["league"] == league_code
        assert isinstance(entry["season"], int)
        # A real schedule exists for both leagues in this real DB -- a real
        # current week and real game counts should resolve, not None.
        assert entry["current_week"] is not None
        assert entry["upcoming_count"] is not None
        assert entry["final_count"] is not None
        assert entry["upcoming_count"] + entry["final_count"] + entry["voided_count"] == entry["total_games_this_week"]
        assert "last_status" in entry["refresh"]


def test_pickem_health_function_direct():
    """Same real function the route above wraps, called directly -- both
    leagues resolve real counts that add up to the real total slate size."""
    from gateway.services import admin_pickem
    result = admin_pickem.pickem_health()
    assert set(result.keys()) == {"nfl", "cfb"}
    for league_entry in result.values():
        if league_entry["current_week"] is None:
            continue
        total = league_entry["upcoming_count"] + league_entry["final_count"] + league_entry["voided_count"]
        assert total == league_entry["total_games_this_week"]
