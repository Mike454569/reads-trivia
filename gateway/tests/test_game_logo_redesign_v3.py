from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


def test_game_logos_are_svg_pictograms_not_monograms():
    assert "function modeLogoSvg(m)" in APP
    assert "mode-mark-art" in APP
    assert "MODE_LOGO_CODE_OVERRIDES" not in APP
    assert "modeLogoCode(m)" not in APP


def test_flagship_games_have_custom_drawn_marks():
    for mode_id in (
        "quiz", "grid", "blitz", "speed", "silhouette", "iq",
        "legends", "higherLower", "playerClues", "draft_guess",
        "championship_guess", "lineup_guess", "learn", "daily", "h2h",
    ):
        assert f"id === '{mode_id}'" in APP or f"/{mode_id}/i" in APP


def test_long_tail_families_have_visual_motifs():
    for family in (
        "board", "roster", "survival", "strategy", "identify",
        "sequence", "stats", "timeline", "tournament", "speed",
    ):
        assert f"family === '{family}'" in APP


def test_old_text_badges_are_visually_retired():
    assert ".mode-mark-art" in CSS
    assert ".mode-logo-signature" in CSS
    assert ".mode-mark-code," in CSS
    assert "display:none!important" in CSS
