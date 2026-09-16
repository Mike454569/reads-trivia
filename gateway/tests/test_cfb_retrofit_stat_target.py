"""CFB retrofit pass (user request: "I want all these formats to be NFL
and CFB based not just nfl... for the formats already on the app also")
-- CFB_SEASON_RUSHING_YARDS_TARGET, the first CFB variant added to an
already-live NFL-only format (STAT_TARGET). Built on
cfb_player_season_stats_real (78,651 rows, SPORTSDATAVERSE_CFB,
SOURCE_BACKED_DERIVED, 2014-2025) -- reuses the exact same STAT_TARGET
mechanic/renderer as the NFL variant, only the data source differs.

Real bug caught before shipping: safety.check_table_wide_safety() is
hardcoded to require verification_status='SOURCE_BACKED' exactly --
cfb_player_season_stats_real genuinely uses 'SOURCE_BACKED_DERIVED'
instead, so check_verification_status_safety() (which takes the expected
status explicitly) is the correct function here.
"""
import pytest

from tools.director_v04 import stat_target
from tools.director_v02 import mechanic_engine, registry
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_SEASON_RUSHING_YARDS_TARGET" in stat_target.VARIANTS
    assert "NFL_SEASON_RUSHING_YARDS_TARGET" in stat_target.VARIANTS  # unchanged


def test_cfb_variant_generates_real_rounds():
    pkg = stat_target.build_package(seed="test-cfb-stat-target-1", variant="CFB_SEASON_RUSHING_YARDS_TARGET", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] == 8
    for r in pkg["rounds"]:
        assert len(r["options"]) == 4
        assert len(set(o["label"] for o in r["options"])) == 4
        assert "SPORTSDATAVERSE_CFB" in r["_notes"]


def test_nfl_variant_unaffected():
    pkg = stat_target.build_package(seed="test-nfl-stat-target-regression", variant="NFL_SEASON_RUSHING_YARDS_TARGET", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] == 8
    for r in pkg["rounds"]:
        assert "NFLVERSE_DATA" in r["_notes"]


def test_safety_check_uses_correct_verification_status():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = stat_target.safety_check(c)
    finally:
        c.close()
    cfb_check = result["cfb_player_season_stats_real"]
    assert cfb_check["source_id"] == "SPORTSDATAVERSE_CFB"
    assert cfb_check["approved_for_import"] is True
    assert cfb_check["cfb_player_season_stats_real_rows_total"] == cfb_check["cfb_player_season_stats_real_rows_verified"]


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="STAT_TARGET", variant="CFB_SEASON_RUSHING_YARDS_TARGET")
    assert r["round_id"]
    assert r["view"]["round_count"] == 8


def test_public_mode_registered_and_dispatches():
    assert "stat_target_cfb_rushing" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["stat_target_cfb_rushing"]
    assert entry["taxonomy_id"] == "STAT_TARGET"
    assert entry["variant"] == "CFB_SEASON_RUSHING_YARDS_TARGET"
    assert entry["competition"] == "CFB"


def test_public_round_real_fetch_and_submit_roundtrip():
    r = public_mechanics.start_public_round(mode="stat_target_cfb_rushing")
    assert r["round_id"]
    assert r["view"]["target"] > 0
    options = r["view"]["options"]
    assert len(options) == 4
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]
    assert "SPORTSDATAVERSE_CFB" in result["result"]["notes"]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_SEASON_RUSHING_YARDS_TARGET" in mechanic_engine.VARIANTS["STAT_TARGET"]
    assert mechanic_engine.VARIANTS["STAT_TARGET"]["CFB_SEASON_RUSHING_YARDS_TARGET"]["competition"] == "CFB"
