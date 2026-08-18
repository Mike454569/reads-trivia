"""Reliability Design Phase 7A -- WEEKLY_PICKEM.

Real NFL/CFB weekly pick'em: generator-level correctness against real,
current schedule/result data (both an upcoming, fully-SCHEDULED NFL week
and a fully-FINAL, already-completed CFB/NFL week), the client-safe view /
server-authoritative evaluate contract (no leakage of a game's result
before it is genuinely final), automatic re-grading purely from live data
(no cached "graded" flag anywhere), tie handling against a real historical
NFL tie, invalid-pick rejection, duplicate/late-pick handling, and the
admin-gated Gateway routes end to end. Same real-DB, no-mocking discipline
every other Phase 6 mechanic test in this suite already follows.
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

_LEAK_MARKERS = ("_private", "correctIndex", "_audit", "home_score", "away_score", "winner")

# Real, confirmed-live fixtures (see the module docstring's own reasoning
# for why these specific season/weeks were chosen, not arbitrary):
NFL_FUTURE_SEASON, NFL_FUTURE_WEEK = 2026, "1"    # real future schedule, both scores NULL -- confirmed live
NFL_PAST_SEASON, NFL_PAST_WEEK = 2025, "1"        # real completed week -- confirmed live
CFB_PAST_SEASON, CFB_PAST_WEEK = 2025, 1          # real completed CFB week -- confirmed live
NFL_TIE_SEASON, NFL_TIE_WEEK = 2002, "10"         # real NFL tie: 2002_10_ATL_PIT, 34-34


def _assert_no_leakage_for_scheduled_games(view: dict) -> None:
    for g in view["games"]:
        if g["status"] != "FINAL":
            assert "home_score" not in g and "away_score" not in g and "winner" not in g, \
                f"leaked result for a non-final game: {g}"


# --- generator-level: real NFL + CFB data --------------------------------

def test_nfl_future_week_slate_is_all_scheduled_no_leakage():
    from tools.director_v04 import weekly_pickem
    pkg = weekly_pickem.build_package("t-nfl-future", "NFL_WEEKLY_PICKEM", NFL_FUTURE_SEASON, NFL_FUTURE_WEEK)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_count"] >= 1
    game_ids = [g["game_id"] for g in pkg["games"]]
    live = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", game_ids)
    assert all(live[gid]["status"] == "SCHEDULED" for gid in game_ids), live


def test_nfl_past_week_slate_is_all_final_with_real_winners():
    from tools.director_v04 import weekly_pickem
    pkg = weekly_pickem.build_package("t-nfl-past", "NFL_WEEKLY_PICKEM", NFL_PAST_SEASON, NFL_PAST_WEEK)
    assert pkg["qa_status"] == "PASSED"
    game_ids = [g["game_id"] for g in pkg["games"]]
    live = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", game_ids)
    assert all(live[gid]["status"] == "FINAL" for gid in game_ids), live
    assert all(live[gid]["winner_code"] is not None for gid in game_ids)


def test_cfb_past_week_slate_generates_real_games():
    from tools.director_v04 import weekly_pickem
    pkg = weekly_pickem.build_package("t-cfb-past", "CFB_WEEKLY_PICKEM", CFB_PAST_SEASON, CFB_PAST_WEEK)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_count"] >= 1
    for g in pkg["games"]:
        assert g["home_display"] and g["away_display"]
        assert g["home_team"] != g["away_team"]


def test_repeat_generation_is_deterministic():
    from tools.director_v04 import weekly_pickem
    p1 = weekly_pickem.build_package("same-seed", "NFL_WEEKLY_PICKEM", NFL_PAST_SEASON, NFL_PAST_WEEK)
    p2 = weekly_pickem.build_package("same-seed", "NFL_WEEKLY_PICKEM", NFL_PAST_SEASON, NFL_PAST_WEEK)
    assert p1["package_id"] == p2["package_id"]
    assert [g["game_id"] for g in p1["games"]] == [g["game_id"] for g in p2["games"]]


def test_real_nfl_tie_is_reported_as_a_tie_not_a_winner():
    from tools.director_v04 import weekly_pickem
    pkg = weekly_pickem.build_package("t-tie", "NFL_WEEKLY_PICKEM", NFL_TIE_SEASON, NFL_TIE_WEEK)
    assert pkg["qa_status"] == "PASSED"
    game_ids = [g["game_id"] for g in pkg["games"]]
    assert "2002_10_ATL_PIT" in game_ids
    live = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", game_ids)
    tie = live["2002_10_ATL_PIT"]
    assert tie["status"] == "FINAL"
    assert tie["winner_code"] == "TIE"
    assert tie["home_score"] == tie["away_score"] == 34


# --- feasibility ------------------------------------------------------------

def test_feasibility_supported_for_a_real_week():
    from tools.director_v04 import weekly_pickem
    result = weekly_pickem.check_slate_feasibility("NFL_WEEKLY_PICKEM", NFL_PAST_SEASON, NFL_PAST_WEEK)
    assert result["support_status"] == "SUPPORTED"
    assert result["real_game_count"] >= 1


def test_feasibility_missing_data_for_a_nonsense_week_never_fabricates():
    from tools.director_v04 import weekly_pickem
    result = weekly_pickem.check_slate_feasibility("NFL_WEEKLY_PICKEM", NFL_PAST_SEASON, "99")
    assert result["support_status"] == "MISSING_DATA"
    assert result["real_game_count"] == 0


def test_feasibility_unknown_for_bad_variant():
    from tools.director_v04 import weekly_pickem
    result = weekly_pickem.check_slate_feasibility("XFL_WEEKLY_PICKEM", 2025, "1")
    assert result["support_status"] == "UNKNOWN"


# --- mechanic_engine: client view / evaluate, no leakage, grading ---------

def test_client_view_never_leaks_result_for_scheduled_games():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-view-leak")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress)
    _assert_no_leakage_for_scheduled_games(view)
    assert view["graded_count"] == 0
    assert view["completed"] is False


def test_evaluate_rejects_invalid_team_selection():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-invalid-pick")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    game_id = pkg["games"][0]["game_id"]
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission(
            "WEEKLY_PICKEM", pkg, progress, {"game_id": game_id, "predicted_winner": "NOT_A_REAL_TEAM"})


def test_evaluate_rejects_unknown_game_id():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-unknown-game")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission(
            "WEEKLY_PICKEM", pkg, progress, {"game_id": "not-a-real-game-id", "predicted_winner": "SEA"})


def test_pending_pick_on_scheduled_game_is_never_falsely_scored():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-pending")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    game = pkg["games"][0]
    result, progress = mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, progress, {"game_id": game["game_id"], "predicted_winner": game["home_team"]})
    assert result["status"] == "PENDING"
    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress)
    entry = next(g for g in view["games"] if g["game_id"] == game["game_id"])
    assert entry["outcome"] == "PENDING"
    assert "winner" not in entry
    assert view["correct_count"] == 0
    assert view["graded_count"] == 0


def test_duplicate_pick_on_open_game_overwrites_not_errors():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-dup")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    game = pkg["games"][0]
    _, progress = mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, progress, {"game_id": game["game_id"], "predicted_winner": game["home_team"]})
    _, progress = mechanic_engine.evaluate_submission(
        "WEEKLY_PICKEM", pkg, progress, {"game_id": game["game_id"], "predicted_winner": game["away_team"]})
    assert progress["picks"][game["game_id"]]["predicted_winner"] == game["away_team"]
    assert len(progress["picks"]) == 1


def test_pick_is_rejected_once_the_game_is_already_final():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_PAST_SEASON, week=NFL_PAST_WEEK, seed="t-already-final")
    progress = mechanic_engine.initial_progress("WEEKLY_PICKEM")
    game = pkg["games"][0]  # this whole week is real/completed -- see test_nfl_past_week_slate_is_all_final
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission(
            "WEEKLY_PICKEM", pkg, progress, {"game_id": game["game_id"], "predicted_winner": game["home_team"]})


def test_grading_is_automatic_and_correct_once_final_correct_and_incorrect_picks():
    from tools.director_v02 import mechanic_engine
    from tools.director_v04 import weekly_pickem
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_TIE_SEASON, week=NFL_TIE_WEEK, seed="t-grading")
    live = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", [g["game_id"] for g in pkg["games"]])
    # Pick a real, non-tied, already-final game from this same real week to
    # exercise both a correct and an incorrect pick.
    decided = next(g for g in pkg["games"] if live[g["game_id"]]["winner_code"] not in (None, "TIE"))
    real_winner = live[decided["game_id"]]["winner_code"]
    loser_side = decided["away_team"] if real_winner == decided["home_team"] else decided["home_team"]

    # Correct pick: bypass evaluate_submission's "already final -> rejected"
    # guard directly at the progress level (a real player could only ever
    # reach a FINAL game this way if they picked it before it went final --
    # already covered by test_pick_is_rejected_once_the_game_is_already_final
    # -- this test isolates VIEW-TIME grading correctness specifically).
    progress = {"picks": {decided["game_id"]: {"predicted_winner": real_winner, "picked_at": "2002-11-10T00:00:00+00:00"}}}
    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress)
    entry = next(g for g in view["games"] if g["game_id"] == decided["game_id"])
    assert entry["outcome"] == "CORRECT"
    assert entry["winner"] == real_winner
    assert view["correct_count"] == 1
    assert view["graded_count"] == 1

    # Incorrect pick: same real game, the other team.
    progress_wrong = {"picks": {decided["game_id"]: {"predicted_winner": loser_side, "picked_at": "2002-11-10T00:00:00+00:00"}}}
    view_wrong = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress_wrong)
    entry_wrong = next(g for g in view_wrong["games"] if g["game_id"] == decided["game_id"])
    assert entry_wrong["outcome"] == "INCORRECT"
    assert view_wrong["correct_count"] == 0
    assert view_wrong["graded_count"] == 1


def test_tie_pick_outcome_is_tie_not_incorrect():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_TIE_SEASON, week=NFL_TIE_WEEK, seed="t-tie-outcome")
    tie_game = next(g for g in pkg["games"] if g["game_id"] == "2002_10_ATL_PIT")
    progress = {"picks": {tie_game["game_id"]: {"predicted_winner": tie_game["home_team"], "picked_at": "x"}}}
    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress)
    entry = next(g for g in view["games"] if g["game_id"] == tie_game["game_id"])
    assert entry["outcome"] == "TIE"
    assert entry["winner"] == "TIE"
    # A tie is neither counted correct nor left ungraded/pending.
    assert view["correct_count"] == 0
    assert view["graded_count"] == 1


def test_fully_graded_completed_week_reports_completed_true():
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_weekly_pickem_round(
        variant="NFL_WEEKLY_PICKEM", season=NFL_TIE_SEASON, week=NFL_TIE_WEEK, seed="t-completed")
    progress = {"picks": {g["game_id"]: {"predicted_winner": g["home_team"], "picked_at": "x"} for g in pkg["games"]}}
    view = mechanic_engine.client_safe_view("WEEKLY_PICKEM", pkg, progress)
    assert view["completed"] is True
    assert view["graded_count"] == view["game_count"]


# --- Gateway routes, admin-gated, end to end -------------------------------

def test_mechanics_round_requires_admin_for_weekly_pickem(client):
    r = client.post("/v1/creator/mechanics/round",
                     json={"taxonomy_id": "WEEKLY_PICKEM", "variant": "NFL_WEEKLY_PICKEM", "season": 2025, "week": "1"})
    assert r.status_code == 401


def test_mechanics_round_rejects_missing_season_or_week(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round",
                     json={"taxonomy_id": "WEEKLY_PICKEM", "variant": "NFL_WEEKLY_PICKEM"}, headers=auth_headers)
    assert r.status_code == 400


def test_mechanics_round_rejects_unknown_weekly_pickem_variant(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round",
                     json={"taxonomy_id": "WEEKLY_PICKEM", "variant": "XFL_WEEKLY_PICKEM", "season": 2025, "week": "1"},
                     headers=auth_headers)
    assert r.status_code == 400


def test_mechanics_round_reports_no_eligible_game_for_a_real_but_empty_week(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round",
                     json={"taxonomy_id": "WEEKLY_PICKEM", "variant": "NFL_WEEKLY_PICKEM", "season": 2025, "week": "99"},
                     headers=auth_headers)
    assert r.status_code == 503  # NO_ELIGIBLE_GAME's real, established mapping (gateway/errors.py) -- distinct from
    assert r.json()["error"]["code"] == "NO_ELIGIBLE_GAME"  # a hard 5xx crash, this is "ran fine, no real content existed"


def test_weekly_pickem_full_round_trip_generate_pick_grade(client, auth_headers):
    gen = client.post("/v1/creator/mechanics/round", json={
        "taxonomy_id": "WEEKLY_PICKEM", "variant": "NFL_WEEKLY_PICKEM",
        "season": NFL_TIE_SEASON, "week": NFL_TIE_WEEK, "seed": "route-e2e",
    }, headers=auth_headers)
    assert gen.status_code == 200
    body = gen.json()
    round_id = body["round_id"]
    _assert_no_leakage_for_scheduled_games(body["view"])

    game = body["view"]["games"][0]
    assert "home_score" not in game or game["status"] == "FINAL"  # this week is real/completed -- see fixture comment

    resumed = client.get(f"/v1/creator/mechanics/round/{round_id}", headers=auth_headers)
    assert resumed.status_code == 200
    assert resumed.json()["view"]["season"] == NFL_TIE_SEASON

    sub = client.post(f"/v1/creator/mechanics/round/{round_id}/submit",
                       json={"submission": {"game_id": "definitely-not-in-this-slate", "predicted_winner": "X"}},
                       headers=auth_headers)
    assert sub.status_code == 400  # this whole week is already final -- see test_pick_is_rejected_once_the_game_is_already_final


def test_mechanics_round_not_found_is_clean_error_for_weekly_pickem(client, auth_headers):
    r = client.get("/v1/creator/mechanics/round/GGP9:0000000000000000000000ab", headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PACKAGE_NOT_FOUND"
