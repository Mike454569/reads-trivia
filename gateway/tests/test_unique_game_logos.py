from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


def test_mode_logos_have_per_game_codes_and_variants():
    assert "var MODE_LOGO_CODE_OVERRIDES" in APP
    assert "function modeLogoCode(m)" in APP
    assert "function modeLogoVariant(m)" in APP
    assert "mode-mark-v" in APP
    assert "mode-mark-code" in APP
    assert "mode-mark-corner" in APP


def test_flagship_modes_have_distinct_logo_codes():
    for snippet in (
        "quiz:'QZ'",
        "grid:'3X3'",
        "blitz:'BLZ'",
        "speed:'SPD'",
        "silhouette:'ID'",
        "iq:'IQ'",
        "legends:'17-0'",
        "higherLower:'H/L'",
        "playerClues:'WHO'",
        "cfbLegends:'12-0'",
        "cfbPlayerClues:'CWHO'",
    ):
        assert snippet in APP


def test_discovery_surfaces_use_shared_mode_marks_not_raw_icons():
    assert "modeMarkHtml(m,'md')" in APP
    assert "modeMarkHtml(m,'sm')" in APP
    assert "modeMarkHtml(r.mode,'sm')" in APP
    assert "icon(m.icon||'football')" not in APP
    assert "icon(r.mode.icon||'football')" not in APP


def test_logo_variant_styles_exist():
    for i in range(12):
        assert f".mode-mark-v{i}" in CSS
    assert ".mode-mark-code" in CSS
    assert ".mode-mark-corner" in CSS
    assert ".format-mini-mark" in CSS
