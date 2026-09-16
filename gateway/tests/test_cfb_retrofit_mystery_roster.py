"""CFB retrofit pass -- CFB_TEAM_SEASON_MYSTERY_ROSTER on cfb_standings
(FBS only) + cfb_player_season_stats_real + cfb_roster_seasons_real.
Real, disclosed substitutions: leading passer for "starting QB" (no
starts column), leading rusher+receiver by combined yards for "top
player by AV" (no AV-equivalent column), and class_year (mapped to
Freshman..6th-year Senior) for "years of NFL experience".
"""
import pytest

from tools.director_v04 import mystery_roster
from tools.director_v02 import mechanic_engine
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_TEAM_SEASON_MYSTERY_ROSTER" in mystery_roster.VARIANTS
    assert "NFL_TEAM_SEASON_MYSTERY_ROSTER" in mystery_roster.VARIANTS


def test_cfb_variant_generates_real_rounds():
    pkg = mystery_roster.build_package(seed="test-cfb-mr-1", variant="CFB_TEAM_SEASON_MYSTERY_ROSTER", round_count=6)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Mystery Roster (CFB)"
    for r in pkg["rounds"]:
        assert len(r["clues"]) == 4
        assert len(set(o["label"] for o in r["options"])) == 4
        assert "SPORTSDATAVERSE_CFB" in r["_notes"]


def test_nfl_variant_unaffected():
    pkg = mystery_roster.build_package(seed="test-nfl-mr-regress", variant="NFL_TEAM_SEASON_MYSTERY_ROSTER", round_count=4)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Mystery Roster"


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="MYSTERY_ROSTER", variant="CFB_TEAM_SEASON_MYSTERY_ROSTER")
    assert r["round_id"]
    assert len(r["view"]["clues"]) >= 1


def test_public_mode_registered_and_dispatches():
    assert "mystery_roster_cfb" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["mystery_roster_cfb"]
    assert entry["taxonomy_id"] == "MYSTERY_ROSTER"
    assert entry["variant"] == "CFB_TEAM_SEASON_MYSTERY_ROSTER"
    assert entry["competition"] == "CFB"


def test_public_round_real_reveal_and_guess_roundtrip():
    r = public_mechanics.start_public_round(mode="mystery_roster_cfb")
    assert r["round_id"]
    options = r["view"]["options"]
    result = public_mechanics.submit_public_round(
        round_id=r["round_id"], submission={"action": "guess", "choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_TEAM_SEASON_MYSTERY_ROSTER" in mechanic_engine.VARIANTS["MYSTERY_ROSTER"]
    assert mechanic_engine.VARIANTS["MYSTERY_ROSTER"]["CFB_TEAM_SEASON_MYSTERY_ROSTER"]["competition"] == "CFB"


def test_safety_check_reports_cfb_tables():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = mystery_roster.safety_check(c)
    finally:
        c.close()
    assert "cfb_standings" in result
    assert "cfb_player_season_stats_real" in result
    assert "cfb_roster_seasons_real" in result


def test_class_year_labels_cover_all_real_values():
    assert set(mystery_roster._CFB_CLASS_YEAR_LABELS.keys()) == {"1", "2", "3", "4", "5", "6"}
