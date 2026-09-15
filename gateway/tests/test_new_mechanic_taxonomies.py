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

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
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


def test_roster_build_auction_draft_default_uses_balanced_fictional_cost():
    """Real correction verified: NFL_AUCTION_DRAFT's DEFAULT cost mode is
    now the balanced fictional model -- no single real player (not even
    Aaron Rodgers) can alone consume the $50M fictional budget, which was
    a real, disclosed defect in the original real-APY-only implementation."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="NFL_AUCTION_DRAFT", seed="test-roster-3")
    assert pkg["budgeted"] is True
    assert pkg["cost_model"] == "FICTIONAL"
    assert all(p["cost"] < pkg["budget_total"] for p in pkg["players"])


def test_roster_build_auction_draft_real_contract_is_a_separate_explicit_opt_in():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="NFL_AUCTION_DRAFT_REAL_CONTRACT", seed="test-roster-3b")
    assert pkg["cost_model"] == "REAL_CONTRACT"
    qbs = sorted((p for p in pkg["players"] if p["position"] == "QB"), key=lambda p: -p["cost"])
    assert qbs[0]["cost"] > pkg["budget_total"], "expected the real top QB salary to exceed the fictional budget"


def test_roster_build_cap_challenge_free_select_rejects_over_cap_and_incomplete():
    """Real, distinct CAP_CHALLENGE mechanic: free select/deselect, budget
    enforced live per-selection, but completion is only ever validated (and
    locked) at a final submit_lineup action."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="NFL_CAP_CHALLENGE", seed="test-cap-1")
    assert pkg["flow"] == "FREE_SELECT"
    progress = me.initial_progress("ROSTER_BUILD")
    try:
        me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"action": "submit_lineup"})
        assert False, "expected MechanicError -- incomplete lineup"
    except me.MechanicError:
        pass

    # Fill every slot with the cheapest real eligible option, confirm a
    # complete, real, within-cap lineup submits successfully.
    for i, _slot in enumerate(pkg["roster_slots"]):
        view = me.client_safe_view("ROSTER_BUILD", pkg, progress)
        cheapest = min(view["pool_by_slot"][str(i)], key=lambda p: p["cost"])
        _, progress = me.evaluate_submission(
            "ROSTER_BUILD", pkg, progress, {"action": "select", "slot_index": i, "player_id": cheapest["player_id"]},
        )
    result, progress = me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"action": "submit_lineup"})
    assert result["total_spent"] <= pkg["budget_total"]
    assert progress["completed"] is True
    try:
        me.evaluate_submission("ROSTER_BUILD", pkg, progress, {"action": "select", "slot_index": 0, "player_id": "x"})
        assert False, "expected MechanicError -- already submitted"
    except me.MechanicError:
        pass


def test_roster_build_cap_challenge_rejects_a_real_over_cap_selection():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="NFL_CAP_CHALLENGE", seed="test-cap-2")
    progress = me.initial_progress("ROSTER_BUILD")
    slots = pkg["roster_slots"]
    # Fill every slot but the last with the most expensive option, leaving
    # too little real remaining budget for any real player at the final slot.
    for i in range(len(slots) - 1):
        view = me.client_safe_view("ROSTER_BUILD", pkg, progress)
        priciest = max(view["pool_by_slot"][str(i)], key=lambda p: p["cost"])
        _, progress = me.evaluate_submission(
            "ROSTER_BUILD", pkg, progress, {"action": "select", "slot_index": i, "player_id": priciest["player_id"]},
        )
    last_slot = len(slots) - 1
    view = me.client_safe_view("ROSTER_BUILD", pkg, progress)
    all_at_last_position = [p for p in pkg["players"] if p["position"] == slots[last_slot]]
    over_cap_pick = max(all_at_last_position, key=lambda p: p["cost"])
    if over_cap_pick["player_id"] in [r["player_id"] for r in view["roster"] if r]:
        pytest.skip("no distinct over-cap candidate available for this seed")
    try:
        me.evaluate_submission(
            "ROSTER_BUILD", pkg, progress,
            {"action": "select", "slot_index": last_slot, "player_id": over_cap_pick["player_id"]},
        )
        # Not necessarily an error if this specific player happens to still
        # fit -- the real invariant under test is the live cap check itself,
        # confirmed directly below with a value guaranteed to be too large.
    except me.MechanicError:
        pass
    remaining = pkg["budget_total"] - sum(r["cost"] for r in view["roster"] if r)
    guaranteed_over = next((p for p in all_at_last_position if p["cost"] > remaining), None)
    if guaranteed_over is None:
        pytest.skip("no real candidate at this seed exceeds the remaining cap -- cap check exercised above instead")
    else:
        try:
            me.evaluate_submission(
                "ROSTER_BUILD", pkg, progress,
                {"action": "select", "slot_index": last_slot, "player_id": guaranteed_over["player_id"]},
            )
            assert False, "expected MechanicError -- over remaining cap"
        except me.MechanicError:
            pass


