"""CFB retrofit pass (user request: "I want all these formats to be NFL
and CFB based not just nfl... for the formats already on the app also")
-- CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL, the second CFB variant added to
an already-live NFL-only format. Reuses higher_lower.py's own already-
certified `_cfb_items()` verbatim (cfb_standings.total_wins, FBS programs
only, CFBD_API_LIVE/SOURCE_BACKED) -- zero new data work.
"""
import pytest

from tools.director_v04 import king_of_the_hill
from tools.director_v02 import mechanic_engine, registry
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL" in king_of_the_hill.VARIANTS
    assert "NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL" in king_of_the_hill.VARIANTS  # unchanged


def test_cfb_variant_generates_real_items():
    pkg = king_of_the_hill.build_package(seed="test-cfb-koth-1", variant="CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["item_count"] == 16
    assert pkg["game_title"] == "King of the Hill (CFB)"
    values = [it["value"] for it in pkg["items"]]
    assert len(set(values)) == len(values)  # tie-exclusion by construction


def test_nfl_variant_unaffected():
    pkg = king_of_the_hill.build_package(seed="test-nfl-koth-regression", variant="NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL")
    assert pkg["qa_status"] == "PASSED"
    assert pkg["item_count"] == 16
    assert pkg["game_title"] == "King of the Hill"


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="KING_OF_THE_HILL", variant="CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL")
    assert r["round_id"]
    assert r["view"]["completed"] is False
    assert r["view"]["champion"]["label"]
    assert r["view"]["challenger"]["label"]


def test_public_mode_registered_and_dispatches():
    assert "king_of_the_hill_cfb" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["king_of_the_hill_cfb"]
    assert entry["taxonomy_id"] == "KING_OF_THE_HILL"
    assert entry["variant"] == "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL"
    assert entry["competition"] == "CFB"


def test_public_round_real_fetch_and_submit_roundtrip():
    r = public_mechanics.start_public_round(mode="king_of_the_hill_cfb")
    assert r["round_id"]
    assert r["view"]["champion"]["label"]
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice": "champion"})
    assert result["result"]["canonical_answer"] in ("champion", "challenger")
    assert isinstance(result["result"]["champion_value"], int)
    assert isinstance(result["result"]["challenger_value"], int)
    assert result["result"]["champion_value"] != result["result"]["challenger_value"]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL" in mechanic_engine.VARIANTS["KING_OF_THE_HILL"]
    assert mechanic_engine.VARIANTS["KING_OF_THE_HILL"]["CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL"]["competition"] == "CFB"


def test_safety_check_reports_both_leagues():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = king_of_the_hill.safety_check(c)
    finally:
        c.close()
    assert "season_standings" in result
    assert "cfb_standings" in result
