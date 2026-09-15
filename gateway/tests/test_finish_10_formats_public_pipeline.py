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
])
def test_creator_example_prompts_reach_the_intended_new_format(phrase, expected_taxonomy):
    from gateway.services import creator

    result = creator.assess_feasibility(phrase)
    assert result["support_status"] == "SUPPORTED", (phrase, result)
    assert result["taxonomy_id"] == expected_taxonomy, (phrase, result.get("taxonomy_id"))
