from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


def test_mode_logos_use_current_pictogram_system():
    assert "function modeLogoSvg(m)" in APP
    assert "function modeLogoVariant(m)" in APP
    assert "mode-mark-art" in APP
    assert "MODE_LOGO_CODE_OVERRIDES" not in APP
    assert "modeLogoCode(m)" not in APP


def test_flagship_modes_have_distinct_drawn_pictograms():
    for mode_id in (
        "quiz", "grid", "blitz", "speed", "silhouette", "iq",
        "legends", "higherLower", "playerClues", "cfbQuiz",
        "cfbGrid", "cfbBlitz", "cfbSpeed", "cfbIq",
        "cfbLegends", "cfbPlayerClues",
    ):
        assert f"id === '{mode_id}'" in APP or f"id === '{mode_id}' ||" in APP


def test_discovery_surfaces_use_shared_mode_marks():
    assert "modeMarkHtml(m,'md')" in APP
    assert "modeMarkHtml(m,'sm')" in APP
    assert "modeMarkHtml(r.mode,'sm')" in APP
    assert "mode-mark-art" in CSS
    assert "mode-logo-signature" in CSS


def test_generated_game_art_and_pictograms_can_coexist():
    assert "var READS_GAME_ART = {" in APP
    assert "gameArtHtml(m,'format-hub-card-art')" in APP
    assert "gameArtHtml(m,'mode-card-art')" in APP
    assert "Reads-owned game art system" in CSS
