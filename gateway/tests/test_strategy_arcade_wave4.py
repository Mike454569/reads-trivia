"""100-format Expansion Wave 4 -- formats 78-92 state-machine coverage."""
from __future__ import annotations

import pytest
from tools.director_v04 import strategy_arcade_wave4 as w4

def _package(variant:str)->dict:
    cats=("Game Day","Season & Legacy","College Chaos")
    rounds=[]
    for i in range(48):
        rounds.append({"round_index":i,"category":cats[i%3],"bucket":cats[i%3],"prompt":f"Real question {i}?",
          "options":[{"item_id":"A","label":f"Correct {i}"},{"item_id":"B","label":f"Decoy B {i}"},{"item_id":"C","label":f"Decoy C {i}"},{"item_id":"D","label":f"Decoy D {i}"}],
          "_answer_item_id":"A","_notes":f"Source note {i}"})
    return {"domain_variant":variant,"format_id":variant,"rounds":rounds,"round_count":len(rounds)}

def _answer(p,s,choice="A"): return w4.evaluate(p,s,{"choice_item_id":choice})

@pytest.mark.parametrize("variant",sorted(w4.VARIANTS))
def test_every_wave4_variant_has_safe_initial_view(variant):
    v=w4.client_view(_package(variant),{})
    assert v["format_id"]==variant
    assert "_answer_item_id" not in repr(v)
    assert "_notes" not in repr(v)

def test_red_zone_ladder_advances_five_yards():
    p=_package("RED_ZONE_LADDER"); _,s=_answer(p,{})
    assert s["yards"]==5

def test_drive_builder_requires_distinct_play_types():
    p=_package("DRIVE_BUILDER"); _,s=w4.evaluate(p,{},{"action":"short"}); _,s=_answer(p,s)
    with pytest.raises(ValueError): w4.evaluate(p,s,{"action":"short"})

def test_hot_hand_switch_builds_multiplier():
    p=_package("HOT_HAND_SWITCH"); _,s=w4.evaluate(p,{},{"action":"Game Day"}); _,s=_answer(p,s)
    assert s["multiplier"]==2 and s["score"]==100

def test_overtime_shootout_scores_player_possession():
    p=_package("OVERTIME_SHOOTOUT"); _,s=_answer(p,{})
    assert s["player_score"]==7

def test_first_down_chain_converts_after_two_correct():
    p=_package("FIRST_DOWN_CHAIN"); s={}
    _,s=_answer(p,s); _,s=_answer(p,s)
    assert s["first_downs"]==1 and s["down"]==1

def test_blitz_package_rewards_risk_level():
    p=_package("BLITZ_PACKAGE"); _,s=w4.evaluate(p,{},{"action":"allout"}); _,s=_answer(p,s)
    assert s["sacks"]==3

def test_zone_control_claims_selected_zone():
    p=_package("ZONE_CONTROL"); _,s=w4.evaluate(p,{},{"action":"4"}); _,s=_answer(p,s)
    assert s["zones"]["4"]==1

def test_play_caller_has_different_rewards():
    p=_package("PLAY_CALLER"); _,s=w4.evaluate(p,{},{"action":"play_action"}); _,s=_answer(p,s)
    assert s["score"]==3

def test_possession_arrow_flips_on_miss():
    p=_package("POSSESSION_ARROW"); _,s=_answer(p,{},"B")
    assert s["possession"]=="THEM"

def test_sudden_death_miss_ends_game():
    p=_package("SUDDEN_DEATH"); _,s=_answer(p,{},"B")
    assert s["completed"] and "loss" in s["result_label"].lower()

def test_score_bank_can_bank_existing_pot():
    p=_package("SCORE_BANK"); _,s=w4.evaluate(p,{},{"action":"risk"}); _,s=_answer(p,s)
    assert s["pot"]==100
    _,s=w4.evaluate(p,s,{"action":"bank"})
    assert s["bank"]==100 and s["pot"]==0

def test_audible_spends_resource_and_switches_category():
    p=_package("AUDIBLE"); _,s=w4.evaluate(p,{},{"action":"Season & Legacy"})
    assert s["audibles"]==1 and w4.client_view(p,s)["category"]=="Season & Legacy"

def test_fourth_down_field_goal_banks_three():
    p=_package("FOURTH_DOWN_DECISION"); s={}
    for _ in range(3): _,s=_answer(p,s)
    assert s["decision_pending"]
    _,s=w4.evaluate(p,s,{"action":"field_goal"})
    assert s["score"]==3 and s["drive"]==1

def test_series_sweep_gets_bonus():
    p=_package("SERIES_SWEEP"); s={}
    for _ in range(3): _,s=_answer(p,s)
    assert s["completed"] and s["score"]==4

def test_road_to_100_uses_selected_shot_value():
    p=_package("ROAD_TO_100"); _,s=w4.evaluate(p,{},{"action":"30"}); _,s=_answer(p,s)
    assert s["score"]==30

def test_wave4_moves_honest_distinct_format_count_to_92():
    from tools.director_v02.format_audit import audit_format_registry
    audit=audit_format_registry()
    assert audit["registered_format_count"] >= 93
    assert audit["presentation_alias_count"] == 1
    assert audit["distinct_format_count"] >= 92
    assert audit["target_gap"] <= 8
    assert audit["mobile_unverified"]==[]
