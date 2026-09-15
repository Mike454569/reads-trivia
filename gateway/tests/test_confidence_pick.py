"""CONFIDENCE_PICK -- 15-Format Expansion Part 2, format #13.

Real NFL confidence-pool pick'em: reuses WEEKLY_PICKEM's own real,
live-graded weekly slate verbatim (tools/director_v04/weekly_pickem.py),
adding only the real confidence-value-uniqueness rule and points-equal-
to-confidence scoring on top. Same real-DB, no-mocking discipline every
other mechanic test in this suite follows -- generator-level correctness
against both a real, fully-SCHEDULED future NFL week and a real, fully-
FINAL already-completed week (for real live-grading/scoring), the
client-safe view / server-authoritative evaluate contract (no leakage of
a game's result before it is genuinely final), confidence-uniqueness
enforcement, invalid-pick rejection, and the Creator NL bridge end to end.
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


def _resolve_real_future_nfl_week() -> tuple[int, str]:
    """Same real, dynamic resolver test_weekly_pickem.py's own
    _resolve_real_future_nfl_week() already established -- see that
    file's own docstring for why a hardcoded week goes stale."""
    from datetime import datetime, timezone
    c = engine_bootstrap.connect()
    try:
        season = c.execute("SELECT MAX(season) FROM games WHERE game_type='REG'").fetchone()[0]
        today = datetime.now(timezone.utc).date().isoformat()
        row = c.execute(
            "SELECT week FROM games WHERE season = ? AND game_type = 'REG' "
            "GROUP BY week HAVING MIN(game_date) > ? ORDER BY CAST(week AS INTEGER) LIMIT 1",
            (season, today),
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"No fully-future NFL week found for season {season} as of {today} -- "
                "the Engine's schedule data likely needs a refresh (or the season is over)."
            )
        return season, row[0]
    finally:
        c.close()


if engine_bootstrap.ENGINE_DIR.is_dir():
    NFL_FUTURE_SEASON, NFL_FUTURE_WEEK = _resolve_real_future_nfl_week()
else:
    NFL_FUTURE_SEASON, NFL_FUTURE_WEEK = 1900, "1"
NFL_PAST_SEASON, NFL_PAST_WEEK = 2025, "1"  # real completed week -- confirmed live, same fixture test_weekly_pickem.py uses


# --- Generator-level correctness --------------------------------------------

