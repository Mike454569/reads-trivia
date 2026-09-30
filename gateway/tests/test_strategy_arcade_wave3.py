"""100-format Expansion Wave 3 -- formats 63-77 state-machine coverage."""
from __future__ import annotations

import pytest

from tools.director_v04 import strategy_arcade_wave3 as w3


def _package(variant: str) -> dict:
    cats=("NFL Team Records","Heisman Winners","Super Bowl Champions")
    rounds=[]
    for i in range(36):
        rounds.append({
            "round_index":i, "category":cats[i%3], "prompt":f"Real question {i}?",
            "options":[
                {"item_id":"A","label":f"Correct {i}"},
                {"item_id":"B","label":f"Decoy B {i}"},
                {"item_id":"C","label":f"Decoy C {i}"},
                {"item_id":"D","label":f"Decoy D {i}"},
            ],
            "_answer_item_id":"A", "_notes":f"Source-backed note {i}",
        })
    return {"domain_variant":variant,"format_id":variant,"rounds":rounds,"round_count":len(rounds)}


def _answer(p,s,choice="A"):
    return w3.evaluate(p,s,{"choice_item_id":choice})


@pytest.mark.parametrize("variant", sorted(w3.VARIANTS))
def test_every_wave3_variant_has_safe_initial_view(variant):
    v=w3.client_view(_package(variant),{})
    assert v["format_id"]==variant
    assert "_answer_item_id" not in repr(v)
    assert "_notes" not in repr(v)


def test_connect_four_uses_gravity_and_opponent_on_miss():
    p=_package("CONNECT_FOUR"); _,s=w3.evaluate(p,{},{"action":"0"}); _,s=_answer(p,s,"B")
    assert s["connect_board"][5][0]=="THEM"


def test_tic_tac_toe_claims_selected_square():
    p=_package("TIC_TAC_TOE"); _,s=w3.evaluate(p,{},{"action":"4"}); _,s=_answer(p,s)
    assert s["ttt_cells"]["4"]=="YOU"


def test_challenge_flag_replays_same_question_with_wrong_option_removed():
    p=_package("CHALLENGE_FLAG"); r,s=_answer(p,{})
    assert r["correct"]
    r,s=_answer(p,s,"B")
    assert s["review_pending"]
    _,s=w3.evaluate(p,s,{"action":"challenge"})
    v=w3.client_view(p,s)
    assert len(v["options"])==3 and all(o["item_id"]!="B" for o in v["options"])


def test_extra_point_opens_conversion_after_touchdown():
    p=_package("EXTRA_POINT"); _,s=_answer(p,{})
    assert s["score"]==6 and s["conversion_pending"]
    _,s=w3.evaluate(p,s,{"action":"kick"})
    assert s["score"]==7


def test_comeback_mode_completes_at_21():
    p=_package("COMEBACK_MODE"); s={}
    for _ in range(3): _,s=_answer(p,s)
    assert s["score"]==21 and s["completed"]


def test_category_draft_enforces_two_use_limit():
    p=_package("CATEGORY_DRAFT"); s={}
    for _ in range(2):
        _,s=w3.evaluate(p,s,{"action":"Heisman Winners"}); _,s=_answer(p,s)
    with pytest.raises(ValueError):
        w3.evaluate(p,s,{"action":"Heisman Winners"})


def test_three_and_out_converts_drive_on_one_correct():
    p=_package("THREE_AND_OUT"); _,s=_answer(p,{})
    assert s["drives_won"]==1 and s["drive_plays"]==0


def test_pick_your_poison_routes_selected_category():
    p=_package("PICK_YOUR_POISON"); _,s=w3.evaluate(p,{},{"action":"NFL Team Records"})
    assert w3.client_view(p,s)["category"]=="NFL Team Records"


def test_second_chance_queue_defers_first_miss():
    p=_package("SECOND_CHANCE_QUEUE"); _,s=_answer(p,{},"B")
    assert s["deferred_index"]==0 and s["cursor"]==1


def test_coverage_shell_tracks_zone_stops():
    p=_package("COVERAGE_SHELL"); _,s=w3.evaluate(p,{},{"action":"deep"}); _,s=_answer(p,s)
    assert s["zone_stops"]["deep"]==1


def test_offense_defense_alternates_scoring_roles():
    p=_package("OFFENSE_DEFENSE"); _,s=_answer(p,{})
    assert s["player_score"]==7
    _,s=_answer(p,s,"B")
    assert s["opponent_score"]==7


def test_field_goal_range_requires_progress_before_kick():
    p=_package("FIELD_GOAL_RANGE"); s={}
    with pytest.raises(ValueError): w3.evaluate(p,s,{"action":"kick"})
    for _ in range(2):
        _,s=w3.evaluate(p,s,{"action":"drive"}); _,s=_answer(p,s)
    assert s["yards"]==20
    _,s=w3.evaluate(p,s,{"action":"kick"})
    assert s["kick_question"]


def test_two_minute_drill_spends_clock_by_tempo():
    p=_package("TWO_MINUTE_DRILL"); _,s=w3.evaluate(p,{},{"action":"hurry"}); _,s=_answer(p,s)
    assert s["clock"]==105 and s["yards"]==8


def test_category_streak_tracks_categories_independently():
    p=_package("CATEGORY_STREAK"); _,s=w3.evaluate(p,{},{"action":"Heisman Winners"}); _,s=_answer(p,s)
    assert s["category_streaks"]["Heisman Winners"]==1


def test_perfect_quarter_scores_touchdown_for_two_for_two_drive():
    p=_package("PERFECT_QUARTER"); s={}
    _,s=_answer(p,s); _,s=_answer(p,s)
    assert s["touchdowns"]==1 and s["drive_index"]==1


def test_wave3_moves_honest_distinct_format_count_to_77():
    from tools.director_v02.format_audit import audit_format_registry
    audit=audit_format_registry()
    assert audit["registered_format_count"] >= 78
    assert audit["presentation_alias_count"] == 1
    assert audit["distinct_format_count"] >= 77
    assert audit["target_gap"] <= 23
    assert audit["mobile_unverified"]==[]