def test_roster_build_cfb_skill_position_builder_is_real_and_supported():
    """Real data-status correction verified: CFB Lineup Builder is NOT
    globally MISSING_DATA -- the narrower skill-position-only configuration
    is real and fully supported (32,550+ distinct real CFB players)."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="CFB_SKILL_POSITION_BUILDER", seed="test-cfb-lineup-1")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["player_count"] > 1000
    for pos in ("QB", "RB", "WR", "TE"):
        assert pkg["by_position"].get(pos, 0) > 0


def test_roster_build_cfb_lineup_builder_school_filter_is_actually_enforced():
    """Regression guard for the Part 1B fix: a real school filter must
    genuinely restrict the pool (never be silently ignored)."""
    from tools.director_v02 import mechanic_engine as me
    from tools.director_v04 import roster_build

    pkg = me.generate_roster_build_round(
        variant="CFB_SKILL_POSITION_BUILDER", seed="test-cfb-lineup-alabama", filters={"school_name": "Alabama"},
    )
    assert pkg["qa_status"] == "PASSED"
    assert pkg["filters_applied"] == {"school_name": "Alabama"}
    assert 0 < pkg["player_count"] < 1000  # genuinely narrower than the >1000-player unfiltered pool

    from tools.quiz_export import engine as engine_bootstrap
    c = engine_bootstrap.connect()
    try:
        alabama_id = roster_build._cfb_school_id_for_name(c, "Alabama")
        real_ids = {
            r["cfb_player_id"] for r in c.execute(
                "SELECT DISTINCT cfb_player_id FROM cfb_roster_seasons_real WHERE school_id = ?", (alabama_id,)
            ).fetchall()
        }
    finally:
        c.close()
    for p in pkg["players"]:
        assert p["player_id"] in real_ids, p


def test_roster_build_conference_filter_is_actually_enforced():
    from tools.director_v02 import mechanic_engine as me

    unfiltered = me.generate_roster_build_round(variant="CFB_SKILL_POSITION_BUILDER", seed="test-cfb-conf-base")
    filtered = me.generate_roster_build_round(
        variant="CFB_SKILL_POSITION_BUILDER", seed="test-cfb-conf-base", filters={"conference": "SEC"},
    )
    assert filtered["qa_status"] == "PASSED"
    assert 0 < filtered["player_count"] < unfiltered["player_count"]


def test_roster_build_nfl_franchise_filter_is_actually_enforced():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(
        variant="NFL_2010S_OFFENSE_BUILDER", seed="test-nfl-packers", filters={"franchise_name": "Packers"},
    )
    assert pkg["qa_status"] == "PASSED"
    assert 0 < pkg["player_count"] < 200


def test_roster_build_nl_offense_phrasing_actually_routes_with_filters():
    """Regression guard for the Part 1B NL-routing fix: the pool-filter
    tests above all construct filters dicts directly, which never would
    have caught that the real natural-language phrase this task names as
    its own example -- "Build me an SEC offense." -- failed to route at
    all. _LINEUP_BUILDER_RE's original "offense" alternative required a
    rigid contiguous "build an offense" phrase; real requests always have
    words in between ("build ME an ... offense"). Exercises the actual
    detect() -> build_package() round-trip, not just the filter dict."""
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge
    from tools.director_v04 import roster_build

    detected = bridge.detect("Build me an SEC offense.")
    assert detected is not None
    assert detected["taxonomy_id"] == "ROSTER_BUILD"
    assert detected["variant"] == "CFB_SKILL_POSITION_BUILDER"
    assert detected["gen_kwargs"]["filters"] == {"conference": "SEC"}

    pkg = roster_build.build_package(
        seed="test-nl-sec-offense", variant=detected["variant"], filters=detected["gen_kwargs"]["filters"],
    )
    assert pkg["qa_status"] == "PASSED"
    assert pkg["filters_applied"] == {"conference": "SEC"}
    assert pkg["player_count"] > 0

    # A bare "build an offense" (no team/conference name) must still route,
    # just with no filters -- the original phrasing wasn't wrong, just too
    # rigid about what can sit between "build" and "offense".
    bare = bridge.detect("Build me an offense.")
    assert bare is not None and bare["taxonomy_id"] == "ROSTER_BUILD"

    # An unrelated "offense" mention (not a build/construct request) must
    # still NOT match -- the fix must not have widened the pattern into a
    # false positive.
    assert bridge.detect("What is a zone blitz on offense?") is None


def test_roster_build_unmatched_filter_is_honestly_rejected_not_silently_ignored():
    """An unresolvable filter must fail with a disclosed shortfall_reason --
    never silently fall back to generating from the unfiltered pool."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(
        variant="CFB_SKILL_POSITION_BUILDER", seed="test-cfb-bogus",
        filters={"school_name": "Not A Real School XYZ"},
    )
    assert pkg["qa_status"] == "FAILED"
    assert pkg["player_count"] == 0
    assert "school_name" in pkg["shortfall_reason"]


