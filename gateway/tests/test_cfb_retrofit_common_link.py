"""CFB retrofit pass -- CFB_SEASON_COMMON_LINK, deliberately NOT draft-
flavored: real school/season/conference link types on
cfb_player_season_stats_real + schools. Guards against the same real
player appearing twice in a trio (a season-level table can list one real
player across multiple seasons).
"""
import pytest

from tools.director_v04 import common_link
from tools.director_v02 import mechanic_engine
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_SEASON_COMMON_LINK" in common_link.VARIANTS
    assert "NFL_DRAFT_COMMON_LINK" in common_link.VARIANTS


def test_cfb_variant_generates_real_rounds():
    pkg = common_link.build_package(seed="test-cfb-cl-1", variant="CFB_SEASON_COMMON_LINK", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Common Link (CFB)"
    for r in pkg["rounds"]:
        assert len(r["names"]) == 3
        assert len(set(r["names"])) == 3  # 3 genuinely distinct real players
        assert "SPORTSDATAVERSE_CFB" in r["_notes"]


def test_nfl_variant_unaffected():
    pkg = common_link.build_package(seed="test-nfl-cl-regress", variant="NFL_DRAFT_COMMON_LINK", round_count=6)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Common Link"


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="COMMON_LINK", variant="CFB_SEASON_COMMON_LINK")
    assert r["round_id"]
    assert len(r["view"]["names"]) == 3


def test_public_mode_registered_and_dispatches():
    assert "common_link_cfb_season" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["common_link_cfb_season"]
    assert entry["taxonomy_id"] == "COMMON_LINK"
    assert entry["variant"] == "CFB_SEASON_COMMON_LINK"
    assert entry["competition"] == "CFB"


def test_public_round_real_fetch_and_submit_roundtrip():
    r = public_mechanics.start_public_round(mode="common_link_cfb_season")
    options = r["view"]["options"]
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_SEASON_COMMON_LINK" in mechanic_engine.VARIANTS["COMMON_LINK"]
    assert mechanic_engine.VARIANTS["COMMON_LINK"]["CFB_SEASON_COMMON_LINK"]["competition"] == "CFB"


def test_safety_check_reports_both_leagues():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = common_link.safety_check(c)
    finally:
        c.close()
    assert "draft_facts" in result
    assert "cfb_player_season_stats_real" in result
