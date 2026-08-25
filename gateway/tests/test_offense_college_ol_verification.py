"""P1 Release Readiness pass: the 3 offensive-line cells the P0 pass
flagged as unverifiable in-repo were re-checked against live web sources
(team depth-chart releases, player bios) -- see
tools/quiz_export/adapters/nfl_offense_college_curated.py's own
UNRESOLVED_CURRENT_TEAM_BOARD_IDS comment for the full citation trail.
2 confirmed correct (Pittsburgh Steelers LG/South Dakota State, Cleveland
Browns RT/Alabama State); 1 remains genuinely unresolved (Arizona
Cardinals RT/Elon -- real sources disagree on who the actual starter even
is) and is quarantined -- the whole board, not a blanked cell, since this
capability shows all 11 positions as one unit and there's no schema-safe
way to omit just one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters import nfl_offense_college_curated  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_arizona_cardinals_board_is_quarantined():
    assert "GOLD_CUR_ARI_2026" in nfl_offense_college_curated.UNRESOLVED_CURRENT_TEAM_BOARD_IDS


def test_only_the_one_unresolved_board_is_quarantined():
    """Explicit requirement: do not invalidate unrelated boards unless
    necessary. Pittsburgh (LG confirmed) and Cleveland (RT confirmed) --
    the other two P0-flagged cells -- must NOT be quarantined."""
    assert "GOLD_CUR_PIT_2026" not in nfl_offense_college_curated.UNRESOLVED_CURRENT_TEAM_BOARD_IDS
    assert "GOLD_CUR_CLE_2026" not in nfl_offense_college_curated.UNRESOLVED_CURRENT_TEAM_BOARD_IDS


def test_quarantined_board_never_appears_in_real_candidates():
    c = engine_bootstrap.connect()
    try:
        candidates = nfl_offense_college_curated.fetch_ordered_candidates(c, seed="ol-quarantine-check")
    finally:
        c.close()
    board_ids = {b["board_id"] for b in candidates}
    assert "GOLD_CUR_ARI_2026" not in board_ids


def test_31_of_32_current_team_boards_remain_playable():
    c = engine_bootstrap.connect()
    try:
        candidates = nfl_offense_college_curated.fetch_ordered_candidates(c, seed="ol-quarantine-count")
    finally:
        c.close()
    assert len(candidates) == 31


def test_pittsburgh_and_cleveland_boards_still_generate_real_questions():
    from tools.director_v02 import registry
    from tools import game_director_v01 as gd

    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_OFFENSE_COLLEGE_CURATED", "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE")]
    spec = {
        "mechanic": "guess", "domain": "NFL_OFFENSE_COLLEGE_CURATED",
        "relationship_predicate": "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE",
        "question_count": 50, "filters": {}, "exclusions": [],
    }
    pkg = gd.generate_package_from_spec(
        spec, cap["adapter"], request_text="ol verification regression", director_request_id="ol-verify-regression",
        seed="ol-verify-regression-seed", target_count=50,
    )
    answers = {q["answer"] for q in pkg["questions"]}
    assert "Pittsburgh Steelers" in answers
    assert "Cleveland Browns" in answers
    assert "Arizona Cardinals" not in answers


def test_pittsburgh_lg_college_matches_verified_real_source():
    c = engine_bootstrap.connect()
    try:
        row = c.execute(
            "SELECT p.college FROM curated_nfl_offense_college_board b "
            "JOIN curated_nfl_offense_college_position p ON p.board_id = b.board_id "
            "WHERE b.board_id = 'GOLD_CUR_PIT_2026' AND p.position = 'LG'"
        ).fetchone()
    finally:
        c.close()
    # Confirmed via steelers.com's own released 2026 depth chart: Mason
    # McCormick, starting LG, South Dakota State.
    assert row["college"] == "South Dakota State"


def test_cleveland_rt_college_matches_verified_real_source():
    c = engine_bootstrap.connect()
    try:
        row = c.execute(
            "SELECT p.college FROM curated_nfl_offense_college_board b "
            "JOIN curated_nfl_offense_college_position p ON p.board_id = b.board_id "
            "WHERE b.board_id = 'GOLD_CUR_CLE_2026' AND p.position = 'RT'"
        ).fetchone()
    finally:
        c.close()
    # Confirmed via multiple 2026 depth-chart sources: Tytus Howard,
    # starting RT, Alabama State.
    assert row["college"] == "Alabama State"
