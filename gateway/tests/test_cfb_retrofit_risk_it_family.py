"""CFB retrofit pass -- RISK_IT gained a real CFB tiering proxy (per-
season national passing-yards rank, since no draft-style pick number
exists for CFB players), and THREE_STRIKES / DOUBLE_OR_NOTHING both reuse
it verbatim via risk_it._CFB_TIER_RANGES / _rows_for_tier_cfb /
_build_tier_question_cfb. This file covers all 3 formats' CFB variants
together since they share the exact same underlying tiering logic.
"""
import pytest

from tools.director_v04 import risk_it, three_strikes, double_or_nothing
from tools.director_v02 import mechanic_engine
from gateway.services import creator, public_mechanics


# ---- RISK_IT ----

def test_risk_it_cfb_variant_registered():
    assert "CFB_SEASON_PASSING_RISK_IT" in risk_it.VARIANTS
    assert "NFL_DRAFT_RISK_IT" in risk_it.VARIANTS


def test_risk_it_cfb_generates_real_rounds():
    pkg = risk_it.build_package(seed="test-cfb-ri-1", variant="CFB_SEASON_PASSING_RISK_IT", round_count=5)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Risk It (CFB)"
    for r in pkg["rounds"]:
        for tier, q in r["tiers"].items():
            assert "school" in q["prompt"]
            assert "SPORTSDATAVERSE_CFB" in q["_notes"]


def test_risk_it_nfl_unaffected():
    pkg = risk_it.build_package(seed="test-nfl-ri-regress", variant="NFL_DRAFT_RISK_IT", round_count=4)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Risk It"


def test_risk_it_public_mode_and_two_step_roundtrip():
    assert "risk_it_cfb_passing" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["risk_it_cfb_passing"]
    assert entry["variant"] == "CFB_SEASON_PASSING_RISK_IT"
    r = public_mechanics.start_public_round(mode="risk_it_cfb_passing")
    tier_result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"action": "choose_tier", "tier": "LOW"})
    options = tier_result["view"]["options"]
    answer_result = public_mechanics.submit_public_round(
        round_id=r["round_id"], submission={"action": "answer", "choice_item_id": options[0]["item_id"]})
    assert "correct" in answer_result["result"]


# ---- THREE_STRIKES ----

def test_three_strikes_cfb_variant_registered():
    assert "CFB_SEASON_PASSING_THREE_STRIKES" in three_strikes.VARIANTS


def test_three_strikes_cfb_generates_real_rounds():
    pkg = three_strikes.build_package(seed="test-cfb-ts-1", variant="CFB_SEASON_PASSING_THREE_STRIKES", round_count=9)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Three Strikes (CFB)"
    assert all("school" in r["prompt"] for r in pkg["rounds"])


def test_three_strikes_nfl_unaffected():
    pkg = three_strikes.build_package(seed="test-nfl-ts-regress", variant="NFL_DRAFT_THREE_STRIKES", round_count=6)
    assert pkg["qa_status"] == "PASSED"


def test_three_strikes_public_round_roundtrip():
    r = public_mechanics.start_public_round(mode="three_strikes_cfb_passing")
    options = r["view"]["options"]
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]


# ---- DOUBLE_OR_NOTHING ----

def test_double_or_nothing_cfb_variant_registered():
    assert "CFB_SEASON_PASSING_DOUBLE_OR_NOTHING" in double_or_nothing.VARIANTS


def test_double_or_nothing_cfb_generates_real_rounds():
    pkg = double_or_nothing.build_package(seed="test-cfb-don-1", variant="CFB_SEASON_PASSING_DOUBLE_OR_NOTHING", round_count=3)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Double or Nothing (CFB)"


def test_double_or_nothing_nfl_unaffected():
    pkg = double_or_nothing.build_package(seed="test-nfl-don-regress", variant="NFL_DRAFT_DOUBLE_OR_NOTHING", round_count=3)
    assert pkg["qa_status"] == "PASSED"


def test_double_or_nothing_public_round_roundtrip():
    r = public_mechanics.start_public_round(mode="double_or_nothing_cfb_passing")
    options = r["view"]["options"]
    result = public_mechanics.submit_public_round(
        round_id=r["round_id"], submission={"action": "answer", "choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]


# ---- shared mechanic_engine wiring ----

def test_mechanic_engine_variants_dict_has_all_3_cfb_entries():
    assert mechanic_engine.VARIANTS["RISK_IT"]["CFB_SEASON_PASSING_RISK_IT"]["competition"] == "CFB"
    assert mechanic_engine.VARIANTS["THREE_STRIKES"]["CFB_SEASON_PASSING_THREE_STRIKES"]["competition"] == "CFB"
    assert mechanic_engine.VARIANTS["DOUBLE_OR_NOTHING"]["CFB_SEASON_PASSING_DOUBLE_OR_NOTHING"]["competition"] == "CFB"


def test_cfb_tier_ranges_cover_low_medium_high():
    assert set(risk_it._CFB_TIER_RANGES.keys()) == {"LOW", "MEDIUM", "HIGH"}
