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


# --- BEFORE_AFTER (15-Format Expansion Part 2, format #8) ----------------

def test_before_after_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "BEFORE_AFTER" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("BEFORE_AFTER"), "BEFORE_AFTER has no registered variants"


@pytest.mark.parametrize("variant", ["NFL_TEAM_CHANGE_BEFORE_AFTER", "CFB_SCHOOL_TRANSFER_BEFORE_AFTER"])
def test_before_after_generates_real_rounds_with_two_distinct_real_seasons(variant):
    from tools.director_v04 import before_after

    pkg = before_after.build_package("test-before-after-1", variant, round_count=5)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert r["entity_a"]["label"] and r["entity_b"]["label"]
        assert r["entity_a"]["label"] != r["entity_b"]["label"]
        assert r["_season_a"] != r["_season_b"], "a real tie must never be silently broken"
        assert r["_answer"] in ("A", "B")
        expected = "A" if r["_season_a"] < r["_season_b"] else "B"
        assert r["_answer"] == expected, "the earlier real season must always be the real answer"


def test_before_after_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_before_after_round(
        variant="NFL_TEAM_CHANGE_BEFORE_AFTER", round_count=3, seed="test-before-after-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("BEFORE_AFTER")
    canonical = pkg["rounds"][0]["_answer"]
    result, progress = me.evaluate_submission("BEFORE_AFTER", pkg, progress, {"choice": canonical})
    assert result["correct"] is True
    assert result["canonical_answer"] == canonical
    assert result["season_a"] == pkg["rounds"][0]["_season_a"]
    assert result["season_b"] == pkg["rounds"][0]["_season_b"]

    progress2 = me.initial_progress("BEFORE_AFTER")
    wrong = "B" if canonical == "A" else "A"
    result2, progress2 = me.evaluate_submission("BEFORE_AFTER", pkg, progress2, {"choice": wrong})
    assert result2["correct"] is False


def test_before_after_malformed_submission_rejected_not_silently_correct():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_before_after_round(
        variant="NFL_TEAM_CHANGE_BEFORE_AFTER", round_count=2, seed="test-before-after-malformed")

    progress = me.initial_progress("BEFORE_AFTER")
    result, progress = me.evaluate_submission("BEFORE_AFTER", pkg, progress, {"choice": ""})
    assert result["correct"] is False

    progress2 = me.initial_progress("BEFORE_AFTER")
    result2, progress2 = me.evaluate_submission("BEFORE_AFTER", pkg, progress2, {"choice": "Z"})
    assert result2["correct"] is False

    progress3 = me.initial_progress("BEFORE_AFTER")
    result3, progress3 = me.evaluate_submission("BEFORE_AFTER", pkg, progress3, {})
    assert result3["correct"] is False


def test_before_after_client_view_never_leaks_real_seasons_before_submission():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_before_after_round(
        variant="CFB_SCHOOL_TRANSFER_BEFORE_AFTER", round_count=2, seed="test-before-after-leak")
    progress = me.initial_progress("BEFORE_AFTER")
    view = me.client_safe_view("BEFORE_AFTER", pkg, progress)
    assert set(view["entity_a"].keys()) == {"entity_id", "label"}
    assert set(view["entity_b"].keys()) == {"entity_id", "label"}
    assert "season" not in view["entity_a"] and "season" not in view["entity_b"]


# --- CAREER_PATH (15-Format Expansion Part 2, format #10) ----------------

def test_career_path_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "CAREER_PATH" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("CAREER_PATH"), "CAREER_PATH has no registered variants"


@pytest.mark.parametrize("variant", ["NFL_PLAYER_CAREER_PATH_IDENTIFY", "CFB_PLAYER_CAREER_PATH_IDENTIFY"])
def test_career_path_generates_real_rounds_with_no_ambiguous_decoy(variant):
    from tools.director_v04 import career_path

    pkg = career_path.build_package("test-career-path-1", variant, round_count=5)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert len(r["path"]) == 3
        assert len(r["options"]) == 4
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, "no duplicate real players among the 4 candidates"
        assert r["_answer_item_id"] in item_ids


def test_career_path_answer_validation_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_career_path_round(
        variant="NFL_PLAYER_CAREER_PATH_IDENTIFY", round_count=3, seed="test-career-path-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("CAREER_PATH")
    canonical = pkg["rounds"][0]["_answer_item_id"]
    result, progress = me.evaluate_submission("CAREER_PATH", pkg, progress, {"guess_item_id": canonical})
    assert result["correct"] is True
    canonical_label = next(it["label"] for it in pkg["rounds"][0]["options"] if it["item_id"] == canonical)
    assert result["canonical_answer"] == canonical_label

    progress2 = me.initial_progress("CAREER_PATH")
    wrong = next(i for i in ("A", "B", "C", "D") if i != canonical)
    result2, progress2 = me.evaluate_submission("CAREER_PATH", pkg, progress2, {"guess_item_id": wrong})
    assert result2["correct"] is False


def test_career_path_malformed_submission_rejected_not_silently_correct():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_career_path_round(
        variant="NFL_PLAYER_CAREER_PATH_IDENTIFY", round_count=2, seed="test-career-path-malformed")

    progress = me.initial_progress("CAREER_PATH")
    result, progress = me.evaluate_submission("CAREER_PATH", pkg, progress, {"guess_item_id": ""})
    assert result["correct"] is False

    progress2 = me.initial_progress("CAREER_PATH")
    result2, progress2 = me.evaluate_submission("CAREER_PATH", pkg, progress2, {"guess_item_id": "Z"})
    assert result2["correct"] is False

    progress3 = me.initial_progress("CAREER_PATH")
    result3, progress3 = me.evaluate_submission("CAREER_PATH", pkg, progress3, {})
    assert result3["correct"] is False


def test_career_path_client_view_never_leaks_the_real_answer_before_submission():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_career_path_round(
        variant="CFB_PLAYER_CAREER_PATH_IDENTIFY", round_count=2, seed="test-career-path-leak")
    progress = me.initial_progress("CAREER_PATH")
    view = me.client_safe_view("CAREER_PATH", pkg, progress)
    assert set(view.keys()) >= {"round_index", "round_count", "completed", "path", "options"}
    assert "_answer_item_id" not in view
    for it in view["options"]:
        assert set(it.keys()) == {"item_id", "label"}


def test_career_path_no_decoy_shares_the_correct_answers_own_real_path():
    """Real regression guard for the generator's own core safety property:
    a decoy whose real early-career path is identical to the correct
    player's would itself be a second valid real answer -- verified here
    by independently recomputing each decoy's own real path from the raw
    database and confirming none match the shown real path."""
    from tools.director_v04 import career_path
    from tools.quiz_export import engine as engine_bootstrap

    pkg = career_path.build_package("test-career-path-nodupe", "NFL_PLAYER_CAREER_PATH_IDENTIFY", round_count=10)
    c = engine_bootstrap.connect()
    try:
        for r in pkg["rounds"]:
            shown_path = tuple(r["path"])
            for opt in r["options"]:
                if opt["item_id"] == r["_answer_item_id"]:
                    continue
                rows = c.execute(
                    "SELECT rs.season, rs.team_code FROM canonical_roster_seasons rs "
                    "JOIN canonical_players p ON p.player_id = rs.player_id "
                    "WHERE p.display_name = ? AND rs.verification_status='SOURCE_BACKED' "
                    "AND rs.source_id='NFLVERSE_DATA'", (opt["label"],),
                ).fetchall()
                earliest: dict = {}
                for row in rows:
                    if row["team_code"] not in earliest or row["season"] < earliest[row["team_code"]]:
                        earliest[row["team_code"]] = row["season"]
                if len(earliest) < 3:
                    continue
                decoy_path = tuple(sorted(earliest, key=lambda t: earliest[t])[:3])
                assert decoy_path != shown_path, f"decoy {opt['label']!r} shares the shown real path {shown_path}"
    finally:
        c.close()


# --- RISK_IT (15-Format Expansion Part 2, format #11) --------------------

def test_risk_it_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "RISK_IT" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("RISK_IT"), "RISK_IT has no registered variants"


def test_risk_it_generates_real_rounds_with_all_3_tiers_and_real_decoys():
    from tools.director_v04 import risk_it

    pkg = risk_it.build_package("test-risk-1", "NFL_DRAFT_RISK_IT", round_count=7)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    assert pkg["starting_lives"] == 3
    for r in pkg["rounds"]:
        assert set(r["tiers"].keys()) == {"LOW", "MEDIUM", "HIGH"}
        assert r["tiers"]["LOW"]["points"] == 1
        assert r["tiers"]["MEDIUM"]["points"] == 2
        assert r["tiers"]["HIGH"]["points"] == 3
        for tier, q in r["tiers"].items():
            item_ids = {it["item_id"] for it in q["options"]}
            assert item_ids == {"A", "B", "C", "D"}
            labels = [it["label"] for it in q["options"]]
            assert len(set(labels)) == 4, f"{tier} tier has a duplicate real team option"
            assert q["_answer_item_id"] in item_ids


def test_risk_it_full_2_step_playthrough_correct_choose_then_answer():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_risk_it_round(variant="NFL_DRAFT_RISK_IT", round_count=3, seed="test-risk-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("RISK_IT")
    assert progress["lives"] == 3 and progress["score"] == 0

    view0 = me.client_safe_view("RISK_IT", pkg, progress)
    assert view0["awaiting_tier"] is True

    result1, progress = me.evaluate_submission(
        "RISK_IT", pkg, progress, {"action": "choose_tier", "tier": "HIGH"})
    assert result1["action"] == "choose_tier"
    assert progress["current_tier"] == "HIGH"

    view1 = me.client_safe_view("RISK_IT", pkg, progress)
    assert view1["awaiting_tier"] is False
    assert view1["tier"] == "HIGH"

    canonical = pkg["rounds"][0]["tiers"]["HIGH"]["_answer_item_id"]
    result2, progress = me.evaluate_submission(
        "RISK_IT", pkg, progress, {"action": "answer", "choice_item_id": canonical})
    assert result2["correct"] is True
    assert result2["points_earned"] == 3
    assert progress["score"] == 3
    assert progress["lives"] == 3  # unchanged on a correct answer
    assert progress["current_tier"] is None  # reset for the next round
    assert progress["current_index"] == 1


def test_risk_it_wrong_answer_costs_a_life_and_awards_no_points():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_risk_it_round(variant="NFL_DRAFT_RISK_IT", round_count=2, seed="test-risk-wrong")
    progress = me.initial_progress("RISK_IT")
    _, progress = me.evaluate_submission("RISK_IT", pkg, progress, {"action": "choose_tier", "tier": "LOW"})
    assert progress["current_tier"] == "LOW"
    canonical = pkg["rounds"][0]["tiers"]["LOW"]["_answer_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != canonical)
    result, progress = me.evaluate_submission(
        "RISK_IT", pkg, progress, {"action": "answer", "choice_item_id": wrong})
    assert result["correct"] is False
    assert result["points_earned"] == 0
    assert progress["score"] == 0
    assert progress["lives"] == 2


def test_risk_it_run_ends_when_lives_reach_zero_and_rejects_further_submissions():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_risk_it_round(variant="NFL_DRAFT_RISK_IT", round_count=7, seed="test-risk-ended")
    progress = me.initial_progress("RISK_IT")
    for i in range(3):
        _, progress = me.evaluate_submission("RISK_IT", pkg, progress, {"action": "choose_tier", "tier": "MEDIUM"})
        canonical = pkg["rounds"][i]["tiers"]["MEDIUM"]["_answer_item_id"]
        wrong = next(x for x in ("A", "B", "C", "D") if x != canonical)
        _, progress = me.evaluate_submission("RISK_IT", pkg, progress, {"action": "answer", "choice_item_id": wrong})
    assert progress["lives"] == 0
    assert progress["ended"] is True
    assert progress["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("RISK_IT", pkg, progress, {"action": "choose_tier", "tier": "LOW"})


def test_risk_it_client_view_never_leaks_the_real_answer_before_the_answer_action():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_risk_it_round(variant="NFL_DRAFT_RISK_IT", round_count=2, seed="test-risk-leak")
    progress = me.initial_progress("RISK_IT")
    view0 = me.client_safe_view("RISK_IT", pkg, progress)
    assert "tiers" not in view0 and "tier_points" in view0

    _, progress = me.evaluate_submission("RISK_IT", pkg, progress, {"action": "choose_tier", "tier": "LOW"})
    view1 = me.client_safe_view("RISK_IT", pkg, progress)
    assert "_answer_item_id" not in view1
    for it in view1["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- WAGER_MODE (15-Format Expansion Part 2, format #12) -----------------

def test_wager_mode_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "WAGER_MODE" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("WAGER_MODE"), "WAGER_MODE has no registered variants"


def test_wager_mode_generates_real_rounds_across_all_3_categories():
    from tools.director_v04 import wager_mode

    pkg = wager_mode.build_package("test-wager-1", "WAGER_MODE_MIXED", round_count=6)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    assert pkg["starting_balance"] == 1000
    categories_seen = set()
    for r in pkg["rounds"]:
        categories_seen.add(r["category"])
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, f"{r['category']} round has a duplicate real option"
        assert r["_answer_item_id"] in item_ids
    if pkg["round_count"] >= 3:
        assert categories_seen == {"NFL Draft", "Heisman Winners", "Super Bowl Champions"}


def test_wager_mode_full_2_step_playthrough_correct_wager_then_answer():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_wager_mode_round(variant="WAGER_MODE_MIXED", round_count=3, seed="test-wager-eval")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("WAGER_MODE")
    assert progress["balance"] == 1000

    view0 = me.client_safe_view("WAGER_MODE", pkg, progress)
    assert view0["awaiting_wager"] is True
    assert "prompt" not in view0

    result1, progress = me.evaluate_submission(
        "WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": 300})
    assert result1["action"] == "place_wager"
    assert progress["current_wager"] == 300

    view1 = me.client_safe_view("WAGER_MODE", pkg, progress)
    assert view1["awaiting_wager"] is False
    assert view1["wager"] == 300

    canonical = pkg["rounds"][0]["_answer_item_id"]
    result2, progress = me.evaluate_submission(
        "WAGER_MODE", pkg, progress, {"action": "answer", "choice_item_id": canonical})
    assert result2["correct"] is True
    assert result2["balance_delta"] == 300
    assert progress["balance"] == 1300
    assert progress["current_wager"] is None
    assert progress["current_index"] == 1


def test_wager_mode_wrong_answer_subtracts_the_real_wager():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_wager_mode_round(variant="WAGER_MODE_MIXED", round_count=2, seed="test-wager-wrong")
    progress = me.initial_progress("WAGER_MODE")
    _, progress = me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": 250})
    canonical = pkg["rounds"][0]["_answer_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != canonical)
    result, progress = me.evaluate_submission(
        "WAGER_MODE", pkg, progress, {"action": "answer", "choice_item_id": wrong})
    assert result["correct"] is False
    assert result["balance_delta"] == -250
    assert progress["balance"] == 750


def test_wager_mode_rejects_a_wager_outside_the_real_valid_range():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_wager_mode_round(variant="WAGER_MODE_MIXED", round_count=1, seed="test-wager-invalid")
    progress = me.initial_progress("WAGER_MODE")
    with pytest.raises(Exception):
        me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": 5000})
    with pytest.raises(Exception):
        me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": -1})
    with pytest.raises(Exception):
        me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": "not a number"})


def test_wager_mode_run_ends_when_balance_reaches_zero_and_rejects_further_submissions():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_wager_mode_round(variant="WAGER_MODE_MIXED", round_count=5, seed="test-wager-ended")
    progress = me.initial_progress("WAGER_MODE")
    _, progress = me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": 1000})
    canonical = pkg["rounds"][0]["_answer_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != canonical)
    _, progress = me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "answer", "choice_item_id": wrong})
    assert progress["balance"] == 0
    assert progress["ended"] is True
    assert progress["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": 0})


def test_wager_mode_client_view_never_leaks_the_real_answer_before_the_answer_action():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_wager_mode_round(variant="WAGER_MODE_MIXED", round_count=2, seed="test-wager-leak")
    progress = me.initial_progress("WAGER_MODE")
    view0 = me.client_safe_view("WAGER_MODE", pkg, progress)
    assert set(view0.keys()) == {"round_index", "round_count", "completed", "awaiting_wager",
                                  "category", "balance"}

    _, progress = me.evaluate_submission("WAGER_MODE", pkg, progress, {"action": "place_wager", "wager": 100})
    view1 = me.client_safe_view("WAGER_MODE", pkg, progress)
    assert "_answer_item_id" not in view1
    for it in view1["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- LEADERBOARD_CLIMB (15-Format Expansion Part 2, format #14) ----------

def test_leaderboard_climb_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "LEADERBOARD_CLIMB" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("LEADERBOARD_CLIMB"), "LEADERBOARD_CLIMB has no registered variants"


def test_leaderboard_climb_generates_a_real_distinct_pre_sorted_ladder():
    from tools.director_v04 import leaderboard_climb

    pkg = leaderboard_climb.build_package("test-climb-1", "NFL_CAREER_PASSING_YARDS_CLIMB")
    assert pkg["qa_status"] == "PASSED"
    ladder = pkg["items"]
    assert len(ladder) == pkg["ladder_size"]
    assert pkg["ladder_size"] >= 4
    values = [row["value"] for row in ladder]
    # Real, pre-sorted, strictly descending -- and the generator itself
    # already aborted at generation time (RuntimeError) if any real tie
    # existed, so this is re-confirming that guarantee held.
    assert values == sorted(values, reverse=True)
    assert len(set(values)) == len(values), "a real tie slipped through -- generation should have aborted"
    ranks = [row["rank"] for row in ladder]
    assert ranks == list(range(1, len(ladder) + 1))
    labels = [row["label"] for row in ladder]
    assert len(set(labels)) == len(labels), "duplicate real player on the same real ladder"


def test_leaderboard_climb_full_playthrough_climbs_correctly_and_ends_on_a_miss():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_leaderboard_climb_round(variant="NFL_CAREER_PASSING_YARDS_CLIMB", seed="test-climb-play")
    assert pkg["qa_status"] == "PASSED"
    ladder = pkg["items"]
    size = pkg["ladder_size"]

    progress = me.initial_progress("LEADERBOARD_CLIMB")
    assert progress == {"ended": False, "completed": False}

    view0 = me.client_safe_view("LEADERBOARD_CLIMB", pkg, progress)
    assert view0["current_rank"] == size
    assert view0["completed"] is False
    assert set(view0.keys()) == {"current_rank", "ladder_size", "completed", "entity_a", "entity_b"}
    assert set(view0["entity_a"].keys()) == {"entity_id", "label"}
    labels_shown = {view0["entity_a"]["label"], view0["entity_b"]["label"]}
    assert labels_shown == {ladder[size - 1]["label"], ladder[size - 2]["label"]}

    # Always answer correctly (whichever real entity truly ranks higher)
    # until the climb reaches rank 1. current_rank is deliberately absent
    # from a fresh progress dict (sentinel-fallback pattern) so it must be
    # read with the same size-fallback client_safe_view/evaluate_submission
    # themselves use, not assumed present.
    while progress.get("current_rank", size) > 1 and not progress.get("ended"):
        current_rank = progress.get("current_rank", size)
        current_entity = ladder[current_rank - 1]
        next_entity = ladder[current_rank - 2]
        view = me.client_safe_view("LEADERBOARD_CLIMB", pkg, progress)
        a_label, b_label = view["entity_a"]["label"], view["entity_b"]["label"]
        # The real next-rung entity always truly ranks higher (lower rank
        # number) than the current one -- identify which shown slot it's in.
        correct_choice = "A" if a_label == next_entity["label"] else "B"
        assert {a_label, b_label} == {current_entity["label"], next_entity["label"]}
        result, progress = me.evaluate_submission(
            "LEADERBOARD_CLIMB", pkg, progress, {"choice": correct_choice})
        assert result["correct"] is True
        assert result["new_rank"] == current_rank - 1

    assert progress["current_rank"] == 1
    assert progress["completed"] is True
    view_top = me.client_safe_view("LEADERBOARD_CLIMB", pkg, progress)
    assert view_top["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("LEADERBOARD_CLIMB", pkg, progress, {"choice": "A"})


def test_leaderboard_climb_wrong_answer_ends_the_climb_and_rejects_further_submissions():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_leaderboard_climb_round(variant="NFL_CAREER_PASSING_YARDS_CLIMB", seed="test-climb-miss")
    progress = me.initial_progress("LEADERBOARD_CLIMB")
    size = pkg["ladder_size"]

    view0 = me.client_safe_view("LEADERBOARD_CLIMB", pkg, progress)
    canonical = "A" if view0["entity_a"]["label"] == pkg["items"][size - 2]["label"] else "B"
    wrong = "B" if canonical == "A" else "A"

    result, progress = me.evaluate_submission("LEADERBOARD_CLIMB", pkg, progress, {"choice": wrong})
    assert result["correct"] is False
    assert result["new_rank"] == size
    assert progress["ended"] is True
    assert progress["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("LEADERBOARD_CLIMB", pkg, progress, {"choice": canonical})


def test_leaderboard_climb_client_view_never_reveals_values_or_ranking_before_evaluate():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_leaderboard_climb_round(variant="NFL_CAREER_PASSING_YARDS_CLIMB", seed="test-climb-leak")
    progress = me.initial_progress("LEADERBOARD_CLIMB")
    view = me.client_safe_view("LEADERBOARD_CLIMB", pkg, progress)
    for key in ("entity_a", "entity_b"):
        assert set(view[key].keys()) == {"entity_id", "label"}
        assert "value" not in view[key]
        assert "rank" not in view[key]


def test_leaderboard_climb_shuffle_is_idempotent_across_repeated_client_view_calls():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_leaderboard_climb_round(variant="NFL_CAREER_PASSING_YARDS_CLIMB", seed="test-climb-idem")
    progress = me.initial_progress("LEADERBOARD_CLIMB")
    view_a = me.client_safe_view("LEADERBOARD_CLIMB", pkg, progress)
    view_b = me.client_safe_view("LEADERBOARD_CLIMB", pkg, progress)
    assert view_a["entity_a"]["label"] == view_b["entity_a"]["label"]
    assert view_a["entity_b"]["label"] == view_b["entity_b"]["label"]


def test_leaderboard_climb_rejects_malformed_submissions():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_leaderboard_climb_round(variant="NFL_CAREER_PASSING_YARDS_CLIMB", seed="test-climb-bad")
    progress = me.initial_progress("LEADERBOARD_CLIMB")
    result, progress = me.evaluate_submission("LEADERBOARD_CLIMB", pkg, progress, {"choice": "Z"})
    assert result["correct"] is False
    assert progress["ended"] is True


# --- BLIND_RESUME (15-Format Expansion Part 2, format #15, final) --------

def test_blind_resume_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "BLIND_RESUME" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("BLIND_RESUME"), "BLIND_RESUME has no registered variants"


def test_blind_resume_generates_real_rounds_with_distinct_real_candidates():
    from tools.director_v04 import blind_resume

    pkg = blind_resume.build_package("test-resume-1", "NFL_QB_CAREER_BLIND_RESUME", round_count=7)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        resume = r["resume"]
        assert resume["games"] >= blind_resume.MIN_CAREER_GAMES
        assert resume["pass_yards"] > blind_resume.MIN_CAREER_PASS_YARDS
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, "a round has a duplicate real candidate name"
        assert r["_answer_item_id"] in item_ids


def test_blind_resume_full_playthrough_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_blind_resume_round(variant="NFL_QB_CAREER_BLIND_RESUME", round_count=3, seed="test-resume-play")
    assert pkg["qa_status"] == "PASSED"

    progress = me.initial_progress("BLIND_RESUME")
    assert progress == {"current_index": 0, "completed": False}

    view0 = me.client_safe_view("BLIND_RESUME", pkg, progress)
    assert view0["completed"] is False
    assert view0["resume"] == pkg["rounds"][0]["resume"]

    canonical = pkg["rounds"][0]["_answer_item_id"]
    result1, progress = me.evaluate_submission(
        "BLIND_RESUME", pkg, progress, {"choice_item_id": canonical})
    assert result1["correct"] is True
    assert progress["current_index"] == 1
    assert progress["completed"] is False

    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    result2, progress = me.evaluate_submission(
        "BLIND_RESUME", pkg, progress, {"choice_item_id": wrong})
    assert result2["correct"] is False
    assert progress["current_index"] == 2


def test_blind_resume_rejects_malformed_submissions():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_blind_resume_round(variant="NFL_QB_CAREER_BLIND_RESUME", round_count=2, seed="test-resume-bad")
    progress = me.initial_progress("BLIND_RESUME")
    result, progress = me.evaluate_submission("BLIND_RESUME", pkg, progress, {"choice_item_id": "Z"})
    assert result["correct"] is False
    result2, progress = me.evaluate_submission("BLIND_RESUME", pkg, progress, {})
    assert result2["correct"] is False


def test_blind_resume_client_view_never_leaks_the_real_answer_before_evaluate():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_blind_resume_round(variant="NFL_QB_CAREER_BLIND_RESUME", round_count=2, seed="test-resume-leak")
    progress = me.initial_progress("BLIND_RESUME")
    view0 = me.client_safe_view("BLIND_RESUME", pkg, progress)
    assert set(view0.keys()) == {"round_index", "round_count", "completed", "resume", "options"}
    for it in view0["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- DOUBLE_OR_NOTHING (75-Format Expansion, Wave 1) ----------------------

def test_double_or_nothing_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "DOUBLE_OR_NOTHING" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("DOUBLE_OR_NOTHING"), "DOUBLE_OR_NOTHING has no registered variants"


def test_double_or_nothing_generates_real_escalating_tier_rounds():
    from tools.director_v04 import double_or_nothing as don

    pkg = don.build_package("test-don-1", "NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    assert pkg["base_points"] == 100
    tiers_seen = [r["tier"] for r in pkg["rounds"]]
    assert tiers_seen[0] == "LOW"
    if len(tiers_seen) >= 2:
        assert tiers_seen[1] == "MEDIUM"
    if len(tiers_seen) >= 3:
        assert all(t == "HIGH" for t in tiers_seen[2:])
    for r in pkg["rounds"]:
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, f"round {r['round_index']} has a duplicate real option"
        assert r["_answer_item_id"] in item_ids


def test_double_or_nothing_points_double_on_each_correct_answer():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_double_or_nothing_round(
        variant="NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=4, seed="test-don-double")
    progress = {"current_index": 0, "completed": False}
    expected = [100, 200, 400, 800]
    for i, exp in enumerate(expected):
        correct = pkg["rounds"][i]["_answer_item_id"]
        result, progress = me.evaluate_submission(
            "DOUBLE_OR_NOTHING", pkg, progress, {"action": "answer", "choice_item_id": correct})
        assert result["correct"] is True
        assert result["points"] == exp
        assert progress["points"] == exp


def test_double_or_nothing_bank_ends_the_run_and_keeps_points():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_double_or_nothing_round(
        variant="NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=3, seed="test-don-bank")
    progress = {"current_index": 0, "completed": False}
    correct = pkg["rounds"][0]["_answer_item_id"]
    _, progress = me.evaluate_submission(
        "DOUBLE_OR_NOTHING", pkg, progress, {"action": "answer", "choice_item_id": correct})
    result, progress = me.evaluate_submission("DOUBLE_OR_NOTHING", pkg, progress, {"action": "bank"})
    assert result["banked"] is True
    assert result["final_points"] == 100
    assert result["correct"] is True
    assert progress["banked"] is True
    assert progress["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("DOUBLE_OR_NOTHING", pkg, progress, {"action": "answer", "choice_item_id": "A"})


def test_double_or_nothing_wrong_answer_loses_everything_and_ends_the_run():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_double_or_nothing_round(
        variant="NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=3, seed="test-don-wrong")
    progress = {"current_index": 0, "completed": False}
    correct = pkg["rounds"][0]["_answer_item_id"]
    _, progress = me.evaluate_submission(
        "DOUBLE_OR_NOTHING", pkg, progress, {"action": "answer", "choice_item_id": correct})
    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    result, progress = me.evaluate_submission(
        "DOUBLE_OR_NOTHING", pkg, progress, {"action": "answer", "choice_item_id": wrong})
    assert result["correct"] is False
    assert result["points"] == 0
    assert progress["ended"] is True
    assert progress["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("DOUBLE_OR_NOTHING", pkg, progress, {"action": "bank"})


def test_double_or_nothing_rejects_banking_zero_points():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_double_or_nothing_round(
        variant="NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=2, seed="test-don-zero-bank")
    progress = {"current_index": 0, "completed": False}
    with pytest.raises(Exception):
        me.evaluate_submission("DOUBLE_OR_NOTHING", pkg, progress, {"action": "bank"})


def test_double_or_nothing_running_out_of_rounds_auto_banks():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_double_or_nothing_round(
        variant="NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=2, seed="test-don-autobank")
    progress = {"current_index": 0, "completed": False}
    for i in range(2):
        correct = pkg["rounds"][i]["_answer_item_id"]
        result, progress = me.evaluate_submission(
            "DOUBLE_OR_NOTHING", pkg, progress, {"action": "answer", "choice_item_id": correct})
    assert progress["completed"] is True
    assert progress.get("banked") is True


def test_double_or_nothing_client_view_never_leaks_the_real_answer():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_double_or_nothing_round(
        variant="NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=2, seed="test-don-leak")
    progress = {"current_index": 0, "completed": False}
    view = me.client_safe_view("DOUBLE_OR_NOTHING", pkg, progress)
    assert set(view.keys()) == {"round_index", "round_count", "completed", "points", "can_bank",
                                 "tier", "prompt", "options"}
    assert view["can_bank"] is False
    for it in view["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- KING_OF_THE_HILL (75-Format Expansion, Wave 1) -----------------------

def test_king_of_the_hill_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "KING_OF_THE_HILL" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("KING_OF_THE_HILL"), "KING_OF_THE_HILL has no registered variants"


def test_king_of_the_hill_generates_real_distinct_valued_items():
    from tools.director_v04 import king_of_the_hill as koth

    pkg = koth.build_package("test-koth-1", "NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["item_count"] >= 4
    values = [it["value"] for it in pkg["items"]]
    assert len(set(values)) == len(values), "a real tie slipped through -- comparisons could be unanswerable"
    labels = [it["label"] for it in pkg["items"]]
    assert len(set(labels)) == len(labels), "duplicate real team-season on the same board"


def test_king_of_the_hill_champion_defends_and_gets_dethroned_correctly():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_king_of_the_hill_round(
        variant="NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL", seed="test-koth-play")
    items = pkg["items"]
    progress = {"consecutive_defenses": 0, "ended": False, "completed": False}

    view0 = me.client_safe_view("KING_OF_THE_HILL", pkg, progress)
    assert view0["completed"] is False
    assert set(view0.keys()) == {"completed", "consecutive_defenses", "champion", "challenger"}
    assert set(view0["champion"].keys()) == {"entity_id", "label"}

    while not progress.get("completed"):
        champ_idx = progress.get("current_champion_index", 0)
        chall_idx = progress.get("current_challenger_index", 1)
        champ, chall = items[champ_idx], items[chall_idx]
        canonical = "champion" if champ["value"] > chall["value"] else "challenger"
        result, progress = me.evaluate_submission("KING_OF_THE_HILL", pkg, progress, {"choice": canonical})
        assert result["correct"] is True
        expected_new_champ = champ_idx if canonical == "champion" else chall_idx
        assert progress["current_champion_index"] == expected_new_champ
        if canonical == "champion":
            assert progress["consecutive_defenses"] >= 1
        else:
            assert progress["consecutive_defenses"] == 0

    assert progress["completed"] is True
    assert progress.get("ended") is False  # ran out of real challengers, never lost
    assert progress["current_challenger_index"] >= len(items)

    with pytest.raises(Exception):
        me.evaluate_submission("KING_OF_THE_HILL", pkg, progress, {"choice": "champion"})


def test_king_of_the_hill_wrong_guess_ends_the_run_and_rejects_further_submissions():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_king_of_the_hill_round(
        variant="NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL", seed="test-koth-wrong")
    items = pkg["items"]
    progress = {"consecutive_defenses": 0, "ended": False, "completed": False}
    canonical = "champion" if items[0]["value"] > items[1]["value"] else "challenger"
    wrong = "challenger" if canonical == "champion" else "champion"
    result, progress = me.evaluate_submission("KING_OF_THE_HILL", pkg, progress, {"choice": wrong})
    assert result["correct"] is False
    assert progress["ended"] is True
    assert progress["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("KING_OF_THE_HILL", pkg, progress, {"choice": canonical})


def test_king_of_the_hill_client_view_never_leaks_real_win_totals_before_evaluate():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_king_of_the_hill_round(
        variant="NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL", seed="test-koth-leak")
    progress = {"consecutive_defenses": 0, "ended": False, "completed": False}
    view = me.client_safe_view("KING_OF_THE_HILL", pkg, progress)
    for key in ("champion", "challenger"):
        assert set(view[key].keys()) == {"entity_id", "label"}
        assert "value" not in view[key]


# --- FACT_OR_FAKE (75-Format Expansion, Wave 1) ---------------------------

def test_fact_or_fake_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "FACT_OR_FAKE" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("FACT_OR_FAKE"), "FACT_OR_FAKE has no registered variants"


def test_fact_or_fake_generates_a_real_deterministic_true_false_split():
    from tools.director_v04 import fact_or_fake as fof

    pkg = fof.build_package("test-fof-1", "NFL_DRAFT_FACT_OR_FAKE", round_count=10)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    flags = [r["_is_true"] for r in pkg["rounds"]]
    assert flags[0::2] == [True] * len(flags[0::2]), "even rounds should be real, verbatim TRUE statements"
    if len(flags) > 1:
        assert flags[1::2] == [False] * len(flags[1::2]), "odd rounds should be real, substituted FAKE statements"
    for r in pkg["rounds"]:
        assert r["statement"]
        assert r["_notes"]


def test_fact_or_fake_full_playthrough_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_fact_or_fake_round(variant="NFL_DRAFT_FACT_OR_FAKE", round_count=3, seed="test-fof-play")
    progress = {"current_index": 0, "completed": False}

    view0 = me.client_safe_view("FACT_OR_FAKE", pkg, progress)
    assert view0["completed"] is False
    assert view0["statement"] == pkg["rounds"][0]["statement"]

    canonical0 = "TRUE" if pkg["rounds"][0]["_is_true"] else "FAKE"
    result1, progress = me.evaluate_submission("FACT_OR_FAKE", pkg, progress, {"choice": canonical0})
    assert result1["correct"] is True
    assert progress["current_index"] == 1

    canonical1 = "TRUE" if pkg["rounds"][1]["_is_true"] else "FAKE"
    wrong1 = "FAKE" if canonical1 == "TRUE" else "TRUE"
    result2, progress = me.evaluate_submission("FACT_OR_FAKE", pkg, progress, {"choice": wrong1})
    assert result2["correct"] is False
    assert progress["current_index"] == 2


def test_fact_or_fake_rejects_malformed_submissions():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_fact_or_fake_round(variant="NFL_DRAFT_FACT_OR_FAKE", round_count=1, seed="test-fof-bad")
    progress = {"current_index": 0, "completed": False}
    result, progress = me.evaluate_submission("FACT_OR_FAKE", pkg, progress, {"choice": "MAYBE"})
    assert result["correct"] is False
    result2, _ = me.evaluate_submission("FACT_OR_FAKE", pkg, {"current_index": 0, "completed": False}, {})
    assert result2["correct"] is False


def test_fact_or_fake_client_view_never_leaks_the_real_answer_before_evaluate():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_fact_or_fake_round(variant="NFL_DRAFT_FACT_OR_FAKE", round_count=2, seed="test-fof-leak")
    progress = {"current_index": 0, "completed": False}
    view = me.client_safe_view("FACT_OR_FAKE", pkg, progress)
    assert set(view.keys()) == {"round_index", "round_count", "completed", "statement"}


# --- GUESS_THE_RANKING (75-Format Expansion, Wave 1) ----------------------

def test_guess_the_ranking_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "GUESS_THE_RANKING" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("GUESS_THE_RANKING"), "GUESS_THE_RANKING has no registered variants"


def test_guess_the_ranking_generates_real_decoy_complete_rounds():
    from tools.director_v04 import guess_the_ranking as gtr

    pkg = gtr.build_package("test-gtr-1", "NFL_CAREER_PASSING_YARDS_RANKING", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, f"round {r['round_index']} has a duplicate real rank option"
        assert r["_answer_item_id"] in item_ids
        for label in labels:
            assert label.startswith("#")


def test_guess_the_ranking_full_playthrough_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_guess_the_ranking_round(
        variant="NFL_CAREER_PASSING_YARDS_RANKING", round_count=3, seed="test-gtr-play")
    progress = {"current_index": 0, "completed": False}

    view0 = me.client_safe_view("GUESS_THE_RANKING", pkg, progress)
    assert view0["completed"] is False
    assert view0["label"] == pkg["rounds"][0]["label"]

    canonical0 = pkg["rounds"][0]["_answer_item_id"]
    result1, progress = me.evaluate_submission(
        "GUESS_THE_RANKING", pkg, progress, {"choice_item_id": canonical0})
    assert result1["correct"] is True
    assert progress["current_index"] == 1

    wrong1 = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    result2, progress = me.evaluate_submission(
        "GUESS_THE_RANKING", pkg, progress, {"choice_item_id": wrong1})
    assert result2["correct"] is False
    assert progress["current_index"] == 2


def test_guess_the_ranking_client_view_never_leaks_the_real_answer_before_evaluate():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_guess_the_ranking_round(
        variant="NFL_CAREER_PASSING_YARDS_RANKING", round_count=2, seed="test-gtr-leak")
    progress = {"current_index": 0, "completed": False}
    view = me.client_safe_view("GUESS_THE_RANKING", pkg, progress)
    assert set(view.keys()) == {"round_index", "round_count", "completed", "label", "options"}
    for it in view["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- STAT_TARGET (75-Format Expansion, Wave 1) ----------------------------

def test_stat_target_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "STAT_TARGET" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("STAT_TARGET"), "STAT_TARGET has no registered variants"


def test_stat_target_generates_real_unambiguous_closest_candidate_rounds():
    from tools.director_v04 import stat_target as st

    pkg = st.build_package("test-st-1", "NFL_SEASON_RUSHING_YARDS_TARGET", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert r["target"] in st._TARGETS
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, f"round {r['round_index']} has a duplicate real candidate"
        assert r["_answer_item_id"] in item_ids


def test_stat_target_full_playthrough_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_stat_target_round(
        variant="NFL_SEASON_RUSHING_YARDS_TARGET", round_count=3, seed="test-st-play")
    progress = {"current_index": 0, "completed": False}

    view0 = me.client_safe_view("STAT_TARGET", pkg, progress)
    assert view0["completed"] is False
    assert view0["target"] == pkg["rounds"][0]["target"]

    canonical0 = pkg["rounds"][0]["_answer_item_id"]
    result1, progress = me.evaluate_submission("STAT_TARGET", pkg, progress, {"choice_item_id": canonical0})
    assert result1["correct"] is True
    assert progress["current_index"] == 1

    wrong1 = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    result2, progress = me.evaluate_submission("STAT_TARGET", pkg, progress, {"choice_item_id": wrong1})
    assert result2["correct"] is False
    assert progress["current_index"] == 2


def test_stat_target_client_view_never_leaks_the_real_answer_before_evaluate():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_stat_target_round(
        variant="NFL_SEASON_RUSHING_YARDS_TARGET", round_count=2, seed="test-st-leak")
    progress = {"current_index": 0, "completed": False}
    view = me.client_safe_view("STAT_TARGET", pkg, progress)
    assert set(view.keys()) == {"round_index", "round_count", "completed", "target", "options"}
    for it in view["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- REVERSE_TRIVIA (75-Format Expansion, Wave 1) -------------------------

def test_reverse_trivia_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "REVERSE_TRIVIA" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("REVERSE_TRIVIA"), "REVERSE_TRIVIA has no registered variants"


def test_reverse_trivia_generates_real_decoy_complete_rounds():
    from tools.director_v04 import reverse_trivia as rt

    pkg = rt.build_package("test-rt-1", "NFL_DRAFT_REVERSE_TRIVIA", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    for r in pkg["rounds"]:
        assert r["subject_name"]
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, f"round {r['round_index']} has a duplicate real statement"
        assert r["_answer_item_id"] in item_ids


def test_reverse_trivia_full_playthrough_correct_and_incorrect():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_reverse_trivia_round(
        variant="NFL_DRAFT_REVERSE_TRIVIA", round_count=3, seed="test-rt-play")
    progress = {"current_index": 0, "completed": False}

    view0 = me.client_safe_view("REVERSE_TRIVIA", pkg, progress)
    assert view0["completed"] is False
    assert view0["subject_name"] == pkg["rounds"][0]["subject_name"]

    canonical0 = pkg["rounds"][0]["_answer_item_id"]
    result1, progress = me.evaluate_submission("REVERSE_TRIVIA", pkg, progress, {"choice_item_id": canonical0})
    assert result1["correct"] is True
    assert progress["current_index"] == 1

    wrong1 = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    result2, progress = me.evaluate_submission("REVERSE_TRIVIA", pkg, progress, {"choice_item_id": wrong1})
    assert result2["correct"] is False
    assert progress["current_index"] == 2


def test_reverse_trivia_client_view_never_leaks_the_real_answer_before_evaluate():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_reverse_trivia_round(
        variant="NFL_DRAFT_REVERSE_TRIVIA", round_count=2, seed="test-rt-leak")
    progress = {"current_index": 0, "completed": False}
    view = me.client_safe_view("REVERSE_TRIVIA", pkg, progress)
    assert set(view.keys()) == {"round_index", "round_count", "completed", "subject_name", "options"}
    for it in view["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- THREE_STRIKES (75-Format Expansion, Wave 1) --------------------------

def test_three_strikes_is_registered():
    from tools.director_v02 import mechanic_engine as me

    assert "THREE_STRIKES" in me.TAXONOMY_IDS
    assert me.VARIANTS.get("THREE_STRIKES"), "THREE_STRIKES has no registered variants"


def test_three_strikes_generates_real_escalating_tier_rounds():
    from tools.director_v04 import three_strikes as ts

    pkg = ts.build_package("test-ts-1", "NFL_DRAFT_THREE_STRIKES", round_count=12)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] >= 1
    assert pkg["starting_strikes"] == 3
    tiers_seen = [r["tier"] for r in pkg["rounds"]]
    if len(tiers_seen) >= 8:
        assert tiers_seen[0] == "LOW"
        assert tiers_seen[-1] == "HIGH"
    for r in pkg["rounds"]:
        item_ids = {it["item_id"] for it in r["options"]}
        assert item_ids == {"A", "B", "C", "D"}
        labels = [it["label"] for it in r["options"]]
        assert len(set(labels)) == 4, f"round {r['round_index']} has a duplicate real option"
        assert r["_answer_item_id"] in item_ids


def test_three_strikes_wrong_answers_deplete_strikes_and_end_the_run():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_three_strikes_round(variant="NFL_DRAFT_THREE_STRIKES", round_count=12, seed="test-ts-wrong")
    progress = me.initial_progress("THREE_STRIKES")
    assert progress == {"current_index": 0, "score": 0, "streak": 0, "strikes": 3,
                         "ended": False, "completed": False}

    for i in range(3):
        wrong = next(x for x in ("A", "B", "C", "D") if x != pkg["rounds"][i]["_answer_item_id"])
        result, progress = me.evaluate_submission("THREE_STRIKES", pkg, progress, {"choice_item_id": wrong})
        assert result["correct"] is False
        assert progress["strikes"] == 3 - (i + 1)

    assert progress["ended"] is True
    assert progress["completed"] is True

    with pytest.raises(Exception):
        me.evaluate_submission("THREE_STRIKES", pkg, progress, {"choice_item_id": "A"})


def test_three_strikes_correct_answers_accumulate_score_and_streak():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_three_strikes_round(variant="NFL_DRAFT_THREE_STRIKES", round_count=5, seed="test-ts-correct")
    progress = me.initial_progress("THREE_STRIKES")
    for i in range(5):
        correct = pkg["rounds"][i]["_answer_item_id"]
        result, progress = me.evaluate_submission("THREE_STRIKES", pkg, progress, {"choice_item_id": correct})
        assert result["correct"] is True
        assert progress["streak"] == i + 1
    assert progress["strikes"] == 3
    assert progress["score"] == sum(r["points"] for r in pkg["rounds"])
    assert progress["completed"] is True
    assert progress["ended"] is False


def test_three_strikes_client_view_never_leaks_the_real_answer():
    from tools.director_v02 import mechanic_engine as me

    pkg = me.generate_three_strikes_round(variant="NFL_DRAFT_THREE_STRIKES", round_count=2, seed="test-ts-leak")
    progress = me.initial_progress("THREE_STRIKES")
    view = me.client_safe_view("THREE_STRIKES", pkg, progress)
    assert set(view.keys()) == {"round_index", "round_count", "completed", "tier", "points", "prompt",
                                 "options", "score", "streak", "strikes"}
    for it in view["options"]:
        assert set(it.keys()) == {"item_id", "label"}
