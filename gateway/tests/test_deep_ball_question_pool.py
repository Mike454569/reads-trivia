from pathlib import Path

from tools.director_v02 import registry
from tools.director_v04 import deep_trivia

ROOT = Path(__file__).resolve().parents[2]


def test_deep_ball_pool_has_real_breadth_and_no_team_record_filler():
    assert deep_trivia.capability_count() >= 25
    entries = deep_trivia._DEEP_CAPABILITIES
    domains = {row[1] for row in entries}
    predicates = {row[2] for row in entries}
    categories = {row[3] for row in entries}

    assert "NFL_GAME_BOXSCORE" in domains
    assert "CFB_GAME_BOXSCORE" in domains
    assert "NFL_SCORING_PLAY" in domains
    assert "NFL_DEFENSIVE_EVENT" in domains
    assert "CFB_RANKING" in domains
    assert "CFB_UPSET" in domains
    assert "CFB_TRANSFER" in domains
    assert "CFB_RIVALRY_TRIVIA" in domains
    assert "LED_LEAGUE_IN_STAT" in predicates
    assert "What was" not in " ".join(categories)
    assert "NFL Team Records" not in categories


def test_every_deep_ball_source_is_an_existing_certified_registry_capability():
    missing = []
    for mechanic, domain, predicate, _category, _filters in deep_trivia._DEEP_CAPABILITIES:
        cap = registry.CAPABILITY_REGISTRY.get((mechanic, domain, predicate))
        if not cap or not callable(cap.get("generate_fn")):
            missing.append((mechanic, domain, predicate))
    assert missing == []


def test_deep_ball_has_all_three_player_facing_lanes():
    lanes = {deep_trivia._bucket_for(row[1]) for row in deep_trivia._DEEP_CAPABILITIES}
    assert lanes == {"Game Day", "Season & Legacy", "College Chaos"}


def test_arcade_and_wager_use_deep_ball_pool_and_version_new_packages():
    roulette = (ROOT / "tools/director_v04/category_roulette.py").read_text()
    wager = (ROOT / "tools/director_v04/wager_mode.py").read_text()
    core = (ROOT / "tools/director_v04/strategy_arcade.py").read_text()
    wave3 = (ROOT / "tools/director_v04/strategy_arcade_wave3.py").read_text()
    wave4 = (ROOT / "tools/director_v04/strategy_arcade_wave4.py").read_text()
    wave5 = (ROOT / "tools/director_v04/strategy_arcade_wave5.py").read_text()

    assert "deep_trivia.generate_rounds" in roulette
    assert "deep_trivia.generate_rounds" in wager
    assert 'PACKAGE_SCHEMA_VERSION = "2.0"' in roulette
    assert 'PACKAGE_SCHEMA_VERSION = "2.0"' in wager
    assert 'PACKAGE_SCHEMA_VERSION = "2.0"' in core
    assert 'PACKAGE_SCHEMA_VERSION = "2.0"' in wave3
    assert 'PACKAGE_SCHEMA_VERSION="2.0"' in wave4
    assert 'PACKAGE_SCHEMA_VERSION="2.0"' in wave5

    for src in (core, wave3, wave4, wave5):
        assert "Game Day" in src
        assert "Season & Legacy" in src
        assert "College Chaos" in src
