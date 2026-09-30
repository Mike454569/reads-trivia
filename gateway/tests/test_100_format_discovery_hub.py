"""100-format Discovery Hub regression coverage."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")

def test_home_uses_single_100_format_discovery_hub():
    assert "formatDiscoveryHubHtml()" in APP
    home=APP[APP.index("function renderHome()"):APP.index("/* ============================== NFL/CFB mode picker")]
    assert "formatDiscoveryHubHtml()" in home
    assert "modeSectionHtml('nfl')" not in home
    assert "modeSectionHtml('cfb')" not in home

def test_hub_exposes_search_and_all_required_filters():
    assert 'id="format-hub-search"' in APP
    for hook in (
        "data-format-hub-league",
        "data-format-hub-family",
        "data-format-hub-difficulty",
        "data-format-hub-new",
        "data-format-hub-reset",
    ):
        assert hook in APP

def test_personalization_scores_unique_full_playable_catalog():
    assert "function allPlayableModesUnique()" in APP
    assert "var all = allPlayableModesUnique();" in APP
    assert "function formatHubRecommendationRows" in APP
    assert "getPersonalizationState().playEvents" in APP

def test_frontend_milestone_matches_machine_audit():
    from tools.director_v02.format_audit import audit_format_registry
    audit=audit_format_registry()
    assert audit["distinct_format_count"] == 100
    assert audit["target_gap"] == 0
    assert "var READS_DISTINCT_FORMAT_COUNT = 100;" in APP
    assert "100 Ways to Play Football" in APP

def test_hub_has_mobile_specific_layout():
    for selector in (
        ".format-hub-grid",
        ".format-hub-rec-row",
        ".format-hub-search",
        ".format-hub-scroll",
    ):
        assert selector in CSS
    assert "@media(max-width:640px)" in CSS
