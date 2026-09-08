"""Pick'em Season Record -- real, verified win/loss tracking across every
concluded real week of a season (user request: "keep a record of your
pick'ems throughout the season so u can compete with other users").

No new grading logic exists anywhere in this feature -- it strictly
aggregates the exact same real, already-established single-week grading
(mechanic_engine.client_safe_view("WEEKLY_PICKEM", ...)) that every
existing Pick'em view already uses, across every real week
nl_schedule_bridge.weeks_concluded_so_far() reports as concluded (itself
built from the same real candidate-list logic resolve_current_week()
already used -- refactored into a shared helper this pass, not a second,
possibly-inconsistent "what counts as a real week" implementation).
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

_TEST_CLIENT_PREFIX = "pytest-season-record-"


@pytest.fixture(autouse=True)
def _cleanup_pickem_picks():
    yield
    c = engine_bootstrap.connect()
    try:
        c.execute("DELETE FROM pickem_picks WHERE client_id LIKE ?", (f"{_TEST_CLIENT_PREFIX}%",))
        c.commit()
    finally:
        c.close()


def _real_final_game(league: str, season: int, week: str):
    """A real, live, already-FINAL game for the given real week -- skips
    the test (never fabricates one) if the real data doesn't have one yet
    for this exact (league, season, week)."""
    from tools.director_v04 import weekly_pickem

    variant = "CFB_WEEKLY_PICKEM" if league == "CFB" else "NFL_WEEKLY_PICKEM"
    seed = f"public-pickem|{variant}|{season}|{week}"
    if variant == "CFB_WEEKLY_PICKEM":
        pkg = weekly_pickem.build_cfb_slate_package(seed, variant, season, week, slate="FULL", conference=None)
    else:
        pkg = weekly_pickem.build_package(seed, variant, season, week)
    games = pkg.get("games", [])
    if not games:
        return None
    statuses = weekly_pickem.live_game_statuses(variant, [g["game_id"] for g in games])
    for g in games:
        s = statuses.get(g["game_id"], {})
        if s.get("status") == "FINAL" and s.get("winner_code"):
            return g, s
    return None


def test_weeks_concluded_so_far_matches_resolve_current_weeks_own_candidate_list():
    """Structural guard: both functions must be built from the SAME real
    candidate data (real_week_candidates()), not two independently-
    maintained queries that could silently drift apart."""
    from tools.director_v04 import nl_schedule_bridge

    c = engine_bootstrap.connect()
    for league in ("NFL", "CFB"):
        candidates = nl_schedule_bridge.real_week_candidates(c, league, 2026)
        concluded = nl_schedule_bridge.weeks_concluded_so_far(c, league, 2026)
        assert set(concluded) <= {cand[0] for cand in candidates}
        # Every concluded week must genuinely be in the past.
        import datetime
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        by_id = {cand[0]: cand for cand in candidates}
        for week in concluded:
            assert by_id[week][2][:10] < today, (league, week)


def test_season_record_with_zero_picks_is_all_zero_but_not_an_error():
    from tools.director_v04 import pickem_season_record

    rec = pickem_season_record.compute_season_record(
        client_id=f"{_TEST_CLIENT_PREFIX}empty", league="CFB", season=2026)
    assert rec["total_picks_made"] == 0
    assert rec["total_graded"] == 0
    assert rec["win_pct"] is None
    assert rec["weeks_concluded"] >= 1


def test_a_real_correct_pick_on_a_real_final_game_is_graded_correctly():
    from tools.director_v04 import pickem_season_record, pickem_store

    found = _real_final_game("CFB", 2026, "1")
    if found is None:
        pytest.skip("no real FINAL CFB week-1 2026 game available yet to test against")
    game, status = found
    client_id = f"{_TEST_CLIENT_PREFIX}correct"
    pickem_store.upsert_pick(client_id=client_id, league="CFB", season=2026, week="1",
                              game_id=game["game_id"], predicted_winner=status["winner_code"])
    rec = pickem_season_record.compute_season_record(client_id=client_id, league="CFB", season=2026)
    assert rec["total_picks_made"] >= 1
    assert rec["total_correct"] >= 1
    assert rec["win_pct"] is not None and rec["win_pct"] > 0


def test_a_real_incorrect_pick_on_a_real_final_game_is_graded_correctly():
    from tools.director_v04 import pickem_season_record, pickem_store

    found = _real_final_game("CFB", 2026, "1")
    if found is None:
        pytest.skip("no real FINAL CFB week-1 2026 game available yet to test against")
    game, status = found
    loser = game["home_team"] if status["winner_code"] != game["home_team"] else game["away_team"]
    client_id = f"{_TEST_CLIENT_PREFIX}incorrect"
    pickem_store.upsert_pick(client_id=client_id, league="CFB", season=2026, week="1",
                              game_id=game["game_id"], predicted_winner=loser)
    rec = pickem_season_record.compute_season_record(client_id=client_id, league="CFB", season=2026)
    assert rec["total_graded"] >= 1
    assert rec["total_correct"] == 0


def test_season_record_never_undercounts_a_pick_made_while_viewing_a_filtered_slate():
    """Real, deliberate design guard: a CFB pick can be made while viewing
    ANY slate (FEATURED/TOP25/.../FULL), but the season record must always
    build the FULL slate internally to grade it -- a filtered slate is not
    a strict superset and could silently omit a real pick from the total."""
    from tools.director_v04 import pickem_season_record, pickem_store, weekly_pickem

    seed = "public-pickem|CFB_WEEKLY_PICKEM|2026|1"
    full_pkg = weekly_pickem.build_cfb_slate_package(seed, "CFB_WEEKLY_PICKEM", 2026, "1", slate="FULL", conference=None)
    featured_pkg = weekly_pickem.build_cfb_slate_package(seed, "CFB_WEEKLY_PICKEM", 2026, "1", slate="FEATURED", conference=None)
    featured_ids = {g["game_id"] for g in featured_pkg["games"]}
    # A real game that exists in FULL but not in FEATURED -- proves the
    # test is meaningful (not vacuously true because every game happens to
    # be featured).
    only_in_full = next((g for g in full_pkg["games"] if g["game_id"] not in featured_ids), None)
    if only_in_full is None:
        pytest.skip("every real game this week is also in FEATURED -- can't test the filtered-slate gap")
    client_id = f"{_TEST_CLIENT_PREFIX}filtered-slate"
    pickem_store.upsert_pick(client_id=client_id, league="CFB", season=2026, week="1",
                              game_id=only_in_full["game_id"], predicted_winner=only_in_full["home_team"])
    rec = pickem_season_record.compute_season_record(client_id=client_id, league="CFB", season=2026)
    assert rec["total_picks_made"] >= 1, "a real pick on a FULL-slate-only game was silently dropped"


def test_gateway_route_returns_the_same_record_the_module_computes(client):
    from tools.director_v04 import pickem_season_record

    client_id = f"{_TEST_CLIENT_PREFIX}route-check"
    expected = pickem_season_record.compute_season_record(client_id=client_id, league="CFB", season=2026)
    r = client.get("/v1/public/pickem/CFB/record", params={"client_id": client_id, "season": 2026})
    assert r.status_code == 200
    body = r.json()
    assert body["total_picks_made"] == expected["total_picks_made"]
    assert body["total_correct"] == expected["total_correct"]
    assert body["win_pct"] == expected["win_pct"]


def test_gateway_route_rejects_an_invalid_league(client):
    r = client.get("/v1/public/pickem/MLB/record", params={"client_id": "pytest-invalid-league-client"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_MODE"


def test_gateway_route_rejects_a_missing_client_id(client):
    r = client.get("/v1/public/pickem/CFB/record")
    # This Gateway's global handler converts FastAPI's own validation
    # errors into its own {error: {code, message}} contract -- same
    # pattern every other required-query-param route in this app already
    # follows, confirmed directly rather than assumed to be a raw 422.
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_gateway_route_defaults_season_to_the_current_real_season(client):
    import datetime
    r = client.get("/v1/public/pickem/CFB/record", params={"client_id": "pytest-default-season-client"})
    assert r.status_code == 200
    assert r.json()["season"] == datetime.datetime.now(datetime.timezone.utc).year
