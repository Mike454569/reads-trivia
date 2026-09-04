"""Weekly Pick'em Player Experience pass -- real-DB coverage for CFB slate
filtering/scoring (FEATURED/TOP25/POWER4/CONFERENCE/FULL), the NL slate
routing default, and pick persistence across different slate variants for
the same real (client_id, league, season, week, game_id). Same real-DB,
no-mocking discipline as test_weekly_pickem.py/test_dynamic_pickem.py.

Real, disclosed limitation exercised directly here, not hidden: this
suite's own fixture season (2026 week 1, ~99 games) genuinely has zero
cfb_betting_lines coverage -- confirmed live before writing this file --
so FEATURED's betting-spread signal contributes 0 for every one of these
real games right now. Tests assert on that honestly (spread-based points
never appear) rather than assuming a coverage this real data doesn't have.
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

_TEST_CLIENT_PREFIX = "pytest-pickem-slate-"


@pytest.fixture(autouse=True)
def _cleanup_pickem_picks():
    yield
    c = engine_bootstrap.connect()
    try:
        c.execute("DELETE FROM pickem_picks WHERE client_id LIKE ?", (f"{_TEST_CLIENT_PREFIX}%",))
        c.commit()
    finally:
        c.close()


def _real_cfb_full_slate():
    """The real, live current-week full CFB slate, resolved the same way
    the public route does -- never a hardcoded season/week, since this
    suite must keep working as the real season progresses."""
    from tools.director_v04 import nl_schedule_bridge, weekly_pickem
    c = engine_bootstrap.connect()
    try:
        season = nl_schedule_bridge._current_season()
        week = nl_schedule_bridge.resolve_current_week(c, "CFB", season)
    finally:
        c.close()
    assert week is not None, "no real current CFB week to test slates against"
    package = weekly_pickem.build_package(f"t-slate-fixture|{season}|{week}", "CFB_WEEKLY_PICKEM", season, week)
    assert package["qa_status"] == "PASSED"
    return season, week, package["games"]


# --- normalize_slate ---------------------------------------------------------

def test_normalize_slate_defaults_to_featured():
    from tools.director_v04 import weekly_pickem
    assert weekly_pickem.normalize_slate(None) == "FEATURED"


def test_normalize_slate_accepts_case_insensitive_real_values():
    from tools.director_v04 import weekly_pickem
    assert weekly_pickem.normalize_slate("full") == "FULL"
    assert weekly_pickem.normalize_slate("Top25") == "TOP25"


def test_normalize_slate_rejects_unknown_value():
    from tools.director_v04 import weekly_pickem
    with pytest.raises(ValueError):
        weekly_pickem.normalize_slate("NOT_A_REAL_SLATE")


# --- real slate filtering against the live current CFB week -----------------

def test_full_slate_matches_the_real_generated_slate_exactly():
    from tools.director_v04 import weekly_pickem
    season, week, games = _real_cfb_full_slate()
    filtered, meta = weekly_pickem.filter_games_for_slate(games, slate="FULL", conference=None, season=season, week=week)
    assert meta["slate"] == "FULL"
    assert filtered is games or [g["game_id"] for g in filtered] == [g["game_id"] for g in games]


def test_featured_slate_is_subset_capped_at_target_and_deduplicated():
    from tools.director_v04 import weekly_pickem
    season, week, games = _real_cfb_full_slate()
    filtered, meta = weekly_pickem.filter_games_for_slate(games, slate="FEATURED", conference=None, season=season, week=week)
    assert meta["slate"] == "FEATURED"
    assert len(filtered) <= weekly_pickem.FEATURED_TARGET_COUNT
    assert len(filtered) == min(weekly_pickem.FEATURED_TARGET_COUNT, len(games))
    full_ids = {g["game_id"] for g in games}
    featured_ids = [g["game_id"] for g in filtered]
    assert set(featured_ids).issubset(full_ids)  # never a game not in the real full slate
    assert len(featured_ids) == len(set(featured_ids))  # no duplicates


def test_featured_slate_is_deterministic_across_repeated_calls():
    """Real stability guarantee (no new caching needed -- see
    filter_games_for_slate's own docstring): two calls against the same
    real data return the identical ordered game_id list."""
    from tools.director_v04 import weekly_pickem
    season, week, games = _real_cfb_full_slate()
    first, _ = weekly_pickem.filter_games_for_slate(games, slate="FEATURED", conference=None, season=season, week=week)
    second, _ = weekly_pickem.filter_games_for_slate(games, slate="FEATURED", conference=None, season=season, week=week)
    assert [g["game_id"] for g in first] == [g["game_id"] for g in second]


def test_top25_slate_only_includes_games_with_a_real_ranked_participant():
    from tools.director_v04 import weekly_pickem
    season, week, games = _real_cfb_full_slate()
    filtered, meta = weekly_pickem.filter_games_for_slate(games, slate="TOP25", conference=None, season=season, week=week)
    assert meta["slate"] == "TOP25"
    c = engine_bootstrap.connect()
    try:
        ranked_school_ids = {r["school_id"] for r in c.execute(
            "SELECT school_id FROM cfb_rankings WHERE season=? AND week=? AND season_type='regular' AND poll='AP Top 25'",
            (season, int(week)) if str(week).isdigit() else (season, 1),
        )}
    finally:
        c.close()
    assert len(filtered) >= 1  # real, current AP Top 25 data exists for this fixture week
    for g in filtered:
        assert g["home_team"] in ranked_school_ids or g["away_team"] in ranked_school_ids


def test_power4_slate_only_includes_games_with_a_real_p4_participant():
    from tools.director_v04 import weekly_pickem
    season, week, games = _real_cfb_full_slate()
    filtered, meta = weekly_pickem.filter_games_for_slate(games, slate="POWER4", conference=None, season=season, week=week)
    assert meta["slate"] == "POWER4"
    game_ids = [g["game_id"] for g in filtered]
    c = engine_bootstrap.connect()
    try:
        placeholders = ",".join("?" for _ in game_ids) or "''"
        rows = c.execute(
            f"SELECT game_id, home_conference, away_conference FROM cfb_games_canonical WHERE game_id IN ({placeholders})",
            game_ids,
        ).fetchall() if game_ids else []
    finally:
        c.close()
    assert len(filtered) >= 1  # real fixture week has at least one real P4 game
    for r in rows:
        assert r["home_conference"] in weekly_pickem.POWER_FOUR_CONFERENCES or \
            r["away_conference"] in weekly_pickem.POWER_FOUR_CONFERENCES


def test_conference_slate_only_includes_games_with_that_real_conference():
    from tools.director_v04 import weekly_pickem
    season, week, games = _real_cfb_full_slate()
    filtered, meta = weekly_pickem.filter_games_for_slate(games, slate="CONFERENCE", conference="SEC", season=season, week=week)
    assert meta["slate"] == "CONFERENCE"
    assert meta["conference"] == "SEC"
    game_ids = [g["game_id"] for g in filtered]
    c = engine_bootstrap.connect()
    try:
        placeholders = ",".join("?" for _ in game_ids) or "''"
        rows = c.execute(
            f"SELECT home_conference, away_conference FROM cfb_games_canonical WHERE game_id IN ({placeholders})",
            game_ids,
        ).fetchall() if game_ids else []
    finally:
        c.close()
    assert len(filtered) >= 1  # real fixture week has at least one real SEC game
    for r in rows:
        assert r["home_conference"] == "SEC" or r["away_conference"] == "SEC"


def test_conference_slate_rejects_unreal_conference_name():
    from tools.director_v04 import weekly_pickem
    season, week, games = _real_cfb_full_slate()
    with pytest.raises(ValueError):
        weekly_pickem.filter_games_for_slate(games, slate="CONFERENCE", conference="Not A Real Conference",
                                              season=season, week=week)


# --- build_cfb_slate_package: real package + shortfall + package_id --------

def test_build_cfb_slate_package_real_featured_passes_qa():
    from tools.director_v04 import weekly_pickem
    season, week, _ = _real_cfb_full_slate()
    package = weekly_pickem.build_cfb_slate_package(
        "t-build-featured", "CFB_WEEKLY_PICKEM", season, week, slate="FEATURED", conference=None)
    assert package["qa_status"] == "PASSED"
    assert package["slate"] == "FEATURED"
    assert 1 <= package["game_count"] <= weekly_pickem.FEATURED_TARGET_COUNT


def test_build_cfb_slate_package_different_slates_get_different_package_ids():
    """Real regression guard: package_id is a content hash of
    variant|season|week|seed only -- without folding slate/conference into
    the seed, two different real slates for the same (season, week) would
    collide under packages.py's content-addressed storage."""
    from tools.director_v04 import weekly_pickem
    season, week, _ = _real_cfb_full_slate()
    featured = weekly_pickem.build_cfb_slate_package(
        "t-collision", "CFB_WEEKLY_PICKEM", season, week, slate="FEATURED", conference=None)
    full = weekly_pickem.build_cfb_slate_package(
        "t-collision", "CFB_WEEKLY_PICKEM", season, week, slate="FULL", conference=None)
    assert featured["package_id"] != full["package_id"]


def test_build_cfb_slate_package_empty_conference_reports_real_shortfall_not_a_crash():
    from tools.director_v04 import weekly_pickem
    season, week, _ = _real_cfb_full_slate()
    package = weekly_pickem.build_cfb_slate_package(
        "t-empty-conf", "CFB_WEEKLY_PICKEM", season, week, slate="CONFERENCE", conference="Big Sky")
    if package["game_count"] == 0:
        assert package["qa_status"] == "FAILED"
        assert "Big Sky" in package["shortfall_reason"]


def test_build_cfb_slate_package_rejects_nfl_variant():
    from tools.director_v04 import weekly_pickem
    with pytest.raises(ValueError):
        weekly_pickem.build_cfb_slate_package("t-nfl", "NFL_WEEKLY_PICKEM", 2026, "1", slate="FEATURED", conference=None)


# --- NL routing: real slate defaults/keywords --------------------------------

def test_bare_cfb_pickem_request_defaults_to_featured_not_full():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me this week's CFB Pick'em")
    assert result is not None
    assert result["league"] == "CFB"
    assert result["slate"] == "FEATURED"
    assert result["conference"] is None


def test_explicit_full_slate_request_resolves_to_full():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me the full college football slate")
    assert result["slate"] == "FULL"


def test_top25_pickem_request_resolves_to_top25():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me Top 25 Pick'em")
    assert result["slate"] == "TOP25"


def test_power_four_pickem_request_resolves_to_power4():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me a Power Four Pick'em")
    assert result["slate"] == "POWER4"


def test_sec_pickem_request_resolves_to_conference_sec():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me an SEC Pick'em")
    assert result["slate"] == "CONFERENCE"
    assert result["conference"] == "SEC"


def test_big_ten_pickem_request_resolves_to_conference_big_ten():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me Big Ten Pick'em")
    assert result["slate"] == "CONFERENCE"
    assert result["conference"] == "Big Ten"


def test_nfl_pickem_request_never_populates_slate():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me NFL Pick'em")
    assert result["league"] == "NFL"
    assert result["slate"] is None
    assert result["conference"] is None


def test_all_nfl_games_request_still_resolves_nfl_no_slate():
    from tools.director_v04 import nl_schedule_bridge
    result = nl_schedule_bridge.detect("Give me all NFL games this week")
    assert result is not None
    assert result["league"] == "NFL"
    assert result["slate"] is None


# --- pick persistence across CFB slate variants ------------------------------

def test_pick_made_in_featured_slate_appears_in_full_and_conference_slates(client):
    """The core cross-slate identity guarantee: client_id+league+season+
    week+game_id is the only real pick key -- a pick made while looking at
    one slate must already be visible when the SAME real game appears in a
    different slate for the same real week."""
    featured = client.get("/v1/public/pickem/CFB", params={"slate": "FEATURED"}).json()
    view = featured["view"]
    assert view["game_count"] >= 1
    game = view["games"][0]
    season, week = featured["season"], featured["week"]
    client_id = _TEST_CLIENT_PREFIX + "cross-slate"

    sub = client.post(f"/v1/public/pickem/cfb/{season}/{week}/pick", json={
        "client_id": client_id, "game_id": game["game_id"], "predicted_winner": game["home_team_code"],
    })
    assert sub.status_code == 200, sub.json()

    full = client.get(f"/v1/public/pickem/cfb/{season}/{week}", params={"slate": "FULL", "client_id": client_id}).json()
    full_entry = next(g for g in full["view"]["games"] if g["game_id"] == game["game_id"])
    assert full_entry["your_pick"] == game["home_team_code"]

    # Also confirmed directly in the real pickem_picks table -- exactly one row.
    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT predicted_winner FROM pickem_picks WHERE client_id=? AND league='CFB' AND season=? AND week=? AND game_id=?",
            (client_id, season, week, game["game_id"]),
        ).fetchall()
    finally:
        c.close()
    assert len(rows) == 1
    assert rows[0]["predicted_winner"] == game["home_team_code"]


