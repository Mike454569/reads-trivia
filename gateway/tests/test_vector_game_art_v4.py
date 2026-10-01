from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


def test_game_cards_use_vector_art_not_raster_sprite_backgrounds():
    start = APP.index("function gameArtHtml(m, extraClass)")
    end = APP.index("var formatHubState", start)
    block = APP[start:end]
    assert "reads-game-art-vector" in block
    assert "modeMarkHtml(m,'xl')" in block
    assert "fetch(path" not in block
    assert "data:image/webp" not in block


def test_vector_logos_have_per_mode_fingerprint_detail():
    assert "vector-fingerprint-v1" in APP
    assert "mode-logo-fingerprint" in APP
    assert ".mode-logo-fingerprint" in CSS


def test_retina_vector_card_treatment_is_enabled():
    assert "Game art v4 — retina-safe vector treatment" in CSS
    assert ".mode-mark-xl" in CSS
    assert "shape-rendering:geometricPrecision" in CSS
    assert "background-image:none!important" in CSS