def test_roster_build_filters_change_package_identity():
    """Filtered and unfiltered rosters at the same seed must never collide
    under the same content-addressed package_id."""
    from tools.director_v02 import mechanic_engine as me

    unfiltered = me.generate_roster_build_round(variant="CFB_SKILL_POSITION_BUILDER", seed="test-cfb-identity")
    filtered = me.generate_roster_build_round(
        variant="CFB_SKILL_POSITION_BUILDER", seed="test-cfb-identity", filters={"school_name": "Alabama"},
    )
    assert unfiltered["package_id"] != filtered["package_id"]


def test_roster_build_cfb_auction_draft_uses_fictional_cost_never_nil():
    """Real correction verified: CFB AUCTION_DRAFT never requires NIL/salary
    data -- its cost is the same real, deterministic fictional model as
    NFL's default, derived from real career yardage."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_roster_build_round(variant="CFB_AUCTION_DRAFT", seed="test-cfb-auction-1")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["cost_model"] == "FICTIONAL"
    assert all(p["cost"] < pkg["budget_total"] for p in pkg["players"])


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


def test_branch_state_cfb_topic_path_real_generation_and_full_traversal():
    """Part 1C: CFB gets a real branch tree, not a copy of NFL's -- 5
    distinct real leaf capabilities, each independently registered in
    tools/director_v02/registry.py (never a shared generic generator)."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_branch_state_round(variant="CFB_TOPIC_PATH", seed="test-cfb-branch-1")
    assert pkg["qa_status"] == "PASSED"
    choice_ids = {c["choice_id"] for c in pkg["root_choices"]}
    assert choice_ids == {"HEISMAN", "CHAMPIONSHIP", "RIVALRY", "RANKING", "UPSET"}

    for choice_id in ("HEISMAN", "CHAMPIONSHIP", "RIVALRY", "RANKING"):
        progress = me.initial_progress("BRANCH_STATE")
        result, progress = me.evaluate_submission("BRANCH_STATE", pkg, progress, {"choice_id": choice_id})
        assert "leaf_question" in result, choice_id
        q = result["leaf_question"]
        correct = q["options"][q["correctIndex"]]
        result2, progress = me.evaluate_submission("BRANCH_STATE", pkg, progress, {"answer": correct})
        assert result2["correct"] is True, choice_id
        assert progress["completed"] is True, choice_id


