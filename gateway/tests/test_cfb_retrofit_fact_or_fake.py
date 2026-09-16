"""CFB retrofit pass -- CFB_GAME_RESULT_FACT_OR_FAKE, deliberately NOT
draft-flavored (CFB players aren't drafted): a real final-score statement
built on cfb_games_canonical + schools, with score substitution (not team
substitution) as the provably-false mechanism.
"""
import pytest

from tools.director_v04 import fact_or_fake
from tools.director_v02 import mechanic_engine
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_GAME_RESULT_FACT_OR_FAKE" in fact_or_fake.VARIANTS
    assert "NFL_DRAFT_FACT_OR_FAKE" in fact_or_fake.VARIANTS


def test_cfb_variant_generates_real_rounds():
    pkg = fact_or_fake.build_package(seed="test-cfb-fof-1", variant="CFB_GAME_RESULT_FACT_OR_FAKE", round_count=10)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Fact or Fake (CFB)"
    true_count = sum(1 for r in pkg["rounds"] if r["_is_true"])
    false_count = sum(1 for r in pkg["rounds"] if not r["_is_true"])
    assert true_count > 0 and false_count > 0
    for r in pkg["rounds"]:
        assert "SPORTSDATAVERSE_CFB" in r["_notes"]
        assert " beat " in r["statement"]


def test_nfl_variant_unaffected():
    pkg = fact_or_fake.build_package(seed="test-nfl-fof-regress", variant="NFL_DRAFT_FACT_OR_FAKE", round_count=6)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Fact or Fake"


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="FACT_OR_FAKE", variant="CFB_GAME_RESULT_FACT_OR_FAKE")
    assert r["round_id"]
    assert "statement" in r["view"]


def test_public_mode_registered_and_dispatches():
    assert "fact_or_fake_cfb_game" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["fact_or_fake_cfb_game"]
    assert entry["taxonomy_id"] == "FACT_OR_FAKE"
    assert entry["variant"] == "CFB_GAME_RESULT_FACT_OR_FAKE"
    assert entry["competition"] == "CFB"


def test_public_round_real_fetch_and_submit_roundtrip():
    r = public_mechanics.start_public_round(mode="fact_or_fake_cfb_game")
    assert r["round_id"]
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice": "TRUE"})
    assert "correct" in result["result"]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_GAME_RESULT_FACT_OR_FAKE" in mechanic_engine.VARIANTS["FACT_OR_FAKE"]
    assert mechanic_engine.VARIANTS["FACT_OR_FAKE"]["CFB_GAME_RESULT_FACT_OR_FAKE"]["competition"] == "CFB"


def test_safety_check_reports_both_leagues():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = fact_or_fake.safety_check(c)
    finally:
        c.close()
    assert "draft_facts" in result
    assert "cfb_games_canonical" in result