def test_confidence_pick_generates_a_real_future_slate_with_unique_confidence_range():
    from tools.director_v04 import confidence_pick

    pkg = confidence_pick.build_package(
        "t-conf-future", "NFL_CONFIDENCE_PICK", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_count"] >= 2
    assert pkg["max_confidence"] == pkg["game_count"]
    game_ids = [g["game_id"] for g in pkg["games"]]
    assert len(set(game_ids)) == len(game_ids), "no duplicate real games in the slate"


def test_confidence_pick_resolves_the_real_current_week_when_none_is_named():
    from tools.director_v04 import confidence_pick

    pkg = confidence_pick.build_package("t-conf-default", "NFL_CONFIDENCE_PICK")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["season"] is not None and pkg["week"] is not None
    assert pkg["game_count"] >= 1


def test_confidence_pick_rejects_an_unknown_variant():
    from tools.director_v04 import confidence_pick

    with pytest.raises(ValueError):
        confidence_pick.build_package("t-conf-bad", "CFB_CONFIDENCE_PICK", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK)


# --- Client-safe view / evaluate contract -----------------------------------

def test_confidence_pick_full_pick_then_view_never_leaks_a_non_final_result():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-conf-view")
    assert pkg["qa_status"] == "PASSED"
    progress = me.initial_progress("CONFIDENCE_PICK")

    view0 = me.client_safe_view("CONFIDENCE_PICK", pkg, progress)
    assert view0["picks_made"] == 0
    assert view0["available_confidences"] == list(range(1, pkg["max_confidence"] + 1))
    for g in view0["games"]:
        assert "home_score" not in g and "away_score" not in g and "winner" not in g

    g0 = pkg["games"][0]
    result, progress = me.evaluate_submission(
        "CONFIDENCE_PICK", pkg, progress,
        {"game_id": g0["game_id"], "predicted_winner": g0["home_team"], "confidence": pkg["max_confidence"]})
    assert result["confidence"] == pkg["max_confidence"]

    view1 = me.client_safe_view("CONFIDENCE_PICK", pkg, progress)
    assert view1["picks_made"] == 1
    assert pkg["max_confidence"] not in view1["available_confidences"]
    picked_game = next(g for g in view1["games"] if g["game_id"] == g0["game_id"])
    assert picked_game["your_pick"] == g0["home_team"]
    assert picked_game["your_confidence"] == pkg["max_confidence"]
    assert picked_game["outcome"] == "PENDING"  # a real future game -- never graded yet


def test_confidence_pick_duplicate_confidence_on_a_different_game_is_rejected():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-conf-dupe")
    progress = me.initial_progress("CONFIDENCE_PICK")
    g0, g1 = pkg["games"][0], pkg["games"][1]
    _, progress = me.evaluate_submission(
        "CONFIDENCE_PICK", pkg, progress,
        {"game_id": g0["game_id"], "predicted_winner": g0["home_team"], "confidence": 5})
    with pytest.raises(Exception):
        me.evaluate_submission(
            "CONFIDENCE_PICK", pkg, progress,
            {"game_id": g1["game_id"], "predicted_winner": g1["home_team"], "confidence": 5})


def test_confidence_pick_repicking_the_same_game_with_its_own_confidence_is_allowed():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-conf-repick")
    progress = me.initial_progress("CONFIDENCE_PICK")
    g0 = pkg["games"][0]
    _, progress = me.evaluate_submission(
        "CONFIDENCE_PICK", pkg, progress,
        {"game_id": g0["game_id"], "predicted_winner": g0["home_team"], "confidence": 3})
    result, progress = me.evaluate_submission(
        "CONFIDENCE_PICK", pkg, progress,
        {"game_id": g0["game_id"], "predicted_winner": g0["away_team"], "confidence": 3})
    assert result["predicted_winner"] == g0["away_team"]
    assert result["confidence"] == 3


@pytest.mark.parametrize("bad_confidence", [0, -1, 100, "abc", 3.5, True])
def test_confidence_pick_rejects_out_of_range_or_non_integer_confidence(bad_confidence):
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-conf-invalid")
    progress = me.initial_progress("CONFIDENCE_PICK")
    g0 = pkg["games"][0]
    with pytest.raises(Exception):
        me.evaluate_submission(
            "CONFIDENCE_PICK", pkg, progress,
            {"game_id": g0["game_id"], "predicted_winner": g0["home_team"], "confidence": bad_confidence})


def test_confidence_pick_rejects_an_invalid_predicted_winner():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_FUTURE_SEASON, week=NFL_FUTURE_WEEK, seed="t-conf-badwinner")
    progress = me.initial_progress("CONFIDENCE_PICK")
    g0 = pkg["games"][0]
    with pytest.raises(Exception):
        me.evaluate_submission(
            "CONFIDENCE_PICK", pkg, progress,
            {"game_id": g0["game_id"], "predicted_winner": "NOT_A_REAL_TEAM", "confidence": 1})


# --- Real live grading against an already-completed real week --------------

def test_confidence_pick_scores_real_points_equal_to_confidence_on_a_correct_past_pick():
    """Grading is tested by directly injecting a progress dict holding a
    pick already made (simulating one placed BEFORE this real game's real
    kickoff, back when it was still open) -- evaluate_submission's own
    real kickoff-lock correctly refuses to accept a brand-new pick on an
    already-played game (see the dedicated lock test below), so this
    exercises _confidence_pick_client_view's real live-grading directly,
    which is the actual thing under test here."""
    from tools.director_v02 import mechanic_engine as me
    from tools.director_v04 import weekly_pickem

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_PAST_SEASON, week=NFL_PAST_WEEK, seed="t-conf-past")
    assert pkg["qa_status"] == "PASSED"
    g0 = pkg["games"][0]
    live = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", [g0["game_id"]])[g0["game_id"]]
    assert live["status"] == "FINAL", "this fixture week must already be fully final"
    real_winner = live["winner_code"]
    if real_winner == "TIE":
        pytest.skip("this particular real game was a tie -- not a useful fixture for a correct-pick assertion")

    progress = {"picks": {g0["game_id"]: {"predicted_winner": real_winner, "confidence": pkg["max_confidence"]}}}
    view = me.client_safe_view("CONFIDENCE_PICK", pkg, progress)
    picked = next(g for g in view["games"] if g["game_id"] == g0["game_id"])
    assert picked["outcome"] == "CORRECT"
    assert picked["points_earned"] == pkg["max_confidence"]
    assert view["total_score"] == pkg["max_confidence"]


