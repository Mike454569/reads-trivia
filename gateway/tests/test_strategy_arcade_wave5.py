"""100-format Expansion Wave 5 -- final formats 93-100."""
from __future__ import annotations

import pytest
from tools.director_v04 import strategy_arcade_wave5 as w5

def _package(variant:str)->dict:
    cats=("NFL Team Records","Heisman Winners","Super Bowl Champions")
    rounds=[]
    for i in range(48):
        rounds.append({"round_index":i,"category":cats[i%3],"prompt":f"Real question {i}?",
          "options":[{"item_id":"A","label":f"Correct {i}"},{"item_id":"B","label":f"Decoy B {i}"},{"item_id":"C","label":f"Decoy C {i}"},{"item_id":"D","label":f"Decoy D {i}"}],
          "_answer_item_id":"A","_notes":f"Source note {i}"})
    return {"domain_variant":variant,"format_id":variant,"rounds":rounds,"round_count":len(rounds)}

def _answer(p,s,choice="A"): return w5.evaluate(p,s,{"choice_item_id":choice})

@pytest.mark.parametrize("variant",sorted(w5.VARIANTS))
def test_every_wave5_variant_has_safe_initial_view(variant):
    v=w5.client_view(_package(variant),{})
    assert v["format_id"]==variant
    assert "_answer_item_id" not in repr(v)
    assert "_notes" not in repr(v)

def test_option_eraser_spends_token_and_removes_one_decoy():
    p=_package("OPTION_ERASER"); _,s=w5.evaluate(p,{},{"action":"erase"})
    v=w5.client_view(p,s)
    assert s["erasers"]==2 and len(v["options"])==3

def test_route_tree_tracks_three_distinct_routes():
    p=_package("ROUTE_TREE"); s={}
    for route in ("slant","post","go"):
        _,s=w5.evaluate(p,s,{"action":route}); _,s=_answer(p,s)
    assert s["completed"] and s["score"]==6

def test_turnover_battle_resets_drive_yards_only():
    p=_package("TURNOVER_BATTLE"); _,s=_answer(p,{})
    assert s["drive_yards"]==10 and s["total_yards"]==10
    _,s=_answer(p,s,"B")
    assert s["drive_yards"]==0 and s["total_yards"]==10

def test_category_lockout_scores_selected_category():
    p=_package("CATEGORY_LOCKOUT"); _,s=w5.evaluate(p,{},{"action":"Heisman Winners"}); _,s=_answer(p,s)
    assert "Heisman Winners" in s["scored_categories"]

def test_hail_mary_unlocks_at_exactly_three_of_five():
    p=_package("HAIL_MARY"); s={}
    for choice in ("A","A","A","B","B"): _,s=_answer(p,s,choice)
    assert s["hail_mary"] and not s["completed"]

def test_moving_target_changes_after_answer():
    p=_package("MOVING_TARGET"); _,s=w5.evaluate(p,{},{"action":"2"}); _,s=_answer(p,s)
    assert s["score"]==2 and s["target"]!=9

def test_draft_order_aggressive_trade_moves_three_slots():
    p=_package("DRAFT_ORDER"); _,s=w5.evaluate(p,{},{"action":"aggressive"}); _,s=_answer(p,s)
    assert s["pick"]==7

def test_championship_run_advances_stage():
    p=_package("CHAMPIONSHIP_RUN"); _,s=_answer(p,{})
    assert s["stage"]==1 and not s["completed"]

def test_final_wave_reaches_exactly_100_distinct_formats():
    from tools.director_v02.format_audit import audit_format_registry
    audit=audit_format_registry()
    assert audit["registered_format_count"]==101
    assert audit["presentation_alias_count"]==1
    assert audit["distinct_format_count"]==100
    assert audit["target_gap"]==0
    assert audit["mobile_unverified"]==[]
