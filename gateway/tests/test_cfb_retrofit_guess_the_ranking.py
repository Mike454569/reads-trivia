"""CFB retrofit pass (user request: "I want all these formats to be NFL
and CFB based not just nfl... for the formats already on the app also")
-- CFB_CAREER_PASSING_YARDS_RANKING, the fourth CFB variant added to an
already-live NFL-only format.

Self-contained real top-15 CFB career passing yards query (does NOT reuse
leaderboard_climb.py's fetcher -- that format is protected from an
earlier duplicate-audit pass). Built on cfb_player_season_stats_real +
cfb_roster_seasons_real.position='QB'.
"""
import pytest

from tools.director_v04 import guess_the_ranking
from tools.director_v02 import mechanic_engine, registry
from gateway.services import creator, public_mechanics


def test_cfb_variant_registered():
    assert "CFB_CAREER_PASSING_YARDS_RANKING" in guess_the_ranking.VARIANTS
    assert "NFL_CAREER_PASSING_YARDS_RANKING" in guess_the_ranking.VARIANTS  # unchanged


def test_cfb_variant_generates_real_rounds():
    pkg = guess_the_ranking.build_package(seed="test-cfb-ranking-1", variant="CFB_CAREER_PASSING_YARDS_RANKING", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Guess the Ranking (CFB)"
    for r in pkg["rounds"]:
        assert len(set(o["label"] for o in r["options"])) == 4
        assert r["_answer_item_id"] in [o["item_id"] for o in r["options"]]
        assert "SPORTSDATAVERSE_CFB" in r["_notes"]


def test_nfl_variant_unaffected():
    pkg = guess_the_ranking.build_package(seed="test-nfl-ranking-regression", variant="NFL_CAREER_PASSING_YARDS_RANKING", round_count=8)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["game_title"] == "Guess the Ranking"
    for r in pkg["rounds"]:
        assert "NFLVERSE_DATA" in r["_notes"]


def test_cfb_ladder_is_real_and_tie_free():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        ladder = guess_the_ranking._fetch_cfb_ladder(c)
    finally:
        c.close()
    assert len(ladder) >= 4
    values = [r["value"] for r in ladder]
    assert len(set(values)) == len(values)  # no ties
    assert values == sorted(values, reverse=True)  # real descending order


def test_generate_direct_real_pipeline():
    r = creator.generate_direct(taxonomy_id="GUESS_THE_RANKING", variant="CFB_CAREER_PASSING_YARDS_RANKING")
    assert r["round_id"]
    assert len(r["view"]["options"]) == 4


def test_public_mode_registered_and_dispatches():
    assert "guess_the_ranking_cfb" in public_mechanics.PUBLIC_MECHANIC_MODES
    entry = public_mechanics.PUBLIC_MECHANIC_MODES["guess_the_ranking_cfb"]
    assert entry["taxonomy_id"] == "GUESS_THE_RANKING"
    assert entry["variant"] == "CFB_CAREER_PASSING_YARDS_RANKING"
    assert entry["competition"] == "CFB"


def test_public_round_real_fetch_and_submit_roundtrip():
    r = public_mechanics.start_public_round(mode="guess_the_ranking_cfb")
    assert r["round_id"]
    options = r["view"]["options"]
    assert len(options) == 4
    result = public_mechanics.submit_public_round(round_id=r["round_id"], submission={"choice_item_id": options[0]["item_id"]})
    assert "correct" in result["result"]
    assert result["result"]["canonical_answer"] in [o["label"] for o in options]


def test_mechanic_engine_variants_dict_has_cfb_entry():
    assert "CFB_CAREER_PASSING_YARDS_RANKING" in mechanic_engine.VARIANTS["GUESS_THE_RANKING"]
    assert mechanic_engine.VARIANTS["GUESS_THE_RANKING"]["CFB_CAREER_PASSING_YARDS_RANKING"]["competition"] == "CFB"


def test_safety_check_reports_both_leagues():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = guess_the_ranking.safety_check(c)
    finally:
        c.close()
    assert "player_season_stats" in result
    assert "cfb_player_season_stats_real" in result
    assert result["cfb_player_season_stats_real"]["source_id"] == "SPORTSDATAVERSE_CFB"
