"""Reusable Game Format System pass -- real, verified tests for the new
COMPARISON_BRACKET mechanic (tools/director_v04/comparison.py,
tools/director_v02/mechanic_engine.py's own comparison functions), backing
the new BRACKET_TREE format.
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


def test_build_package_produces_a_real_tie_free_8_entrant_bracket():
    from tools.director_v04 import comparison

    for variant in comparison.VARIANTS:
        pkg = comparison.build_package(f"pytest-bracket-{variant}", variant)
        assert pkg["qa_status"] == "PASSED", pkg.get("shortfall_reason")
        assert len(pkg["_private_rounds"][0]) == 4  # quarterfinals: 8 entrants -> 4 matchups
        assert len(pkg["_private_rounds"][1]) == 2  # semifinals
        assert len(pkg["_private_rounds"][2]) == 1  # final
        assert pkg["rounds"][0]["round_label"] == "Quarterfinals"
        assert pkg["rounds"][2]["round_label"] == "Final"


def test_public_package_never_leaks_the_real_winner_or_values():
    """The public `rounds` field (what a real client actually receives)
    must carry only entrant labels -- real_winner/value_a/value_b live
    exclusively in `_private_rounds`, which mechanic_engine.py's own
    client_safe_view() never returns."""
    from tools.director_v04 import comparison

    pkg = comparison.build_package("pytest-no-leak", "CFB_TEAM_SEASON_WINS_BRACKET")
    for r in pkg["rounds"]:
        for m in r["matchups"]:
            assert set(m.keys()) == {"match_id", "entrant_a", "entrant_b"}


def test_every_real_matchup_winner_is_correctly_the_higher_win_total():
    from tools.director_v04 import comparison

    pkg = comparison.build_package("pytest-real-winner-check", "NFL_TEAM_SEASON_WINS_BRACKET")
    for r in pkg["_private_rounds"]:
        for m in r:
            expected_winner = m["entrant_a"] if m["value_a"] > m["value_b"] else m["entrant_b"]
            assert m["real_winner"] == expected_winner
            assert m["value_a"] != m["value_b"], "tie-exclusion violated -- every matchup must have a real winner"


def test_later_round_matchups_are_built_from_real_previous_round_winners():
    from tools.director_v04 import comparison

    pkg = comparison.build_package("pytest-round-chain", "NFL_TEAM_SEASON_WINS_BRACKET")
    qf, sf, final = pkg["_private_rounds"]
    qf_winners = {m["real_winner"] for m in qf}
    sf_entrants = {m["entrant_a"] for m in sf} | {m["entrant_b"] for m in sf}
    assert sf_entrants <= qf_winners
    sf_winners = {m["real_winner"] for m in sf}
    final_entrants = {final[0]["entrant_a"], final[0]["entrant_b"]}
    assert final_entrants <= sf_winners


def test_mechanic_engine_client_view_and_evaluate_end_to_end():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_comparison_round(variant="CFB_TEAM_SEASON_WINS_BRACKET", seed="pytest-e2e-1")
    assert pkg["qa_status"] == "PASSED"
    progress = me.initial_progress("COMPARISON_BRACKET")
    view = me.client_safe_view("COMPARISON_BRACKET", pkg, progress)
    assert view["picks_made"] == 0
    assert view["total_matchups"] == 7  # 4 + 2 + 1
    assert not view["completed"]

    # Real, correct pick.
    m0 = pkg["rounds"][0]["matchups"][0]
    real_winner = next(m["real_winner"] for m in pkg["_private_rounds"][0] if m["match_id"] == m0["match_id"])
    result, progress = me.evaluate_submission(
        "COMPARISON_BRACKET", pkg, progress, {"match_id": m0["match_id"], "predicted_winner": real_winner})
    assert result["correct"] is True
    assert result["real_winner"] == real_winner

    view2 = me.client_safe_view("COMPARISON_BRACKET", pkg, progress)
    assert view2["picks_made"] == 1
    assert view2["correct_count"] == 1
    revealed = view2["rounds"][0]["matchups"][0]
    assert revealed["your_pick"] == real_winner
    assert revealed["correct"] is True


def test_evaluate_rejects_a_predicted_winner_not_in_the_real_matchup():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_comparison_round(variant="NFL_TEAM_SEASON_WINS_BRACKET", seed="pytest-invalid-pick")
    progress = me.initial_progress("COMPARISON_BRACKET")
    m0 = pkg["rounds"][0]["matchups"][0]
    with pytest.raises(me.MechanicError):
        me.evaluate_submission("COMPARISON_BRACKET", pkg, progress, {
            "match_id": m0["match_id"], "predicted_winner": "Not A Real Entrant (1999)",
        })


def test_evaluate_rejects_an_unknown_match_id():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_comparison_round(variant="NFL_TEAM_SEASON_WINS_BRACKET", seed="pytest-bad-match-id")
    progress = me.initial_progress("COMPARISON_BRACKET")
    with pytest.raises(me.MechanicError):
        me.evaluate_submission("COMPARISON_BRACKET", pkg, progress, {
            "match_id": "NOT_A_REAL_MATCH", "predicted_winner": "anything",
        })


def test_completing_every_real_matchup_marks_the_round_completed():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_comparison_round(variant="CFB_TEAM_SEASON_WINS_BRACKET", seed="pytest-full-bracket")
    progress = me.initial_progress("COMPARISON_BRACKET")
    all_matchups = [m for r in pkg["rounds"] for m in r["matchups"]]
    for m in all_matchups:
        _, progress = me.evaluate_submission(
            "COMPARISON_BRACKET", pkg, progress, {"match_id": m["match_id"], "predicted_winner": m["entrant_a"]})
    assert progress["completed"] is True
    view = me.client_safe_view("COMPARISON_BRACKET", pkg, progress)
    assert view["completed"] is True
    assert view["picks_made"] == view["total_matchups"]
