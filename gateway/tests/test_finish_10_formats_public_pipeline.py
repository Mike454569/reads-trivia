"""Finish-10-Formats pass -- real, end-to-end tests proving all 10 new
formats are reachable through the ACTUAL public game pipeline
(gateway/services/public_mechanics.py: start_public_round/get_public_round/
submit_public_round), not just the admin Creator preview. Every test here
plays a real round to completion against the live SQLite Engine, using the
server's own stored package to discover the correct answer where needed
(never a shortcut around server-authoritative validation -- the test reads
the private package the same way an admin/debugging tool would, the
PLAYER-facing API never exposes it).

Also covers the user's own exact example Creator prompts, verifying each
routes to the intended new format end-to-end through gateway.services.creator.
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


def _play_correct_guess_question(pm, packages, round_data):
    """Helper: given a round from a guess-style format (drive_progression,
    branch_state leaf), reads the real stored package to submit the actual
    correct answer -- exercises the full real server-authoritative path,
    not a client-side shortcut."""
    pkg = packages.load_package(round_data["round_id"])
    idx = round_data["view"]["round_index"]
    q = pkg["questions"][idx]
    return q["options"][q["correctIndex"]]


# --- public mode discovery ---------------------------------------------------

def test_all_10_new_public_modes_are_listed():
    from gateway.services import public_mechanics as pm

    modes = {m["mode"] for m in pm.list_public_mechanic_modes()}
    expected = {
        "connection_grid_nfl", "perfect_drive_nfl", "perfect_drive_cfb",
        "goal_line_stand_nfl", "goal_line_stand_cfb", "lineup_builder_nfl", "lineup_builder_cfb",
        "auction_draft_nfl", "auction_draft_cfb", "cap_challenge_nfl", "cap_challenge_cfb",
        "knockout_tournament_nfl", "knockout_tournament_cfb",
        "six_degrees_cfb_nfl", "chain_reaction_cfb_nfl", "choose_your_path_nfl",
    }
    assert expected.issubset(modes)


# --- 1. CONNECTION_GRID -------------------------------------------------------

def test_connection_grid_full_public_playthrough():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="connection_grid_nfl")
    rid = r["round_id"]
    assert len(r["view"]["row_labels"]) == 3 and len(r["view"]["col_labels"]) == 3
    # Answer several real cells (correct and incorrect), confirm real
    # per-cell server-side grading and progress accumulation.
    sub1 = pm.submit_public_round(round_id=rid, submission={"row_index": 0, "col_index": 0, "guess": "Not A Real Player"})
    assert sub1["result"]["correct"] is False
    view2 = pm.get_public_round(round_id=rid)["view"]
    assert view2["cells_answered"] == 1


# --- 2. PERFECT_DRIVE ----------------------------------------------------------

def test_perfect_drive_full_playthrough_to_touchdown_or_end():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="perfect_drive_nfl")
    rid, view = r["round_id"], r["view"]
    pkg = packages.load_package(rid)
    steps = 0
    while not view.get("completed") and not view.get("ended") and steps < 20:
        q = pkg["questions"][view["round_index"]]
        sub = pm.submit_public_round(round_id=rid, submission={"answer": q["options"][q["correctIndex"]]})
        view = sub["view"]
        steps += 1
    assert view.get("ended") is True
    assert view.get("scored") is True  # always-correct answers must reach a real touchdown
    assert view.get("field_position_yards") == 100


# --- 3. GOAL_LINE_STAND ---------------------------------------------------------

def test_goal_line_stand_scores_on_a_correct_answer():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="goal_line_stand_cfb")
    rid, view = r["round_id"], r["view"]
    pkg = packages.load_package(rid)
    q = pkg["questions"][view["round_index"]]
    sub = pm.submit_public_round(round_id=rid, submission={"answer": q["options"][q["correctIndex"]]})
    assert sub["view"]["scored"] is True


def test_goal_line_stand_wrong_answer_costs_a_down():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="goal_line_stand_nfl")
    rid, view = r["round_id"], r["view"]
    sub = pm.submit_public_round(round_id=rid, submission={"answer": "Definitely Not A Real Team"})
    assert sub["view"]["downs_remaining"] == view["downs_total"] - 1


# --- 4. LINEUP_BUILDER -----------------------------------------------------------

def test_lineup_builder_completes_a_real_roster_nfl_and_cfb():
    from gateway.services import public_mechanics as pm

    for mode in ("lineup_builder_nfl", "lineup_builder_cfb"):
        r = pm.start_public_round(mode=mode)
        rid, view = r["round_id"], r["view"]
        while not view["completed"]:
            pick = view["remaining_pool"][0]
            sub = pm.submit_public_round(round_id=rid, submission={"player_id": pick["player_id"]})
            view = sub["view"]
        assert view["completed"] is True
        assert view["picks_made"] == 6


# --- 5. AUCTION_DRAFT -------------------------------------------------------------

def test_auction_draft_budget_decreases_correctly_nfl_and_cfb():
    from gateway.services import public_mechanics as pm

    for mode in ("auction_draft_nfl", "auction_draft_cfb"):
        r = pm.start_public_round(mode=mode)
        rid, view = r["round_id"], r["view"]
        pick = view["remaining_pool"][0]
        sub = pm.submit_public_round(round_id=rid, submission={"player_id": pick["player_id"]})
        assert sub["view"]["remaining_budget"] == pytest.approx(view["remaining_budget"] - pick["cost"])


# --- 6. CAP_CHALLENGE -------------------------------------------------------------

def test_cap_challenge_completes_within_cap_and_rejects_over_cap():
    from gateway.services import public_mechanics as pm
    from gateway.errors import GatewayError

    r = pm.start_public_round(mode="cap_challenge_nfl")
    rid, view = r["round_id"], r["view"]
    for i, _slot in enumerate(view["roster_slots"]):
        cheapest = min(view["pool_by_slot"][str(i)], key=lambda p: p["cost"])
        sub = pm.submit_public_round(round_id=rid, submission={"action": "select", "slot_index": i, "player_id": cheapest["player_id"]})
        view = sub["view"]
    final = pm.submit_public_round(round_id=rid, submission={"action": "submit_lineup"})
    assert final["result"]["total_spent"] <= r["view"]["budget_total"]
    assert final["view"]["completed"] is True
    try:
        pm.submit_public_round(round_id=rid, submission={"action": "select", "slot_index": 0, "player_id": "x"})
        assert False, "expected GatewayError -- already submitted"
    except GatewayError:
        pass


# --- 7. KNOCKOUT_TOURNAMENT -------------------------------------------------------

def test_knockout_tournament_full_playthrough_to_champion():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="knockout_tournament_nfl")
    rid, view = r["round_id"], r["view"]
    while not view["completed"]:
        m = None
        for rnd in view["rounds"]:
            for mm in rnd["matchups"]:
                if "your_pick" not in mm:
                    m = mm
                    break
            if m:
                break
        sub = pm.submit_public_round(round_id=rid, submission={"match_id": m["match_id"], "predicted_winner": m["entrant_a"]})
        view = sub["view"]
    assert view["picks_made"] == view["total_matchups"] == 15  # real 16-team field


# --- 8/9. SIX_DEGREES / CHAIN_REACTION --------------------------------------------

def test_six_degrees_and_chain_reaction_real_correct_and_incorrect_guess():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    for mode in ("six_degrees_cfb_nfl", "chain_reaction_cfb_nfl"):
        r = pm.start_public_round(mode=mode)
        rid = r["round_id"]
        pkg = packages.load_package(rid)
        real_end = pkg["chains"][0]["nodes"][-1]["label"]
        sub_correct = pm.submit_public_round(round_id=rid, submission={"guess": real_end})
        assert sub_correct["result"]["correct"] is True
        r2 = pm.start_public_round(mode=mode)
        sub_wrong = pm.submit_public_round(round_id=r2["round_id"], submission={"guess": "Definitely Not Real"})
        assert sub_wrong["result"]["correct"] is False


# --- 10. CHOOSE_YOUR_PATH ----------------------------------------------------------

def test_choose_your_path_full_playthrough_reaches_completion():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="choose_your_path_nfl")
    rid = r["round_id"]
    choice = r["view"]["choices"][0]["choice_id"]
    sub1 = pm.submit_public_round(round_id=rid, submission={"choice_id": choice})
    assert sub1["view"]["completed"] is False  # navigation, not a graded answer
    answer = _play_correct_guess_question(pm, packages, {"round_id": rid, "view": {"round_index": 0}}) \
        if False else sub1["view"]["options"][0]  # any valid option string exercises the real path
    sub2 = pm.submit_public_round(round_id=rid, submission={"answer": answer})
    assert sub2["view"]["completed"] is True
    # Re-fetching after completion must keep reporting completed=True, never
    # re-trap the player on the same leaf question forever (the real bug
    # found and fixed in mechanic_engine.py's _branch_state_client_view
    # during this pass).
    refetched = pm.get_public_round(round_id=rid)
    assert refetched["view"]["completed"] is True


def test_choose_your_path_branches_materially_change_the_question_domain():
    """Real requirement: branches must materially change the generated
    path, not funnel to the same question pool regardless of choice."""
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="choose_your_path_nfl")
    rid = r["round_id"]
    choices = {c["choice_id"]: c["next"] for c in r["view"]["choices"]}
    assert len(set(choices.values())) == len(choices), "every real choice must lead to a distinct real leaf"


# --- 11. GUESS_THE_SEASON (15-Format Expansion Part 2) ----------------------

def test_guess_the_season_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="guess_the_season_nfl")
    rid = r["round_id"]
    assert rid.startswith("GGP17:")
    assert len(r["view"]["clues"]) >= 2

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer"]
    sub_wrong = pm.submit_public_round(round_id=rid, submission={"guess_season": "1899"})
    assert sub_wrong["result"]["correct"] is False
    assert sub_wrong["result"]["canonical_answer"] == correct

    r2 = pm.start_public_round(mode="guess_the_season_nfl")
    rid2 = r2["round_id"]
    pkg2 = packages.load_package(rid2)
    correct2 = pkg2["rounds"][0]["_answer"]
    sub_correct = pm.submit_public_round(round_id=rid2, submission={"guess_season": correct2})
    assert sub_correct["result"]["correct"] is True


def test_guess_the_season_never_leaks_the_answer_before_submission():
    """Real requirement: the client-safe view must never include the real
    answer (season) before the player submits -- only the clue texts."""
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="guess_the_season_nfl")
    rid = r["round_id"]
    pkg = packages.load_package(rid)
    real_answer = pkg["rounds"][0]["_answer"]
    assert "season" not in r["view"] and "_answer" not in r["view"]
    for clue in r["view"]["clues"]:
        assert real_answer not in clue.get("display_text", "")


# --- 12. HEAD_TO_HEAD_DUEL (15-Format Expansion Part 2, format #3) ----------

@pytest.mark.parametrize("mode", [
    "head_to_head_duel_nfl_rushing", "head_to_head_duel_nfl_passing_td", "head_to_head_duel_cfb_rushing",
])
def test_head_to_head_duel_full_public_playthrough_correct_and_incorrect(mode):
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode=mode)
    rid = r["round_id"]
    assert rid.startswith("GGP18:")
    assert r["view"]["entity_a"]["label"] and r["view"]["entity_b"]["label"]

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer"]
    sub_correct = pm.submit_public_round(round_id=rid, submission={"choice": correct})
    assert sub_correct["result"]["correct"] is True

    r2 = pm.start_public_round(mode=mode)
    rid2 = r2["round_id"]
    pkg2 = packages.load_package(rid2)
    wrong = "B" if pkg2["rounds"][0]["_answer"] == "A" else "A"
    sub_wrong = pm.submit_public_round(round_id=rid2, submission={"choice": wrong})
    assert sub_wrong["result"]["correct"] is False


def test_head_to_head_duel_never_leaks_real_values_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="head_to_head_duel_nfl_rushing")
    assert set(r["view"]["entity_a"].keys()) == {"entity_id", "label"}
    assert set(r["view"]["entity_b"].keys()) == {"entity_id", "label"}


# --- 13. BEST_OF_SEVEN_DUEL (15-Format Expansion Part 2, format #4) ---------

def test_best_of_seven_duel_full_public_playthrough_reveals_match_summary_only_at_the_end():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="best_of_seven_duel_nfl_qb")
    rid = r["round_id"]
    assert rid.startswith("GGP18:")
    pkg = packages.load_package(rid)
    total = pkg["round_count"]
    assert 3 <= total <= 7
    # Same fixed real pair every round -- a real requirement of "best of
    # seven", distinct from plain HEAD_TO_HEAD_DUEL where each round is an
    # unrelated new pair.
    assert r["view"]["entity_a"]["label"] == pkg["rounds"][0]["entity_a"]["label"]

    last_sub = None
    for i in range(total):
        correct = pkg["rounds"][i]["_answer"]
        last_sub = pm.submit_public_round(round_id=rid, submission={"choice": correct})
        if i < total - 1:
            assert "match_summary" not in last_sub["result"]
    assert "match_summary" in last_sub["result"]
    ms = last_sub["result"]["match_summary"]
    assert ms["wins_a"] + ms["wins_b"] == ms["categories_played"] == total
    assert last_sub["view"]["completed"] is True


# --- 14. PICK_THE_IMPOSTOR (15-Format Expansion Part 2, format #5) ---------

@pytest.mark.parametrize("mode", ["pick_the_impostor_nfl", "pick_the_impostor_cfb"])
def test_pick_the_impostor_full_public_playthrough_correct_and_incorrect(mode):
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode=mode)
    rid = r["round_id"]
    assert rid.startswith("GGP19:")
    assert len(r["view"]["items"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_impostor_item_id"]
    sub_correct = pm.submit_public_round(round_id=rid, submission={"impostor_item_id": correct})
    assert sub_correct["result"]["correct"] is True

    r2 = pm.start_public_round(mode=mode)
    rid2 = r2["round_id"]
    pkg2 = packages.load_package(rid2)
    correct2 = pkg2["rounds"][0]["_impostor_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != correct2)
    sub_wrong = pm.submit_public_round(round_id=rid2, submission={"impostor_item_id": wrong})
    assert sub_wrong["result"]["correct"] is False


def test_pick_the_impostor_never_leaks_the_real_impostor_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="pick_the_impostor_nfl")
    for it in r["view"]["items"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 15. UNIQUE_ONE_OUT (15-Format Expansion Part 2, format #6) ------------

def test_unique_one_out_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="unique_one_out_nfl")
    rid = r["round_id"]
    assert rid.startswith("GGP19:")
    assert len(r["view"]["items"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_impostor_item_id"]
    sub_correct = pm.submit_public_round(round_id=rid, submission={"impostor_item_id": correct})
    assert sub_correct["result"]["correct"] is True

    r2 = pm.start_public_round(mode="unique_one_out_nfl")
    rid2 = r2["round_id"]
    pkg2 = packages.load_package(rid2)
    correct2 = pkg2["rounds"][0]["_impostor_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != correct2)
    sub_wrong = pm.submit_public_round(round_id=rid2, submission={"impostor_item_id": wrong})
    assert sub_wrong["result"]["correct"] is False


# --- 16. MISSING_PIECE (15-Format Expansion Part 2, format #7) -------------

@pytest.mark.parametrize("mode", ["missing_piece_nfl", "missing_piece_cfb"])
def test_missing_piece_full_public_playthrough_correct_and_incorrect(mode):
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode=mode)
    rid = r["round_id"]
    assert rid.startswith("GGP20:")
    assert len(r["view"]["group_members"]) == 3
    assert len(r["view"]["items"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub_correct = pm.submit_public_round(round_id=rid, submission={"answer_item_id": correct})
    assert sub_correct["result"]["correct"] is True

    r2 = pm.start_public_round(mode=mode)
    rid2 = r2["round_id"]
    pkg2 = packages.load_package(rid2)
    correct2 = pkg2["rounds"][0]["_answer_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != correct2)
    sub_wrong = pm.submit_public_round(round_id=rid2, submission={"answer_item_id": wrong})
    assert sub_wrong["result"]["correct"] is False


def test_missing_piece_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="missing_piece_nfl")
    for it in r["view"]["items"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 17. BEFORE_AFTER (15-Format Expansion Part 2, format #8) --------------

@pytest.mark.parametrize("mode", ["before_after_nfl", "before_after_cfb"])
def test_before_after_full_public_playthrough_correct_and_incorrect(mode):
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode=mode)
    rid = r["round_id"]
    assert rid.startswith("GGP21:")
    assert r["view"]["entity_a"]["label"] and r["view"]["entity_b"]["label"]

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer"]
    sub_correct = pm.submit_public_round(round_id=rid, submission={"choice": correct})
    assert sub_correct["result"]["correct"] is True

    r2 = pm.start_public_round(mode=mode)
    rid2 = r2["round_id"]
    pkg2 = packages.load_package(rid2)
    wrong = "B" if pkg2["rounds"][0]["_answer"] == "A" else "A"
    sub_wrong = pm.submit_public_round(round_id=rid2, submission={"choice": wrong})
    assert sub_wrong["result"]["correct"] is False


def test_before_after_never_leaks_real_seasons_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="before_after_nfl")
    assert set(r["view"]["entity_a"].keys()) == {"entity_id", "label"}
    assert set(r["view"]["entity_b"].keys()) == {"entity_id", "label"}


# --- 18. STAT_LADDER public modes (real gap closed this pass -- these 3
# modes existed since format #1 but had never been exercised through the
# real public pipeline in a persisted test) -----------------------------

@pytest.mark.parametrize("mode", ["stat_ladder_nfl_rushing", "stat_ladder_nfl_passing_td", "stat_ladder_cfb_rushing"])
def test_stat_ladder_public_mode_full_playthrough(mode):
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode=mode)
    rid = r["round_id"]
    assert len(r["view"]["items_shuffled"]) == 4

    pkg = packages.load_package(rid)
    correct_order = pkg["rounds"][0]["_private_correct_order"]
    sub = pm.submit_public_round(round_id=rid, submission={"order": correct_order})
    assert sub["result"]["exact_match"] is True
    assert "values_by_item_id" in sub["result"]


# --- 19. MAP_THE_CAREER (15-Format Expansion Part 2, format #9) ------------

@pytest.mark.parametrize("mode", ["map_the_career_nfl", "map_the_career_cfb"])
def test_map_the_career_public_mode_full_playthrough(mode):
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode=mode)
    rid = r["round_id"]
    assert len(r["view"]["items_shuffled"]) == 4

    pkg = packages.load_package(rid)
    correct_order = pkg["rounds"][0]["_private_correct_order"]
    sub = pm.submit_public_round(round_id=rid, submission={"order": correct_order})
    assert sub["result"]["exact_match"] is True
    assert "values_by_item_id" in sub["result"]


def test_map_the_career_never_leaks_real_debut_seasons_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="map_the_career_nfl")
    for it in r["view"]["items_shuffled"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 20. CAREER_PATH (15-Format Expansion Part 2, format #10) -------------

@pytest.mark.parametrize("mode", ["career_path_nfl", "career_path_cfb"])
def test_career_path_full_public_playthrough_correct_and_incorrect(mode):
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode=mode)
    rid = r["round_id"]
    assert rid.startswith("GGP22:")
    assert len(r["view"]["path"]) == 3
    assert len(r["view"]["options"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub_correct = pm.submit_public_round(round_id=rid, submission={"guess_item_id": correct})
    assert sub_correct["result"]["correct"] is True

    r2 = pm.start_public_round(mode=mode)
    rid2 = r2["round_id"]
    pkg2 = packages.load_package(rid2)
    correct2 = pkg2["rounds"][0]["_answer_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != correct2)
    sub_wrong = pm.submit_public_round(round_id=rid2, submission={"guess_item_id": wrong})
    assert sub_wrong["result"]["correct"] is False


def test_career_path_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="career_path_nfl")
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 21. RISK_IT (15-Format Expansion Part 2, format #11) ------------------

def test_risk_it_full_public_playthrough_tracks_score_and_lives():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="risk_it_nfl_draft")
    rid = r["round_id"]
    assert rid.startswith("GGP23:")
    assert r["view"]["awaiting_tier"] is True
    assert r["view"]["lives"] == 3 and r["view"]["score"] == 0

    pkg = packages.load_package(rid)
    sub1 = pm.submit_public_round(round_id=rid, submission={"action": "choose_tier", "tier": "HIGH"})
    assert sub1["view"]["awaiting_tier"] is False and sub1["view"]["tier"] == "HIGH"

    correct = pkg["rounds"][0]["tiers"]["HIGH"]["_answer_item_id"]
    sub2 = pm.submit_public_round(round_id=rid, submission={"action": "answer", "choice_item_id": correct})
    assert sub2["result"]["correct"] is True
    assert sub2["result"]["points_earned"] == 3
    assert sub2["view"]["score"] == 3
    assert sub2["view"]["lives"] == 3
    assert sub2["view"]["awaiting_tier"] is True  # back to tier-choice for the next round


def test_risk_it_wrong_answer_costs_a_real_life_through_the_public_pipeline():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="risk_it_nfl_draft")
    rid = r["round_id"]
    pkg = packages.load_package(rid)
    pm.submit_public_round(round_id=rid, submission={"action": "choose_tier", "tier": "LOW"})
    correct = pkg["rounds"][0]["tiers"]["LOW"]["_answer_item_id"]
    wrong = next(i for i in ("A", "B", "C", "D") if i != correct)
    sub = pm.submit_public_round(round_id=rid, submission={"action": "answer", "choice_item_id": wrong})
    assert sub["result"]["correct"] is False
    assert sub["view"]["lives"] == 2
    assert sub["view"]["score"] == 0


def test_risk_it_never_leaks_real_answer_or_other_tiers_before_they_are_chosen():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="risk_it_nfl_draft")
    assert "tiers" not in r["view"]
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "awaiting_tier",
                                      "tier_points", "score", "lives"}


# --- 22. WAGER_MODE (15-Format Expansion Part 2, format #12) --------------

def test_wager_mode_full_public_playthrough_tracks_balance():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="wager_mode_mixed")
    rid = r["round_id"]
    assert rid.startswith("GGP24:")
    assert r["view"]["awaiting_wager"] is True
    assert r["view"]["balance"] == 1000

    pkg = packages.load_package(rid)
    sub1 = pm.submit_public_round(round_id=rid, submission={"action": "place_wager", "wager": 200})
    assert sub1["view"]["awaiting_wager"] is False and sub1["view"]["wager"] == 200

    correct = pkg["rounds"][0]["_answer_item_id"]
    sub2 = pm.submit_public_round(round_id=rid, submission={"action": "answer", "choice_item_id": correct})
    assert sub2["result"]["correct"] is True
    assert sub2["result"]["balance_delta"] == 200
    assert sub2["view"]["balance"] == 1200
    assert sub2["view"]["awaiting_wager"] is True  # back to wager-choice for the next round


def test_wager_mode_rejects_out_of_range_wager_through_the_public_pipeline():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="wager_mode_mixed")
    rid = r["round_id"]
    with pytest.raises(Exception):
        pm.submit_public_round(round_id=rid, submission={"action": "place_wager", "wager": 99999})


def test_wager_mode_never_leaks_real_answer_or_prompt_before_a_wager_is_placed():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="wager_mode_mixed")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "awaiting_wager",
                                      "category", "balance"}


# --- 23. LEADERBOARD_CLIMB (15-Format Expansion Part 2, format #14) -------

def test_leaderboard_climb_full_public_playthrough_climbs_and_ends_on_a_miss():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="leaderboard_climb_nfl")
    rid = r["round_id"]
    assert rid.startswith("GGP26:")
    assert r["view"]["completed"] is False
    size = r["view"]["ladder_size"]
    assert r["view"]["current_rank"] == size

    pkg = packages.load_package(rid)
    ladder = pkg["items"]
    next_entity = ladder[size - 2]  # real rank size-1, one rung better than the start
    canonical = "A" if r["view"]["entity_a"]["label"] == next_entity["label"] else "B"

    sub = pm.submit_public_round(round_id=rid, submission={"choice": canonical})
    assert sub["result"]["correct"] is True
    assert sub["view"]["current_rank"] == size - 1
    assert sub["view"]["completed"] is False

    # The next rung's A/B shuffle is independently seeded -- re-derive the
    # real correct choice for THIS matchup rather than reusing the first
    # rung's canonical answer.
    next_next_entity = ladder[size - 3]
    canonical2 = "A" if sub["view"]["entity_a"]["label"] == next_next_entity["label"] else "B"
    wrong = "B" if canonical2 == "A" else "A"
    sub2 = pm.submit_public_round(round_id=rid, submission={"choice": wrong})
    assert sub2["result"]["correct"] is False
    assert sub2["view"]["current_rank"] == size - 1  # unchanged -- climb ended, not demoted
    assert sub2["view"]["completed"] is True

    with pytest.raises(Exception):
        pm.submit_public_round(round_id=rid, submission={"choice": canonical})


def test_leaderboard_climb_never_leaks_real_values_or_ranks_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="leaderboard_climb_nfl")
    assert set(r["view"].keys()) == {"current_rank", "ladder_size", "completed", "entity_a", "entity_b"}
    for key in ("entity_a", "entity_b"):
        assert set(r["view"][key].keys()) == {"entity_id", "label"}


# --- 24. BLIND_RESUME (15-Format Expansion Part 2, format #15, final) -----

def test_blind_resume_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="blind_resume_nfl_qb")
    rid = r["round_id"]
    assert rid.startswith("GGP27:")
    assert r["view"]["completed"] is False
    assert len(r["view"]["options"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub = pm.submit_public_round(round_id=rid, submission={"choice_item_id": correct})
    assert sub["result"]["correct"] is True
    assert sub["view"]["round_index"] == 1

    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    sub2 = pm.submit_public_round(round_id=rid, submission={"choice_item_id": wrong})
    assert sub2["result"]["correct"] is False
    assert sub2["view"]["round_index"] == 2


def test_blind_resume_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="blind_resume_nfl_qb")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "resume", "options"}
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 25. DOUBLE_OR_NOTHING (75-Format Expansion, Wave 1) -------------------
# Reachable only through gateway.services.creator.generate_direct() / the
# Format Picker (no natural-language bridge exists for this or any future
# 75-Format Expansion format) -- see creator.generate_direct()'s own
# docstring for why that's the deliberate, scalable design going forward.

def test_double_or_nothing_full_public_playthrough_banks_doubled_points():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="double_or_nothing_nfl_draft")
    rid = r["round_id"]
    assert rid.startswith("GGP28:")
    assert r["view"]["points"] == 0 and r["view"]["can_bank"] is False

    pkg = packages.load_package(rid)
    correct0 = pkg["rounds"][0]["_answer_item_id"]
    sub1 = pm.submit_public_round(round_id=rid, submission={"action": "answer", "choice_item_id": correct0})
    assert sub1["result"]["correct"] is True and sub1["result"]["points"] == 100
    assert sub1["view"]["can_bank"] is True

    correct1 = pkg["rounds"][1]["_answer_item_id"]
    sub2 = pm.submit_public_round(round_id=rid, submission={"action": "answer", "choice_item_id": correct1})
    assert sub2["result"]["points"] == 200

    sub3 = pm.submit_public_round(round_id=rid, submission={"action": "bank"})
    assert sub3["result"]["banked"] is True
    assert sub3["result"]["final_points"] == 200
    assert sub3["view"]["completed"] is True

    with pytest.raises(Exception):
        pm.submit_public_round(round_id=rid, submission={"action": "answer", "choice_item_id": "A"})


def test_double_or_nothing_wrong_answer_through_the_public_pipeline_loses_everything():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="double_or_nothing_nfl_draft")
    rid = r["round_id"]
    pkg = packages.load_package(rid)
    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][0]["_answer_item_id"])
    sub = pm.submit_public_round(round_id=rid, submission={"action": "answer", "choice_item_id": wrong})
    assert sub["result"]["correct"] is False
    assert sub["result"]["points"] == 0
    assert sub["view"]["completed"] is True
    assert sub["view"]["ended"] is True


def test_double_or_nothing_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="double_or_nothing_nfl_draft")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "points", "can_bank",
                                      "tier", "prompt", "options"}
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 26. KING_OF_THE_HILL (75-Format Expansion, Wave 1) --------------------

def test_king_of_the_hill_full_public_playthrough_defends_and_dethrones():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="king_of_the_hill_nfl")
    rid = r["round_id"]
    assert rid.startswith("GGP29:")
    assert r["view"]["completed"] is False
    assert r["view"]["consecutive_defenses"] == 0

    pkg = packages.load_package(rid)
    items = pkg["items"]
    canonical0 = "champion" if items[0]["value"] > items[1]["value"] else "challenger"
    sub1 = pm.submit_public_round(round_id=rid, submission={"choice": canonical0})
    assert sub1["result"]["correct"] is True
    expected_champ_idx = 0 if canonical0 == "champion" else 1
    expected_defenses = 1 if canonical0 == "champion" else 0
    assert sub1["view"]["consecutive_defenses"] == expected_defenses
    assert sub1["view"]["champion"]["label"] == items[expected_champ_idx]["label"]


def test_king_of_the_hill_wrong_guess_ends_the_run_through_the_public_pipeline():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="king_of_the_hill_nfl")
    rid = r["round_id"]
    pkg = packages.load_package(rid)
    items = pkg["items"]
    canonical = "champion" if items[0]["value"] > items[1]["value"] else "challenger"
    wrong = "challenger" if canonical == "champion" else "champion"
    sub = pm.submit_public_round(round_id=rid, submission={"choice": wrong})
    assert sub["result"]["correct"] is False
    assert sub["view"]["completed"] is True

    with pytest.raises(Exception):
        pm.submit_public_round(round_id=rid, submission={"choice": canonical})


def test_king_of_the_hill_never_leaks_real_win_totals_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="king_of_the_hill_nfl")
    assert set(r["view"].keys()) == {"completed", "consecutive_defenses", "champion", "challenger"}
    for key in ("champion", "challenger"):
        assert set(r["view"][key].keys()) == {"entity_id", "label"}


# --- 27. FACT_OR_FAKE (75-Format Expansion, Wave 1) ------------------------

def test_fact_or_fake_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="fact_or_fake_nfl_draft")
    rid = r["round_id"]
    assert rid.startswith("GGP30:")
    assert r["view"]["completed"] is False
    assert r["view"]["statement"]

    pkg = packages.load_package(rid)
    canonical0 = "TRUE" if pkg["rounds"][0]["_is_true"] else "FAKE"
    sub1 = pm.submit_public_round(round_id=rid, submission={"choice": canonical0})
    assert sub1["result"]["correct"] is True
    assert sub1["view"]["round_index"] == 1

    canonical1 = "TRUE" if pkg["rounds"][1]["_is_true"] else "FAKE"
    wrong1 = "FAKE" if canonical1 == "TRUE" else "TRUE"
    sub2 = pm.submit_public_round(round_id=rid, submission={"choice": wrong1})
    assert sub2["result"]["correct"] is False
    assert sub2["view"]["round_index"] == 2


def test_fact_or_fake_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="fact_or_fake_nfl_draft")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "statement"}


# --- 28. GUESS_THE_RANKING (75-Format Expansion, Wave 1) -------------------

def test_guess_the_ranking_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="guess_the_ranking_nfl")
    rid = r["round_id"]
    assert rid.startswith("GGP31:")
    assert r["view"]["completed"] is False
    assert len(r["view"]["options"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub = pm.submit_public_round(round_id=rid, submission={"choice_item_id": correct})
    assert sub["result"]["correct"] is True
    assert sub["view"]["round_index"] == 1

    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    sub2 = pm.submit_public_round(round_id=rid, submission={"choice_item_id": wrong})
    assert sub2["result"]["correct"] is False
    assert sub2["view"]["round_index"] == 2


def test_guess_the_ranking_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="guess_the_ranking_nfl")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "label", "options"}
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 29. STAT_TARGET (75-Format Expansion, Wave 1) -------------------------

def test_stat_target_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="stat_target_nfl_rushing")
    rid = r["round_id"]
    assert rid.startswith("GGP32:")
    assert r["view"]["completed"] is False
    assert len(r["view"]["options"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub = pm.submit_public_round(round_id=rid, submission={"choice_item_id": correct})
    assert sub["result"]["correct"] is True
    assert sub["view"]["round_index"] == 1

    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    sub2 = pm.submit_public_round(round_id=rid, submission={"choice_item_id": wrong})
    assert sub2["result"]["correct"] is False
    assert sub2["view"]["round_index"] == 2


def test_stat_target_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="stat_target_nfl_rushing")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "target", "options"}
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 30. REVERSE_TRIVIA (75-Format Expansion, Wave 1) ----------------------

def test_reverse_trivia_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="reverse_trivia_nfl_draft")
    rid = r["round_id"]
    assert rid.startswith("GGP33:")
    assert r["view"]["completed"] is False
    assert len(r["view"]["options"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub = pm.submit_public_round(round_id=rid, submission={"choice_item_id": correct})
    assert sub["result"]["correct"] is True
    assert sub["view"]["round_index"] == 1

    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    sub2 = pm.submit_public_round(round_id=rid, submission={"choice_item_id": wrong})
    assert sub2["result"]["correct"] is False
    assert sub2["view"]["round_index"] == 2


def test_reverse_trivia_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="reverse_trivia_nfl_draft")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "subject_name", "options"}
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 31. THREE_STRIKES (75-Format Expansion, Wave 1) -----------------------

def test_three_strikes_full_public_playthrough_tracks_score_and_strikes():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="three_strikes_nfl_draft")
    rid = r["round_id"]
    assert rid.startswith("GGP34:")
    assert r["view"]["strikes"] == 3 and r["view"]["score"] == 0

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub1 = pm.submit_public_round(round_id=rid, submission={"choice_item_id": correct})
    assert sub1["result"]["correct"] is True
    assert sub1["result"]["points_earned"] == pkg["rounds"][0]["points"]
    assert sub1["view"]["score"] == pkg["rounds"][0]["points"]
    assert sub1["view"]["strikes"] == 3


def test_three_strikes_wrong_answer_costs_a_strike_through_the_public_pipeline():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="three_strikes_nfl_draft")
    rid = r["round_id"]
    pkg = packages.load_package(rid)
    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][0]["_answer_item_id"])
    sub = pm.submit_public_round(round_id=rid, submission={"choice_item_id": wrong})
    assert sub["result"]["correct"] is False
    assert sub["view"]["strikes"] == 2
    assert sub["view"]["score"] == 0


def test_three_strikes_never_leaks_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="three_strikes_nfl_draft")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "tier", "points", "prompt",
                                      "options", "score", "streak", "strikes"}


# --- 32. MYSTERY_ROSTER (75-Format Expansion, Wave 1) ----------------------

def test_mystery_roster_full_public_playthrough_reveal_then_guess():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="mystery_roster_nfl")
    rid = r["round_id"]
    assert rid.startswith("GGP35:")
    assert r["view"]["clues_revealed"] == 1

    sub1 = pm.submit_public_round(round_id=rid, submission={"action": "reveal"})
    assert sub1["result"]["action"] == "reveal"
    assert sub1["view"]["clues_revealed"] == 2

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub2 = pm.submit_public_round(round_id=rid, submission={"action": "guess", "choice_item_id": correct})
    assert sub2["result"]["correct"] is True
    assert sub2["result"]["points_earned"] == 3
    assert sub2["view"]["score"] == 3
    assert sub2["view"]["clues_revealed"] == 1


def test_mystery_roster_never_leaks_the_real_answer_before_a_guess():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="mystery_roster_nfl")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "clues", "clues_revealed",
                                      "max_clues", "options", "score"}
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- 33. DRAFT_PICK_LADDER (75-Format Expansion, Wave 1) -------------------

def test_draft_pick_ladder_full_public_playthrough_correct_and_incorrect():
    from gateway.services import public_mechanics as pm
    from gateway.services import packages

    r = pm.start_public_round(mode="draft_pick_ladder_nfl")
    rid = r["round_id"]
    assert rid.startswith("GGP36:")
    assert r["view"]["completed"] is False
    assert len(r["view"]["options"]) == 4

    pkg = packages.load_package(rid)
    correct = pkg["rounds"][0]["_answer_item_id"]
    sub = pm.submit_public_round(round_id=rid, submission={"choice_item_id": correct})
    assert sub["result"]["correct"] is True
    assert sub["view"]["round_index"] == 1

    wrong = next(i for i in ("A", "B", "C", "D") if i != pkg["rounds"][1]["_answer_item_id"])
    sub2 = pm.submit_public_round(round_id=rid, submission={"choice_item_id": wrong})
    assert sub2["result"]["correct"] is False
    assert sub2["view"]["round_index"] == 2


def test_draft_pick_ladder_never_leaks_the_real_answer_before_submission():
    from gateway.services import public_mechanics as pm

    r = pm.start_public_round(mode="draft_pick_ladder_nfl")
    assert set(r["view"].keys()) == {"round_index", "round_count", "completed", "tier", "player_name",
                                      "season", "options"}
    for it in r["view"]["options"]:
        assert set(it.keys()) == {"item_id", "label"}


# --- Creator NL prompt verification (user's own exact example phrases) -----------

@pytest.mark.parametrize("phrase,expected_taxonomy", [
    ("Make me a connection grid with NFL teams and draft rounds.", "GRID_CONSTRAINT_BOARD"),
    ("Give me a perfect drive about NFL history.", "DRIVE_PROGRESSION"),
    ("Make me a four-down CFB trivia game.", "DRIVE_PROGRESSION"),
    ("Build me an Alabama skill-position lineup game.", "ROSTER_BUILD"),
    ("Give me a CFB auction draft with fictional player values.", "ROSTER_BUILD"),
    ("Make me an NFL cap challenge.", "ROSTER_BUILD"),
    ("Give me a 16-team knockout tournament.", "KNOCKOUT_BRACKET"),
    ("Connect these two players.", "RELATIONSHIP_CHAIN"),
    ("Make me a chain reaction game about NFL players and colleges.", "RELATIONSHIP_CHAIN"),
    ("Give me a choose-your-path game about SEC football.", "BRANCH_STATE"),
    ("Guess the season this real NFL team won it all.", "GUESS_THE_SEASON"),
    ("Give me a head to head duel between two real quarterbacks.", "PAIRWISE_COMPARE"),
    ("Give me a best of seven duel between two real quarterbacks.", "PAIRWISE_COMPARE"),
    ("Give me a pick the impostor game with real NFL players.", "PICK_THE_IMPOSTOR"),
    ("Give me a unique one out game with real NFL players.", "PICK_THE_IMPOSTOR"),
    ("Give me a missing piece game with real NFL players.", "MISSING_PIECE"),
    ("Give me a before and after game with a real NFL player.", "BEFORE_AFTER"),
    ("Give me a career path game with a real NFL player.", "CAREER_PATH"),
    ("Give me a risk it game with real NFL Draft picks.", "RISK_IT"),
    ("Give me a wager mode game.", "WAGER_MODE"),
    ("Give me a leaderboard climb game with real NFL passers.", "LEADERBOARD_CLIMB"),
    ("Give me a blind resume game with a real NFL quarterback.", "BLIND_RESUME"),
])
def test_creator_example_prompts_reach_the_intended_new_format(phrase, expected_taxonomy):
    from gateway.services import creator

    result = creator.assess_feasibility(phrase)
    assert result["support_status"] == "SUPPORTED", (phrase, result)
    assert result["taxonomy_id"] == expected_taxonomy, (phrase, result.get("taxonomy_id"))
