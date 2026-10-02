from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_live_football_does_not_fail_all_when_one_league_stalls():
    src = (ROOT / "live-football-ui.js").read_text(encoding="utf-8")
    assert "Showing the league data that loaded." in src
    assert "liveFootballUpcomingGames()" in src
    assert "liveFootballUpcomingCardHtml" in src
    assert "Promise.all([nfl, cfb])" in src


def test_home_shows_upcoming_games_when_no_finals_exist():
    src = (ROOT / "live-football-ui.js").read_text(encoding="utf-8")
    assert "upcoming.length ? '<div class=\"live-final-grid\"'" in src
    assert "Coming up" in src


def test_recent_activity_has_local_fallback_instead_of_disappearing():
    src = (ROOT / "app.js").read_text(encoding="utf-8")
    assert "readsRecentActivityLocal" in src
    assert "Recent activity is temporarily offline." in src
    assert "No recent plays yet. Finish a game and it will show up here." in src


def test_pickem_service_has_short_lived_package_cache():
    src = (ROOT / "gateway" / "services" / "public_pickem.py").read_text(encoding="utf-8")
    assert "_PICKEM_PACKAGE_CACHE_TTL_SECONDS = 60.0" in src
    assert "_package_cache_get(cache_key)" in src
    assert "_package_cache_put(cache_key, package)" in src