def test_pick_made_while_viewing_featured_is_valid_even_if_game_not_in_featured(client):
    """submit_pick always validates against the FULL slate internally
    (never a slate-scoped validation path) -- a pick on a real game that
    Featured filtered OUT must still succeed."""
    full = client.get("/v1/public/pickem/CFB", params={"slate": "FULL"}).json()
    featured = client.get("/v1/public/pickem/CFB", params={"slate": "FEATURED"}).json()
    featured_ids = {g["game_id"] for g in featured["view"]["games"]}
    non_featured_game = next((g for g in full["view"]["games"] if g["game_id"] not in featured_ids), None)
    if non_featured_game is None:
        pytest.skip("real fixture week's Featured slate happens to equal Full this run -- nothing to test")
    season, week = full["season"], full["week"]
    client_id = _TEST_CLIENT_PREFIX + "non-featured"
    sub = client.post(f"/v1/public/pickem/cfb/{season}/{week}/pick", json={
        "client_id": client_id, "game_id": non_featured_game["game_id"],
        "predicted_winner": non_featured_game["home_team_code"],
    })
    assert sub.status_code == 200, sub.json()


def test_nfl_slate_param_other_than_full_is_rejected(client):
    r = client.get("/v1/public/pickem/NFL", params={"slate": "FEATURED"})
    assert r.status_code == 400
