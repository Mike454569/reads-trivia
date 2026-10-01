from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PICKEM = (ROOT / "pickem-ui.js").read_text()
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


def test_pickem_week_history_is_browsable_without_separate_store():
    assert "function changePickemWeek(nextWeek)" in PICKEM
    assert "function renderPickemWeekRail(s)" in PICKEM
    assert 'data-pickem-week="' in PICKEM
    assert "loadPickemView({ preserveScroll: true })" in PICKEM
    assert "[data-pickem-week]" in APP
    assert "changePickemWeek(t.dataset.pickemWeek)" in APP


def test_pickem_cards_render_broadcast_football_team_marks():
    assert "function pickemTeamVisual(league, teamName)" in PICKEM
    assert "pickem-football-badge" in PICKEM
    assert "pickem-rank-chip" in PICKEM
    assert "pickem-team-meta" in PICKEM
    assert ".pickem-football-badge" in CSS
    assert ".pickem-football-badge::before" in CSS
    assert ".pickem-rank-chip" in CSS


def test_pickem_cards_show_rank_record_and_full_team_name():
    assert "g.home_rank" in PICKEM and "g.away_rank" in PICKEM
    assert "g.home_record" in PICKEM and "g.away_record" in PICKEM
    assert "pickem-team-name" in PICKEM
    assert "pickem-team-meta" in PICKEM


def test_pickem_week_rail_is_mobile_scrollable():
    assert ".pickem-week-rail" in CSS
    assert "overflow-x:auto" in CSS
    assert "-webkit-overflow-scrolling:touch" in CSS