def test_confidence_pick_scores_zero_on_an_incorrect_past_pick():
    from tools.director_v02 import mechanic_engine as me
    from tools.director_v04 import weekly_pickem

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_PAST_SEASON, week=NFL_PAST_WEEK, seed="t-conf-past-wrong")
    g0 = pkg["games"][0]
    live = weekly_pickem.live_game_statuses("NFL_WEEKLY_PICKEM", [g0["game_id"]])[g0["game_id"]]
    assert live["status"] == "FINAL"
    real_winner = live["winner_code"]
    if real_winner == "TIE":
        pytest.skip("this particular real game was a tie -- not a useful fixture for an incorrect-pick assertion")
    wrong_pick = g0["away_team"] if real_winner == g0["home_team"] else g0["home_team"]

    progress = {"picks": {g0["game_id"]: {"predicted_winner": wrong_pick, "confidence": pkg["max_confidence"]}}}
    view = me.client_safe_view("CONFIDENCE_PICK", pkg, progress)
    picked = next(g for g in view["games"] if g["game_id"] == g0["game_id"])
    assert picked["outcome"] == "INCORRECT"
    assert picked["points_earned"] == 0
    assert view["total_score"] == 0


def test_confidence_pick_rejects_a_pick_on_a_game_that_has_already_kicked_off():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_confidence_pick_round(
        variant="NFL_CONFIDENCE_PICK", season=NFL_PAST_SEASON, week=NFL_PAST_WEEK, seed="t-conf-locked")
    progress = me.initial_progress("CONFIDENCE_PICK")
    g0 = pkg["games"][0]
    with pytest.raises(Exception):
        me.evaluate_submission(
            "CONFIDENCE_PICK", pkg, progress,
            {"game_id": g0["game_id"], "predicted_winner": g0["home_team"], "confidence": 1})


# --- Creator NL bridge end to end -------------------------------------------

def test_detect_confidence_pick_real_phrasing():
    from tools.director_v04 import nl_schedule_bridge as bridge

    for phrase in ["confidence pick game", "confidence pool for this week", "give me a confidence pickem"]:
        r = bridge.detect(phrase)
        assert r is not None, f"expected a match for {phrase!r}"
        assert r["taxonomy_id"] == "CONFIDENCE_PICK"
        assert r["variant"] == "NFL_CONFIDENCE_PICK"
        assert r["league"] == "NFL"


def test_confidence_pick_never_shadowed_by_or_shadows_plain_weekly_pickem():
    from tools.director_v04 import nl_schedule_bridge as bridge

    r = bridge.detect("make me a weekly nfl pickem")
    assert r["taxonomy_id"] == "WEEKLY_PICKEM"

    r2 = bridge.detect("confidence pick game")
    assert r2["taxonomy_id"] == "CONFIDENCE_PICK"


def test_confidence_pick_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="confidence pick game", puzzle_count=None, difficulty=None, seed="pytest-confidence-pick",
    )
    assert r["taxonomy_id"] == "CONFIDENCE_PICK"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP25:")
    assert r["view"]["game_count"] >= 1
    assert r["view"]["max_confidence"] == r["view"]["game_count"]


def test_confidence_pick_creator_assess_feasibility_reports_supported_with_admin_only_limitation():
    from gateway.services import creator

    r = creator.assess_feasibility("confidence pick game")
    assert r["support_status"] == "SUPPORTED"
    assert r["taxonomy_id"] == "CONFIDENCE_PICK"
    assert any("Admin/Creator-only" in lim for lim in r["known_limitations"])
