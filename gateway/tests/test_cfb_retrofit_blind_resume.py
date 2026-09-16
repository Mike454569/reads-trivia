"""CFB retrofit pass (user request: "I want all these formats to be NFL
and CFB based not just nfl... for the formats already on the app also")
-- CFB_QB_CAREER_BLIND_RESUME, the third CFB variant added to an already-
live NFL-only format. Built on cfb_player_season_stats_real +
cfb_roster_seasons_real.position='QB'.

Real, disclosed data-safety finding: cfb_player_season_stats_real has no
"games played" column at all -- uses real career COMPLETIONS instead as
the 4th resume stat (never fabricated, never mislabeled as games in the
client). r.completions (not r.games) is how the client renderer tells the
two variants apart.
"""
import pytest

from tools.director_v04 import blind_resume
from tools.director_v02 import mechanic_engine, registry
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_QB_CAREER_BLIND_RESUME" in blind_resume.VARIANTS
    assert "NFL_QB_CAREER_BLIND_RESUME" in blind_resume.VARIANTS  # unchanged


def test_cfb_variant_generates_real_rounds():
    pkg = blind_resume.build_package(seed="test-cfb-resume-1", variant="CFB_QB_CAREER_BLIND_RESUME", round_count=7)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["round_count"] == 7
    assert pkg["game_title"] == "Blind Resume (CFB)"
    for r in pkg["rounds"]:
        assert "completions" in r["resume"]
        assert "games" not in r["resume"]  # never claim a field that doesn't exist for CFB
        assert len(set(o["label"] for o in r["options"])) == 4
        assert "SPORTSDATAVERSE_CFB" in r["_notes"]
        assert "career completions" in r["_notes"]


def test_nfl_variant_unaffected():
    pkg = blind_resume.build_package(seed="test-nfl-resume-regression", variant="NFL_QB_CAREER_BLIND_RESUME", round_count=7)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Blind Resume"
    for r in pkg["rounds"]:
        assert "games" in r["resume"]
        assert "completions" not in r["resume"]
        assert "NFLVERSE_DATA" in r["_notes"]


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="BLIND_RESUME", variant="CFB_QB_CAREER_BLIND_RESUME")
    assert r["round_id"]
    assert "completions" in r["view"]["resume"]
    assert len(r["view"]["options"]) == 4


def test_public_mode_registered_and_dispatches():
    assert "blind_resume_cfb_qb" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["blind_resume_cfb_qb"]
    assert entry["taxonomy_id"] == "BLIND_RESUME"
    assert entry["variant"] == "CFB_QB_CAREER_BLIND_RESUME"
    assert entry["competition"] == "CFB"


def test_public_round_real_fetch_and_submit_roundtrip():
    r = public_mechanics.start_public_round(mode="blind_resume_cfb_qb")
    assert r["round_id"]
    assert "completions" in r["view"]["resume"]
    options = r["view"]["options"]
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]
    assert result["result"]["canonical_answer"] in [o["label"] for o in options]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_QB_CAREER_BLIND_RESUME" in mechanic_engine.VARIANTS["BLIND_RESUME"]
    assert mechanic_engine.VARIANTS["BLIND_RESUME"]["CFB_QB_CAREER_BLIND_RESUME"]["competition"] == "CFB"


def test_safety_check_reports_both_leagues():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = blind_resume.safety_check(c)
    finally:
        c.close()
    assert "player_season_stats" in result
    assert "cfb_player_season_stats_real" in result
    assert result["cfb_player_season_stats_real"]["source_id"] == "SPORTSDATAVERSE_CFB"
