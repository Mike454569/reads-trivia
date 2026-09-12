"""40-Format Expansion pass -- real tests for the 6 new mechanic_engine.py
taxonomies (GRID_CONSTRAINT_BOARD, DRIVE_PROGRESSION, ROSTER_BUILD,
KNOCKOUT_BRACKET, RELATIONSHIP_CHAIN, BRANCH_STATE) added to back
CONNECTION_GRID, PERFECT_DRIVE/GOAL_LINE_STAND, LINEUP_BUILDER/AUCTION_DRAFT/
CAP_CHALLENGE, KNOCKOUT_TOURNAMENT, SIX_DEGREES/CHAIN_REACTION, and
CHOOSE_YOUR_PATH respectively. Every generator is exercised against the
real, live SQLite Engine (no mocked data) -- these are integration tests,
matching this repo's own established discipline for every other mechanic.

Covers the user's own 10-point format-testing checklist per taxonomy:
1. registry entry (TAXONOMY_IDS/VARIANTS)
2. real generation from real data
3. answer validation (correct + incorrect)
4. malformed/out-of-range submission rejection
5. no-duplicate/invalid items
6. regression safety for the 8 pre-existing formats (see
   test_phase6_mechanics.py / test_comparison_bracket_mechanic.py, run
   alongside this file, not duplicated here).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = __import__("pytest").mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


# --- registry entries ------------------------------------------------------

def test_all_six_new_taxonomies_are_registered():
    from tools.director_v02 import mechanic_engine as me

    for t in ("GRID_CONSTRAINT_BOARD", "DRIVE_PROGRESSION", "ROSTER_BUILD",
              "KNOCKOUT_BRACKET", "RELATIONSHIP_CHAIN", "BRANCH_STATE"):
        assert t in me.TAXONOMY_IDS
        assert me.VARIANTS.get(t), f"{t} has no registered variants"


# --- GRID_CONSTRAINT_BOARD --------------------------------------------------

def test_grid_constraint_board_generates_real_data_no_duplicate_empty_cells():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_grid_constraint_round(variant="NFL_TEAM_DRAFT_ROUND_GRID", seed="test-grid-1")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["row_labels"]) == 3 and len(pkg["col_labels"]) == 3
    assert len(set(pkg["row_labels"])) == 3  # no duplicate row criteria
    assert len(set(pkg["col_labels"])) == 3


def test_grid_constraint_board_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me
    from tools.quiz_export import engine

    pkg = me.generate_grid_constraint_round(variant="NFL_TEAM_DRAFT_ROUND_GRID", seed="test-grid-2")
    progress = me.initial_progress("GRID_CONSTRAINT_BOARD")
    c = engine.connect()
    try:
        real_answer = c.execute(
            "SELECT d.player_name FROM draft_facts d JOIN canonical_roster_seasons r ON r.player_id = d.player_key "
            "WHERE r.team_code = ? AND r.verification_status='SOURCE_BACKED' AND d.verification_status='SOURCE_BACKED' "
            "AND d.draft_round = ? LIMIT 1",
            (pkg["_private_row_criteria"][0]["value"], pkg["_private_col_criteria"][0]["value"]),
        ).fetchone()[0]
    finally:
        c.close()
    result, progress = me.evaluate_submission("GRID_CONSTRAINT_BOARD", pkg, progress,
                                               {"row_index": 0, "col_index": 0, "guess": real_answer})
    assert result["correct"] is True
    result2, progress = me.evaluate_submission("GRID_CONSTRAINT_BOARD", pkg, progress,
                                                {"row_index": 0, "col_index": 1, "guess": "Definitely Not A Real Player"})
    assert result2["correct"] is False


def test_grid_constraint_board_rejects_out_of_range_cell():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_grid_constraint_round(variant="NFL_TEAM_DRAFT_ROUND_GRID", seed="test-grid-3")
    progress = me.initial_progress("GRID_CONSTRAINT_BOARD")
    try:
        me.evaluate_submission("GRID_CONSTRAINT_BOARD", pkg, progress, {"row_index": 99, "col_index": 0, "guess": "x"})
        assert False, "expected MechanicError"
    except me.MechanicError:
        pass


def test_grid_constraint_board_rejects_answering_the_same_cell_twice():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_grid_constraint_round(variant="NFL_TEAM_DRAFT_ROUND_GRID", seed="test-grid-4")
    progress = me.initial_progress("GRID_CONSTRAINT_BOARD")
    _, progress = me.evaluate_submission("GRID_CONSTRAINT_BOARD", pkg, progress, {"row_index": 0, "col_index": 0, "guess": "x"})
    try:
        me.evaluate_submission("GRID_CONSTRAINT_BOARD", pkg, progress, {"row_index": 0, "col_index": 0, "guess": "y"})
        assert False, "expected MechanicError"
    except me.MechanicError:
        pass


# --- DRIVE_PROGRESSION -------------------------------------------------------

def test_drive_progression_yardage_mode_real_generation_and_scoring():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_drive_progression_round(variant="NFL_DRAFT_PERFECT_DRIVE", question_count=10, seed="test-drive-1")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) == 10
    progress = me.initial_progress("DRIVE_PROGRESSION")
    q = pkg["questions"][0]
    correct = q["options"][q["correctIndex"]]
    result, progress = me.evaluate_submission("DRIVE_PROGRESSION", pkg, progress, {"answer": correct})
    assert result["correct"] is True
    assert result["yards_gained"] > 0
    assert progress["field_position_yards"] == result["yards_gained"]


def test_drive_progression_downs_mode_wrong_answer_costs_a_down():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_drive_progression_round(variant="NFL_DRAFT_GOAL_LINE_STAND", question_count=10, seed="test-drive-2")
    progress = me.initial_progress("DRIVE_PROGRESSION")
    result, progress = me.evaluate_submission("DRIVE_PROGRESSION", pkg, progress, {"answer": "definitely wrong"})
    assert result["correct"] is False
    assert progress["downs_remaining"] == pkg["downs_total"] - 1
    assert not progress["ended"]


def test_drive_progression_yardage_mode_ends_on_first_miss():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_drive_progression_round(variant="NFL_DRAFT_PERFECT_DRIVE", question_count=10, seed="test-drive-3")
    progress = me.initial_progress("DRIVE_PROGRESSION")
    result, progress = me.evaluate_submission("DRIVE_PROGRESSION", pkg, progress, {"answer": "definitely wrong"})
    assert result["correct"] is False
    assert progress["ended"] is True
    try:
        me.evaluate_submission("DRIVE_PROGRESSION", pkg, progress, {"answer": "anything"})
        assert False, "expected MechanicError -- drive already ended"
    except me.MechanicError:
        pass


def test_drive_progression_rejects_malformed_mode():
    from tools.director_v04 import drive_progression as dp
    try:
        dp.build_package("x", "v", mode="NOT_A_MODE", domain="NFL_DRAFT", relationship_predicate="DRAFTED_BY", question_count=5)
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- ROSTER_BUILD -------------------------------------------------------------

def test_roster_build_lineup_builder_real_full_completion():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="NFL_2010S_OFFENSE_BUILDER", seed="test-roster-1")
    assert pkg["qa_status"] == "PASSED"
    progress = me.initial_progress("ROSTER_BUILD")
    drafted_ids = set()
    for _slot in pkg["roster_slots"]:
        view = me.client_safe_view("ROSTER_BUILD", pkg, progress)
        pick = view["remaining_pool"][0]
        assert pick["player_id"] not in drafted_ids  # no player offered twice
        result, progress = me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"player_id": pick["player_id"]})
        drafted_ids.add(result["player_id"])
    assert progress["completed"] is True
    assert len(drafted_ids) == len(pkg["roster_slots"])


def test_roster_build_rejects_drafting_the_same_player_twice():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="NFL_2010S_OFFENSE_BUILDER", seed="test-roster-2")
    progress = me.initial_progress("ROSTER_BUILD")
    view = me.client_safe_view("ROSTER_BUILD", pkg, progress)
    pick = view["remaining_pool"][0]
    _, progress = me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"player_id": pick["player_id"]})
    try:
        me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"player_id": pick["player_id"]})
        assert False, "expected MechanicError"
    except me.MechanicError:
        pass


def test_roster_build_auction_draft_rejects_over_budget_pick():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="NFL_AUCTION_DRAFT", seed="test-roster-3")
    assert pkg["budgeted"] is True
    progress = me.initial_progress("ROSTER_BUILD")
    # Pick the second-most-expensive real QB (the single most expensive,
    # Aaron Rodgers, alone exceeds the entire fictional budget and would
    # fail at pick time) -- real, confirmed to leave too little remaining
    # budget for any real RB, which is exactly the scenario under test.
    qbs = sorted((p for p in pkg["players"] if p["position"] == "QB"), key=lambda p: -p["cost"])
    moderate_qb = qbs[1]
    _, progress = me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"player_id": moderate_qb["player_id"]})
    rbs = [p for p in pkg["players"] if p["position"] == "RB"]
    remaining = pkg["budget_total"] - moderate_qb["cost"]
    over_budget_rb = next((p for p in rbs if p["cost"] > remaining), None)
    assert over_budget_rb is not None, "expected at least one real RB over the remaining real budget"
    try:
        me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"player_id": over_budget_rb["player_id"]})
        assert False, "expected MechanicError -- over remaining budget"
    except me.MechanicError:
        pass


# --- KNOCKOUT_BRACKET ---------------------------------------------------------

def test_knockout_bracket_real_generation_all_sizes():
    from tools.director_v02 import mechanic_engine as me

    for variant, expected_size in (
        ("NFL_TEAM_SEASON_WINS_KNOCKOUT_4", 4), ("CFB_TEAM_SEASON_WINS_KNOCKOUT_16", 16),
    ):
        pkg = me.generate_knockout_bracket_round(variant=variant, seed="test-ko-1")
        assert pkg["qa_status"] == "PASSED"
        assert pkg["field_size"] == expected_size
        entrants = set()
        for r in pkg["rounds"][0]["matchups"]:
            entrants.add(r["entrant_a"])
            entrants.add(r["entrant_b"])
        assert len(entrants) == expected_size  # no duplicate/repeated entrant in round 1


def test_knockout_bracket_answer_validation_and_rejection():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_knockout_bracket_round(variant="NFL_TEAM_SEASON_WINS_KNOCKOUT_4", seed="test-ko-2")
    progress = me.initial_progress("KNOCKOUT_BRACKET")
    m0 = pkg["rounds"][0]["matchups"][0]
    result, progress = me.evaluate_submission("KNOCKOUT_BRACKET", pkg, progress,
                                               {"match_id": m0["match_id"], "predicted_winner": m0["entrant_a"]})
    assert result["predicted_winner"] == m0["entrant_a"]
    assert result["real_winner"] in (m0["entrant_a"], m0["entrant_b"])
    try:
        me.evaluate_submission("KNOCKOUT_BRACKET", pkg, progress,
                                {"match_id": m0["match_id"], "predicted_winner": "Not A Real Team"})
        assert False, "expected MechanicError"
    except me.MechanicError:
        pass


# --- RELATIONSHIP_CHAIN -------------------------------------------------------

def test_relationship_chain_real_generation_no_empty_chains():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_relationship_chain_round(variant="CFB_SCHOOL_TO_NFL_TEAM_CHAIN", chain_count=8, seed="test-chain-1")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["chain_count"] >= 5
    for ch in pkg["chains"]:
        assert len(ch["nodes"]) == 3
        assert all(n["label"] for n in ch["nodes"])  # no empty/missing node label


def test_relationship_chain_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_relationship_chain_round(variant="CFB_SCHOOL_TO_NFL_TEAM_CHAIN", chain_count=8, seed="test-chain-2")
    progress = me.initial_progress("RELATIONSHIP_CHAIN")
    real_end = pkg["chains"][0]["nodes"][-1]["label"]
    result, progress = me.evaluate_submission("RELATIONSHIP_CHAIN", pkg, progress, {"guess": real_end})
    assert result["correct"] is True
    result2, progress = me.evaluate_submission("RELATIONSHIP_CHAIN", pkg, progress, {"guess": "Definitely Not A Real Team"})
    assert result2["correct"] is False


# --- BRANCH_STATE --------------------------------------------------------------

def test_branch_state_real_generation_and_full_traversal():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_branch_state_round(variant="NFL_TOPIC_PATH", seed="test-branch-1")
    assert pkg["qa_status"] == "PASSED"
    progress = me.initial_progress("BRANCH_STATE")
    view = me.client_safe_view("BRANCH_STATE", pkg, progress)
    assert len(view["choices"]) >= 2
    choice_id = view["choices"][0]["choice_id"]
    result, progress = me.evaluate_submission("BRANCH_STATE", pkg, progress, {"choice_id": choice_id})
    assert "leaf_question" in result
    q = result["leaf_question"]
    correct = q["options"][q["correctIndex"]]
    result2, progress = me.evaluate_submission("BRANCH_STATE", pkg, progress, {"answer": correct})
    assert result2["correct"] is True
    assert progress["completed"] is True


def test_branch_state_rejects_invalid_choice_id():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_branch_state_round(variant="NFL_TOPIC_PATH", seed="test-branch-2")
    progress = me.initial_progress("BRANCH_STATE")
    try:
        me.evaluate_submission("BRANCH_STATE", pkg, progress, {"choice_id": "NOT_A_REAL_CHOICE"})
        assert False, "expected MechanicError"
    except me.MechanicError:
        pass