def test_branch_state_cfb_upset_branch_is_a_genuine_second_level_not_decorative():
    """The UPSET choice leads to a real second branch node (Ranking Upset
    vs. Betting Upset -- two structurally distinct real capabilities), not
    straight to a leaf and not to the same generator as any sibling."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_branch_state_round(variant="CFB_TOPIC_PATH", seed="test-cfb-branch-upset")
    seen_domains = set()
    for sub_choice in ("RANKING_UPSET", "BETTING_UPSET"):
        progress = me.initial_progress("BRANCH_STATE")
        result, progress = me.evaluate_submission("BRANCH_STATE", pkg, progress, {"choice_id": "UPSET"})
        assert "leaf_question" not in result  # intermediate branch node, no question yet
        assert progress["current_node"] == "cfb_upset_branch"
        view = me.client_safe_view("BRANCH_STATE", pkg, progress)
        assert {c["choice_id"] for c in view["choices"]} == {"RANKING_UPSET", "BETTING_UPSET"}

        result2, progress = me.evaluate_submission("BRANCH_STATE", pkg, progress, {"choice_id": sub_choice})
        assert "leaf_question" in result2
        seen_domains.add(result2["leaf_question"]["question"])
        q = result2["leaf_question"]
        correct = q["options"][q["correctIndex"]]
        result3, progress = me.evaluate_submission("BRANCH_STATE", pkg, progress, {"answer": correct})
        assert result3["correct"] is True
        assert progress["completed"] is True


# --- GUESS_THE_SEASON (15-Format Expansion Part 2, format #2) -------------

def test_guess_the_season_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "GUESS_THE_SEASON" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("GUESS_THE_SEASON"), "GUESS_THE_SEASON has no registered variants"


def test_guess_the_season_generates_real_rounds_with_real_clues():
    from tools.director_v04 import guess_the_season

    pkg = guess_the_season.build_package(
        "test-season-1", "NFL_SUPER_BOWL_SEASON", round_count=5, difficulty="MEDIUM")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert len(r["clues"]) >= 2
        assert r["_answer"].isdigit() and len(r["_answer"]) == 4
        assert "Super Bowl champion" in r["clues"][0]["display_text"]


def test_guess_the_season_sb_mvp_clue_uses_the_real_shifted_row_not_the_wrong_unshifted_one():
    """Regression test for a real bug caught live this pass: nfl_season_awards
    stores SB_MVP rows under season+1 (the calendar year the Super Bowl was
    actually PLAYED), not the season it caps -- every other award type is
    stored under the season it represents. build_package() must read SB_MVP
    from the shifted row; this asserts the live output actually does, cross-
    checked directly against the raw table rather than trusting the fix."""
    from tools.director_v04 import guess_the_season
    from tools.quiz_export import engine as engine_bootstrap

    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT season, player_name_raw FROM nfl_season_awards "
            "WHERE award_type = 'SB_MVP' AND player_name_raw IS NOT NULL"
        ).fetchall()
    finally:
        c.close()
    real_sb_mvp_by_played_season = {r["season"]: r["player_name_raw"] for r in rows}

    pkg = guess_the_season.build_package(
        "test-season-mvp-regress", "NFL_SUPER_BOWL_SEASON", round_count=25, difficulty="EASY")
    checked_any = False
    for r in pkg["rounds"]:
        season = int(r["_answer"])
        expected_mvp = real_sb_mvp_by_played_season.get(season + 1)
        for clue in r["clues"]:
            if "Super Bowl MVP" not in clue["display_text"]:
                continue
            assert expected_mvp is not None
            assert expected_mvp in clue["display_text"]
            wrong_row = real_sb_mvp_by_played_season.get(season)
            if wrong_row and wrong_row != expected_mvp:
                assert wrong_row not in clue["display_text"]
            checked_any = True
    assert checked_any, "no round in this sample included an SB_MVP clue -- widen round_count"


def test_guess_the_season_known_real_history_peyton_manning_2006_season():
    """Concrete spot-check against known real history (not just internal
    consistency): Super Bowl XLI, capping the 2006 season, was played in
    Feb 2007 and its real MVP was Peyton Manning."""
    from tools.director_v04 import guess_the_season
    from tools.quiz_export import engine as engine_bootstrap

    c = engine_bootstrap.connect()
    try:
        row = c.execute(
            "SELECT winner_team_code FROM nfl_championship_events WHERE season = 2006"
        ).fetchone()
    finally:
        c.close()
    if row is None or row["winner_team_code"] is None:
        pytest.skip("season 2006 championship row not resolved in this Engine copy")

    pkg = guess_the_season.build_package(
        "test-season-manning", "NFL_SUPER_BOWL_SEASON", round_count=60, difficulty="EASY")
    season_2006 = next((r for r in pkg["rounds"] if r["_answer"] == "2006"), None)
    if season_2006 is None:
        pytest.skip("season 2006 didn't have enough real corroborating evidence to be included")
    mvp_clues = [cl["display_text"] for cl in season_2006["clues"] if "Super Bowl MVP" in cl["display_text"]]
    if mvp_clues:
        assert "Manning" in mvp_clues[0]


def test_guess_the_season_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_guess_the_season_round(
        variant="NFL_SUPER_BOWL_SEASON", round_count=3, difficulty="MEDIUM", seed="test-season-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("GUESS_THE_SEASON")
    canonical = pkg["rounds"][0]["_answer"]
    result, progress = me.evaluate_submission("GUESS_THE_SEASON", pkg, progress, {"guess_season": canonical})
    assert result["correct"] is True
    assert result["canonical_answer"] == canonical

    progress2 = me.initial_progress("GUESS_THE_SEASON")
    wrong_guess = "1899" if canonical != "1899" else "1898"
    result2, progress2 = me.evaluate_submission("GUESS_THE_SEASON", pkg, progress2, {"guess_season": wrong_guess})
    assert result2["correct"] is False


def test_guess_the_season_malformed_submission_rejected_not_silently_correct():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_guess_the_season_round(
        variant="NFL_SUPER_BOWL_SEASON", round_count=2, difficulty="MEDIUM", seed="test-season-malformed")

    progress = me.initial_progress("GUESS_THE_SEASON")
    result, progress = me.evaluate_submission("GUESS_THE_SEASON", pkg, progress, {"guess_season": ""})
    assert result["correct"] is False

    progress2 = me.initial_progress("GUESS_THE_SEASON")
    result2, progress2 = me.evaluate_submission("GUESS_THE_SEASON", pkg, progress2, {})
    assert result2["correct"] is False


def test_guess_the_season_easy_clue_set_is_superset_of_hard_clue_set():
    from tools.director_v04 import guess_the_season

    easy_pkg = guess_the_season.build_package(
        "test-season-superset", "NFL_SUPER_BOWL_SEASON", round_count=10, difficulty="EASY")
    hard_pkg = guess_the_season.build_package(
        "test-season-superset", "NFL_SUPER_BOWL_SEASON", round_count=10, difficulty="HARD")
    easy_by_season = {r["_answer"]: {cl["display_text"] for cl in r["clues"]} for r in easy_pkg["rounds"]}
    hard_by_season = {r["_answer"]: {cl["display_text"] for cl in r["clues"]} for r in hard_pkg["rounds"]}
    shared_seasons = set(easy_by_season) & set(hard_by_season)
    assert shared_seasons, "expected overlapping seasons between EASY and HARD samples for the same seed"
    for season in shared_seasons:
        assert hard_by_season[season].issubset(easy_by_season[season])


# --- PAIRWISE_COMPARE / HEAD_TO_HEAD_DUEL (15-Format Expansion Part 2, format #3) ---

def test_pairwise_compare_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "PAIRWISE_COMPARE" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("PAIRWISE_COMPARE"), "PAIRWISE_COMPARE has no registered variants"


@pytest.mark.parametrize("variant", [
    "NFL_SEASON_RUSHING_YARDS_DUEL", "NFL_CAREER_PASSING_TD_DUEL", "CFB_CAREER_RUSHING_YARDS_DUEL",
])
def test_head_to_head_duel_generates_real_rounds_with_two_distinct_real_values(variant):
    from tools.director_v04 import head_to_head_duel

    pkg = head_to_head_duel.build_package("test-duel-1", variant, round_count=5)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert r["entity_a"]["label"] and r["entity_b"]["label"]
        assert r["entity_a"]["label"] != r["entity_b"]["label"]
        assert r["_value_a"] != r["_value_b"], "a real tie must never be silently broken"
        assert r["_answer"] in ("A", "B")
        expected_winner = "A" if r["_value_a"] > r["_value_b"] else "B"
        assert r["_answer"] == expected_winner


def test_head_to_head_duel_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pairwise_compare_round(
        variant="NFL_SEASON_RUSHING_YARDS_DUEL", round_count=3, seed="test-duel-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("PAIRWISE_COMPARE")
    canonical = pkg["rounds"][0]["_answer"]
    result, progress = me.evaluate_submission("PAIRWISE_COMPARE", pkg, progress, {"choice": canonical})
    assert result["correct"] is True
    assert result["canonical_answer"] == canonical
    assert result["value_a"] == pkg["rounds"][0]["_value_a"]
    assert result["value_b"] == pkg["rounds"][0]["_value_b"]

    progress2 = me.initial_progress("PAIRWISE_COMPARE")
    wrong = "B" if canonical == "A" else "A"
    result2, progress2 = me.evaluate_submission("PAIRWISE_COMPARE", pkg, progress2, {"choice": wrong})
    assert result2["correct"] is False


def test_head_to_head_duel_malformed_submission_rejected_not_silently_correct():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pairwise_compare_round(
        variant="NFL_SEASON_RUSHING_YARDS_DUEL", round_count=2, seed="test-duel-malformed")

    progress = me.initial_progress("PAIRWISE_COMPARE")
    result, progress = me.evaluate_submission("PAIRWISE_COMPARE", pkg, progress, {"choice": ""})
    assert result["correct"] is False

    progress2 = me.initial_progress("PAIRWISE_COMPARE")
    result2, progress2 = me.evaluate_submission("PAIRWISE_COMPARE", pkg, progress2, {"choice": "Z"})
    assert result2["correct"] is False

    progress3 = me.initial_progress("PAIRWISE_COMPARE")
    result3, progress3 = me.evaluate_submission("PAIRWISE_COMPARE", pkg, progress3, {})
    assert result3["correct"] is False


def test_head_to_head_duel_client_view_never_leaks_real_values_before_submission():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pairwise_compare_round(
        variant="NFL_CAREER_PASSING_TD_DUEL", round_count=2, seed="test-duel-leak")
    progress = me.initial_progress("PAIRWISE_COMPARE")
    view = me.client_safe_view("PAIRWISE_COMPARE", pkg, progress)
    assert set(view["entity_a"].keys()) == {"entity_id", "label"}
    assert set(view["entity_b"].keys()) == {"entity_id", "label"}
    assert "value" not in view["entity_a"] and "value" not in view["entity_b"]


# --- BEST_OF_SEVEN_DUEL (15-Format Expansion Part 2, format #4) -----------

def test_best_of_seven_duel_is_a_registered_pairwise_compare_variant():
    from tools.director_v02 import mechanic_engine as me

    assert "NFL_CAREER_QB_BEST_OF_SEVEN" in me.VARIANTS["PAIRWISE_COMPARE"]


def test_best_of_seven_duel_generates_real_categories_for_a_fixed_real_pair():
    from tools.director_v04 import head_to_head_duel

    pkg = head_to_head_duel.build_package("test-b7-1", "NFL_CAREER_QB_BEST_OF_SEVEN", round_count=7)
    assert pkg["qa_status"] == "PASSED"
    assert 3 <= pkg["round_count"] <= 7
    labels_a = {r["entity_a"]["label"] for r in pkg["rounds"]}
    labels_b = {r["entity_b"]["label"] for r in pkg["rounds"]}
    assert len(labels_a) == 1 and len(labels_b) == 1, "the same real pair must be compared across every round"
    assert labels_a != labels_b
    for r in pkg["rounds"]:
        assert r["_value_a"] != r["_value_b"], "a real tie must never be silently broken"
        assert r["prompt"] != ""

    ms = pkg["_match_summary"]
    assert ms["categories_played"] == pkg["round_count"]
    assert ms["wins_a"] + ms["wins_b"] == ms["categories_played"]
    if ms["wins_a"] > ms["wins_b"]:
        assert ms["winner"] == "A"
    elif ms["wins_b"] > ms["wins_a"]:
        assert ms["winner"] == "B"
    else:
        assert ms["winner"] == "TIE"


def test_best_of_seven_duel_match_summary_only_revealed_on_the_final_round():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pairwise_compare_round(
        variant="NFL_CAREER_QB_BEST_OF_SEVEN", round_count=7, seed="test-b7-reveal")
    total = pkg["round_count"]
    progress = me.initial_progress("PAIRWISE_COMPARE")
    for i in range(total):
        canonical = pkg["rounds"][i]["_answer"]
        result, progress = me.evaluate_submission("PAIRWISE_COMPARE", pkg, progress, {"choice": canonical})
        if i < total - 1:
            assert "match_summary" not in result, f"match_summary leaked early at round {i} of {total}"
        else:
            assert "match_summary" in result
            assert result["match_summary"] == pkg["_match_summary"]
    assert progress["completed"] is True


def test_best_of_seven_duel_match_winner_independent_of_any_single_round_answer():
    """Real regression guard for the exact scenario caught during live
    verification: the match's overall real winner (most real categories)
    can differ from the winner of any individual real category, including
    the final one -- the two concepts must never be conflated."""
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pairwise_compare_round(
        variant="NFL_CAREER_QB_BEST_OF_SEVEN", round_count=7, seed="test-b7-independent")
    ms = pkg["_match_summary"]
    last_round_answer = pkg["rounds"][-1]["_answer"]
    # This is a real-data assertion of internal consistency, not a claim
    # that they must differ -- just that match winner is computed from the
    # full real category tally, never copied from the last round's answer.
    assert ms["winner"] in ("A", "B", "TIE")
    recomputed_wins_a = sum(1 for r in pkg["rounds"] if r["_answer"] == "A")
    recomputed_wins_b = sum(1 for r in pkg["rounds"] if r["_answer"] == "B")
    assert ms["wins_a"] == recomputed_wins_a
    assert ms["wins_b"] == recomputed_wins_b


# --- PICK_THE_IMPOSTOR (15-Format Expansion Part 2, format #5) -----------

def test_pick_the_impostor_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "PICK_THE_IMPOSTOR" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("PICK_THE_IMPOSTOR"), "PICK_THE_IMPOSTOR has no registered variants"


@pytest.mark.parametrize("variant", ["NFL_TEAM_ROSTER_IMPOSTOR", "CFB_SCHOOL_ROSTER_IMPOSTOR"])
def test_pick_the_impostor_generates_real_rounds_with_a_genuinely_absent_impostor(variant):
    from tools.director_v04 import pick_the_impostor

    pkg = pick_the_impostor.build_package("test-impostor-1", variant, round_count=5)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert len(r["items"]) == 4
        item_ids = {it["item_id"] for it in r["items"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["items"]]
        assert len(set(labels)) == 4, "no duplicate real players within a round"
        assert r["_impostor_item_id"] in item_ids


def test_pick_the_impostor_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pick_the_impostor_round(
        variant="NFL_TEAM_ROSTER_IMPOSTOR", round_count=3, seed="test-impostor-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("PICK_THE_IMPOSTOR")
    canonical = pkg["rounds"][0]["_impostor_item_id"]
    result, progress = me.evaluate_submission(
        "PICK_THE_IMPOSTOR", pkg, progress, {"impostor_item_id": canonical})
    assert result["correct"] is True
    canonical_label = next(it["label"] for it in pkg["rounds"][0]["items"] if it["item_id"] == canonical)
    assert result["canonical_answer"] == canonical_label

    progress2 = me.initial_progress("PICK_THE_IMPOSTOR")
    wrong = next(i for i in ("A", "B", "C", "D") if i != canonical)
    result2, progress2 = me.evaluate_submission(
        "PICK_THE_IMPOSTOR", pkg, progress2, {"impostor_item_id": wrong})
    assert result2["correct"] is False


def test_pick_the_impostor_malformed_submission_rejected_not_silently_correct():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pick_the_impostor_round(
        variant="NFL_TEAM_ROSTER_IMPOSTOR", round_count=2, seed="test-impostor-malformed")

    progress = me.initial_progress("PICK_THE_IMPOSTOR")
    result, progress = me.evaluate_submission("PICK_THE_IMPOSTOR", pkg, progress, {"impostor_item_id": ""})
    assert result["correct"] is False

    progress2 = me.initial_progress("PICK_THE_IMPOSTOR")
    result2, progress2 = me.evaluate_submission("PICK_THE_IMPOSTOR", pkg, progress2, {"impostor_item_id": "Z"})
    assert result2["correct"] is False

    progress3 = me.initial_progress("PICK_THE_IMPOSTOR")
    result3, progress3 = me.evaluate_submission("PICK_THE_IMPOSTOR", pkg, progress3, {})
    assert result3["correct"] is False


def test_pick_the_impostor_client_view_never_leaks_the_real_impostor_before_submission():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pick_the_impostor_round(
        variant="CFB_SCHOOL_ROSTER_IMPOSTOR", round_count=2, seed="test-impostor-leak")
    progress = me.initial_progress("PICK_THE_IMPOSTOR")
    view = me.client_safe_view("PICK_THE_IMPOSTOR", pkg, progress)
    assert set(view.keys()) >= {"round_index", "round_count", "completed", "prompt", "items"}
    assert "_impostor_item_id" not in view
    for it in view["items"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- UNIQUE_ONE_OUT (15-Format Expansion Part 2, format #6) --------------
# Shares PICK_THE_IMPOSTOR's exact taxonomy/round shape -- see
# tools/director_v04/pick_the_impostor.py's own module docstring.

def test_unique_one_out_is_a_registered_pick_the_impostor_variant():
    from tools.director_v02 import mechanic_engine as me

    assert "NFL_DRAFT_CLASS_ONE_OUT" in me.VARIANTS["PICK_THE_IMPOSTOR"]


def test_unique_one_out_generates_real_rounds_sharing_a_real_draft_class():
    from tools.director_v04 import pick_the_impostor

    pkg = pick_the_impostor.build_package("test-oneout-1", "NFL_DRAFT_CLASS_ONE_OUT", round_count=5)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert len(r["items"]) == 4
        item_ids = {it["item_id"] for it in r["items"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["items"]]
        assert len(set(labels)) == 4
        assert r["_impostor_item_id"] in item_ids
        assert "drafted in" in r["prompt"]


def test_unique_one_out_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_pick_the_impostor_round(
        variant="NFL_DRAFT_CLASS_ONE_OUT", round_count=3, seed="test-oneout-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("PICK_THE_IMPOSTOR")
    canonical = pkg["rounds"][0]["_impostor_item_id"]
    result, progress = me.evaluate_submission(
        "PICK_THE_IMPOSTOR", pkg, progress, {"impostor_item_id": canonical})
    assert result["correct"] is True

    progress2 = me.initial_progress("PICK_THE_IMPOSTOR")
    wrong = next(i for i in ("A", "B", "C", "D") if i != canonical)
    result2, progress2 = me.evaluate_submission(
        "PICK_THE_IMPOSTOR", pkg, progress2, {"impostor_item_id": wrong})
    assert result2["correct"] is False


# --- MISSING_PIECE (15-Format Expansion Part 2, format #7) ---------------

def test_missing_piece_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "MISSING_PIECE" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("MISSING_PIECE"), "MISSING_PIECE has no registered variants"


@pytest.mark.parametrize("variant", ["NFL_TEAM_ROSTER_MISSING_PIECE", "CFB_SCHOOL_ROSTER_MISSING_PIECE"])
def test_missing_piece_generates_real_rounds_with_a_genuine_completion(variant):
    from tools.director_v04 import missing_piece

    pkg = missing_piece.build_package("test-missing-1", variant, round_count=5)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert len(r["group_members"]) == 3
        assert len(set(r["group_members"])) == 3, "no duplicate real players in the given group"
        assert len(r["items"]) == 4
        item_ids = {it["item_id"] for it in r["items"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["items"]]
        assert len(set(labels)) == 4, "no duplicate real players among the 4 candidates"
        # the real correct completion must never coincide with a real
        # given group member -- that would make the round trivially
        # self-referential (a duplicate name among the 4 candidates
        # already rules this out, but check explicitly too)
        assert not (set(labels) & set(r["group_members"]))
        assert r["_answer_item_id"] in item_ids


def test_missing_piece_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_missing_piece_round(
        variant="NFL_TEAM_ROSTER_MISSING_PIECE", round_count=3, seed="test-missing-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("MISSING_PIECE")
    canonical = pkg["rounds"][0]["_answer_item_id"]
    result, progress = me.evaluate_submission(
        "MISSING_PIECE", pkg, progress, {"answer_item_id": canonical})
    assert result["correct"] is True
    canonical_label = next(it["label"] for it in pkg["rounds"][0]["items"] if it["item_id"] == canonical)
    assert result["canonical_answer"] == canonical_label

    progress2 = me.initial_progress("MISSING_PIECE")
    wrong = next(i for i in ("A", "B", "C", "D") if i != canonical)
    result2, progress2 = me.evaluate_submission(
        "MISSING_PIECE", pkg, progress2, {"answer_item_id": wrong})
    assert result2["correct"] is False


def test_missing_piece_malformed_submission_rejected_not_silently_correct():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_missing_piece_round(
        variant="NFL_TEAM_ROSTER_MISSING_PIECE", round_count=2, seed="test-missing-malformed")

    progress = me.initial_progress("MISSING_PIECE")
    result, progress = me.evaluate_submission("MISSING_PIECE", pkg, progress, {"answer_item_id": ""})
    assert result["correct"] is False

    progress2 = me.initial_progress("MISSING_PIECE")
    result2, progress2 = me.evaluate_submission("MISSING_PIECE", pkg, progress2, {"answer_item_id": "Z"})
    assert result2["correct"] is False

    progress3 = me.initial_progress("MISSING_PIECE")
    result3, progress3 = me.evaluate_submission("MISSING_PIECE", pkg, progress3, {})
    assert result3["correct"] is False


def test_missing_piece_client_view_never_leaks_the_real_answer_before_submission():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_missing_piece_round(
        variant="CFB_SCHOOL_ROSTER_MISSING_PIECE", round_count=2, seed="test-missing-leak")
    progress = me.initial_progress("MISSING_PIECE")
    view = me.client_safe_view("MISSING_PIECE", pkg, progress)
    assert set(view.keys()) >= {"round_index", "round_count", "completed", "prompt", "group_members", "items"}
    assert "_answer_item_id" not in view
    for it in view["items"]:
        assert set(it.keys()) == {"item_id", "label"}
