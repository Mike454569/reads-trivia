"""CFB retrofit pass -- CFB_SEASON_PASSING_REVERSE_TRIVIA, deliberately
NOT draft-flavored: real single-season passing stat lines from
cfb_player_season_stats_real + schools.
"""
import pytest

from tools.director_v04 import reverse_trivia
from tools.director_v02 import mechanic_engine
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_SEASON_PASSING_REVERSE_TRIVIA" in reverse_trivia.VARIANTS
    assert "NFL_DRAFT_REVERSE_TRIVIA" in reverse_trivia.VARIANTS


def test_cfb_variant_generates_real_rounds():
    pkg = reverse_trivia.build_package(seed="test-cfb-rt-1", variant="CFB_SEASON_PASSING_REVERSE_TRIVIA", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Reverse Trivia (CFB)"
    for r in pkg["rounds"]:
        assert len(set(o["label"] for o in r["options"])) == 4
        assert "SPORTSDATAVERSE_CFB" in r["_notes"]
        assert "Threw for" in r["options"][0]["label"]


def test_nfl_variant_unaffected():
    pkg = reverse_trivia.build_package(seed="test-nfl-rt-regress", variant="NFL_DRAFT_REVERSE_TRIVIA", round_count=6)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Reverse Trivia"


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="REVERSE_TRIVIA", variant="CFB_SEASON_PASSING_REVERSE_TRIVIA")
    assert r["round_id"]
    assert len(r["view"]["options"]) == 4


def test_public_mode_registered_and_dispatches():
    assert "reverse_trivia_cfb_passing" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["reverse_trivia_cfb_passing"]
    assert entry["taxonomy_id"] == "REVERSE_TRIVIA"
    assert entry["variant"] == "CFB_SEASON_PASSING_REVERSE_TRIVIA"
    assert entry["competition"] == "CFB"


def test_public_round_real_fetch_and_submit_roundtrip():
    r = public_mechanics.start_public_round(mode="reverse_trivia_cfb_passing")
    options = r["view"]["options"]
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]
    assert result["result"]["canonical_answer"] in [o["label"] for o in options]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_SEASON_PASSING_REVERSE_TRIVIA" in mechanic_engine.VARIANTS["REVERSE_TRIVIA"]
    assert mechanic_engine.VARIANTS["REVERSE_TRIVIA"]["CFB_SEASON_PASSING_REVERSE_TRIVIA"]["competition"] == "CFB"


def test_safety_check_reports_both_leagues():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = reverse_trivia.safety_check(c)
    finally:
        c.close()
    assert "draft_facts" in result
    assert "cfb_player_season_stats_real" in result
