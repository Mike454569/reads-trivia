from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


def test_app_wide_mode_logo_system_is_shared():
    assert "function modeMarkHtml(m, size)" in APP
    assert "function modeMarkFamily(m)" in APP
    assert "function modeLeagueFor(m)" in APP
    assert "modeMarkHtml(m, m.featured ? 'lg' : 'md')" in APP
    assert "modeMarkHtml(m, 'sm')" in APP


def test_game_cards_and_mode_sheet_use_premium_mode_marks():
    assert '<div class="mode-icon">' in APP
    assert 'class="msi-icon">' in APP
    assert ".mode-mark" in CSS
    assert ".mode-mark-lg" in CSS
    assert ".mode-mark-sm" in CSS


def test_mode_logo_families_have_distinct_visual_shapes():
    for cls in (
        ".mode-mark-grid",
        ".mode-mark-matchup",
        ".mode-mark-identity",
        ".mode-mark-speed",
        ".mode-mark-stats",
        ".mode-mark-timeline",
        ".mode-mark-tournament",
        ".mode-mark-roster",
    ):
        assert cls in CSS


def test_top_and_bottom_tabs_get_upgraded_icon_treatment():
    assert '#top-nav .nav-btn>.icon' in CSS
    assert '#bottom-nav .bn-icon' in CSS
    assert '#bottom-nav [data-league-toggle="nfl"] .bn-icon' in CSS
    assert '#bottom-nav [data-league-toggle="cfb"] .bn-icon' in CSS
    assert '#bottom-nav [data-go="learn"] .bn-icon' in CSS


def test_quick_action_and_film_cards_reuse_mode_mark_system():
    assert "continue-card-mode-mark" in APP
    assert "modeMarkHtml(pseudoMode, 'sm')" in APP
    assert "modeMarkHtml({id:s.id,icon:s.icon,title:s.title,league:'neutral'}, 'md')" in APP
