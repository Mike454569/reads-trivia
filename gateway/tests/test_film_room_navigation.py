"""Player Experience pass (Part 6): Film Room promoted from a buried
home-screen discovery card to a first-class primary navigation tab
(Home | NFL | CFB | Film Room | Board), reachable exactly like NFL/CFB.

This project has no JavaScript test runner (a plain static site -- see
package.json's own description) and no Node.js is available in this
environment, so this file verifies the real, static index.html markup and
app.js's own routing logic directly (regex/string checks against the
actual shipped files, not a mock), the same evidence-over-assumption
standard this project's Python test suite already applies everywhere.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _index_html() -> str:
    return (REPO_ROOT / "index.html").read_text()


def _app_js() -> str:
    return (REPO_ROOT / "app.js").read_text()


def _nav_block(html: str, nav_id: str) -> str:
    m = re.search(r'<nav id="' + nav_id + r'"[^>]*>(.*?)</nav>', html, re.S)
    assert m, f"could not find <nav id=\"{nav_id}\"> in index.html"
    return m.group(1)


def test_top_nav_has_five_tabs_including_film_room_between_cfb_and_board():
    top_nav = _nav_block(_index_html(), "top-nav")
    buttons = re.findall(r"<button[^>]*>", top_nav)
    assert len(buttons) == 5, f"expected 5 top-nav buttons (Home/NFL/CFB/Film Room/Leaderboard), found {len(buttons)}"
    # Order matters: Film Room must sit between CFB and Leaderboard/Board,
    # not buried at the end or hidden before the league toggles.
    order = re.findall(r'data-(?:go|league-toggle)="([a-z]+)"', top_nav)
    assert order == ["home", "nfl", "cfb", "learn", "leaderboard"], order
    assert "Film Room" in top_nav


def test_bottom_nav_has_five_tabs_including_film_between_cfb_and_board():
    bottom_nav = _nav_block(_index_html(), "bottom-nav")
    buttons = re.findall(r"<button[^>]*>", bottom_nav)
    assert len(buttons) == 5, f"expected 5 bottom-nav buttons, found {len(buttons)}"
    order = re.findall(r'data-(?:go|league-toggle)="([a-z]+)"', bottom_nav)
    assert order == ["home", "nfl", "cfb", "learn", "leaderboard"], order
    labels = re.findall(r'<span class="bn-label">([^<]+)</span>', bottom_nav)
    assert labels == ["Home", "NFL", "CFB", "Film", "Board"], labels


def test_film_room_nav_button_routes_to_the_real_learn_screen():
    """data-go="learn" must resolve to the SAME real screen the existing
    Film Room discovery card already routes to (goToMode('learn') ->
    state.screen = 'learn' -> renderLearnScreen()) -- not a new, separate,
    disconnected route."""
    js = _app_js()
    assert "state.screen === 'learn'" in js
    assert "renderLearnScreen()" in js
    # The generic nav click handler resolves any [data-go] button through
    # goToMode(t.dataset.go) -- confirms "learn" needs no special-casing
    # to work as a direct nav target (it already works as a discovery-card
    # target via the exact same function).
    assert "goToMode(t.dataset.go)" in js


def test_nav_active_state_highlighting_covers_both_navs_generically():
    """navScreenMatch() must be applied to ALL [data-go] buttons in BOTH
    navs generically (not a hardcoded per-button list) so the new Film
    Room tab gets its active/selected state for free, matching Part 6's
    "selected state visually obvious" requirement."""
    js = _app_js()
    assert "'#top-nav [data-go], #bottom-nav [data-go]'" in js.replace('"', "'")


def test_film_room_discovery_card_still_exists_as_a_secondary_entry_point():
    """Promoting Film Room to primary nav doesn't require removing the
    existing home-screen discovery card -- both pointing at the same real
    screen is fine, not "burying" it."""
    js = _app_js()
    assert "discoverRowHtml('learn', 'book', 'The Film Room'" in js
