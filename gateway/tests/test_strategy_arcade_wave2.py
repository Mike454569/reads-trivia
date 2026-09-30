"""100-format Expansion Wave 2 -- strategy arcade unit coverage.

These tests deliberately use a tiny certified-shaped in-memory package so every
state machine can be exercised in CI without the multi-GB production database.
The real generator path has separate integration coverage through public/Creator
tests; this file locks the gameplay/state contracts themselves.
"""
from __future__ import annotations

import pytest

from tools.director_v04 import strategy_arcade as sa


def _package(variant: str) -> dict:
    cats = ("NFL Team Records", "Heisman Winners", "Super Bowl Champions")
    rounds = []
    for i in range(30):
        rounds.append({
            "round_index": i,
            "category": cats[i % 3],
            "prompt": f"Real question {i}?",
            "options": [
                {"item_id": "A", "label": f"Correct {i}"},
                {"item_id": "B", "label": f"Decoy B {i}"},
                {"item_id": "C", "label": f"Decoy C {i}"},
                {"item_id": "D", "label": f"Decoy D {i}"},
            ],
            "_answer_item_id": "A",
            "_notes": f"Source-backed note {i}",
        })
    return {
        "domain_variant": variant,
        "format_id": variant,
        "rounds": rounds,
        "round_count": len(rounds),
    }


def _answer(package, progress, choice="A"):
    return sa.evaluate(package, progress, {"choice_item_id": choice})


@pytest.mark.parametrize("variant", sorted(sa.VARIANTS))
def test_every_strategy_variant_has_distinct_spec_and_safe_initial_view(variant):
    package = _package(variant)
    view = sa.client_view(package, {})
    assert view["format_id"] == variant
    assert view["title"] == sa.FORMAT_SPECS[variant]["title"]
    assert "_answer_item_id" not in repr(view)
    assert "_notes" not in repr(view)


def test_bingo_blitz_claims_cell():
    p=_package("BINGO_BLITZ"); _,s=sa.evaluate(p,{},{"action":"0"}); r,s=_answer(p,s)
    assert r["correct"] and 0 in s["claimed"]


def test_territory_takeover_awards_selected_zone():
    p=_package("TERRITORY_TAKEOVER"); _,s=sa.evaluate(p,{},{"action":"2"}); _,s=_answer(p,s)
    assert s["owners"]["2"]=="YOU" and s["player_points"]==3


def test_exact_ten_commits_points_before_question():
    p=_package("EXACT_TEN"); _,s=sa.evaluate(p,{},{"action":"3"}); _,s=_answer(p,s)
    assert s["total"] == 3 and "stake" not in s


def test_pyramid_climb_moves_both_directions():
    p=_package("PYRAMID_CLIMB"); _,s=sa.evaluate(p,{},{"action":"left"}); _,s=_answer(p,s)
    assert s["level"]==1
    _,s=sa.evaluate(p,s,{"action":"right"}); _,s=_answer(p,s,"B")
    assert s["level"]==0


def test_lockbox_requires_three_open_locks_before_vault():
    p=_package("LOCKBOX"); s={}
    for lock in ("0","1","2"):
        _,s=sa.evaluate(p,s,{"action":lock}); _,s=_answer(p,s)
    v=sa.client_view(p,s)
    assert any(a["id"]=="vault" for a in v["actions"])


def test_combo_meter_multiplier_resets_on_miss():
    p=_package("COMBO_METER"); _,s=_answer(p,{})
    assert s["multiplier"]==2
    _,s=_answer(p,s,"B")
    assert s["multiplier"]==1


def test_checkpoint_rally_rolls_back_to_saved_checkpoint():
    p=_package("CHECKPOINT_RALLY"); s={}
    _,s=_answer(p,s); _,s=_answer(p,s)
    assert s["checkpoint"]==2
    _,s=_answer(p,s); _,s=_answer(p,s,"B")
    assert s["distance"]==2


def test_escalator_risk_changes_step_delta():
    p=_package("ESCALATOR"); _,s=sa.evaluate(p,{},{"action":"2"}); _,s=_answer(p,s)
    assert s["step"]==2


def test_power_up_50_50_costs_energy_and_hides_two_decoys():
    p=_package("POWER_UP"); s={"energy":2}
    _,s=sa.evaluate(p,s,{"action":"fifty"})
    v=sa.client_view(p,s)
    assert s["energy"]==0 and len(v["options"])==2
    assert any(o["item_id"]=="A" for o in v["options"])


def test_category_conquest_targets_real_category():
    p=_package("CATEGORY_CONQUEST"); _,s=sa.evaluate(p,{},{"action":"Heisman Winners"})
    assert sa.client_view(p,s)["category"]=="Heisman Winners"
    _,s=_answer(p,s)
    assert "Heisman Winners" in s["captured"]


def test_scoreboard_swing_races_to_21():
    p=_package("SCOREBOARD_SWING"); s={}
    for _ in range(3): _,s=_answer(p,s)
    assert s["player_score"]==21 and s["completed"]


def test_momentum_bar_has_streak_bonus():
    p=_package("MOMENTUM_BAR"); s={}
    for _ in range(3): _,s=_answer(p,s)
    assert s["momentum"]==7


def test_timeout_tokens_skip_and_double_are_consumed():
    p=_package("TIMEOUT_TOKENS"); _,s=sa.evaluate(p,{},{"action":"skip"})
    assert s["skips"]==1 and s["cursor"]==1
    _,s=sa.evaluate(p,s,{"action":"double"}); _,s=_answer(p,s)
    assert s["double"]==0 and s["score"]==200


def test_perfect_set_wins_two_sets():
    p=_package("PERFECT_SET"); s={}
    for _ in range(4): _,s=_answer(p,s)
    assert s["sets_won"]==2 and s["completed"]


def test_triple_or_take_banks_only_completed_series():
    p=_package("TRIPLE_OR_TAKE"); _,s=sa.evaluate(p,{},{"action":"3"})
    for _ in range(3): _,s=_answer(p,s)
    assert s["score"]==6 and s["series_done"]==1


def test_wave2_moves_honest_distinct_format_count_to_62():
    from tools.director_v02.format_audit import audit_format_registry
    audit=audit_format_registry()
    assert audit["registered_format_count"]==63
    assert audit["presentation_alias_count"]==1
    assert audit["distinct_format_count"]==62
    assert audit["target_gap"]==38
    assert audit["mobile_unverified"]==[]
