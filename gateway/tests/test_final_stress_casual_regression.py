"""Final Player-Facing Stress Test pass: real casual/slang routing gaps
found while stress-testing the live Creator with natural, sloppy wording.
Each case here previously fell through to NO_MATCH or a generic
MISSING_DATA fallback despite a real, registered capability existing for
the concept."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.director_v02.providers.mock import MockDeterministicTranslator  # noqa: E402

CASES = [
    # "stud"/"balled" as real casual synonyms for "star"/"played great" --
    # previously only "star"/"great" matched, silently missing this whole
    # phrasing family down to a generic MISSING_DATA fallback.
    ("give me a college stud who became an nfl star", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_ALL_PRO"),
    ("guy who balled in college then balled in the league", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_ALL_PRO"),
    # "picked the QB off" (a noun phrase, not just a pronoun, between
    # "picked" and "off") is equally common real phrasing as "picked it off".
    ("who picked the qb off", "NFL_DEFENSIVE_EVENT", "RECORDED_INTERCEPTION"),
    # "whoami" (no spaces) / "who-am-i" (hyphenated) are the same request
    # as "who am i" -- the plain-word tokenizer can't split "whoami" into
    # separate tokens at all, so word-set matching alone never catches it.
    ("nfl whoami", "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"),
    ("cfb whoami game", "CFB_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"),
    # "went off more" is the same real "who performed better" same-week
    # comparison intent as "balled out harder" -- one of this pass's own
    # given prompts used this exact phrasing.
    ("give me two rbs from the same week and tell me who went off more", "CFB_STAT_COMPARISON", None),
    # "led this game in rushing" (no "yards" word, "this" not "the") is the
    # same real single-game rushing-leader concept as "led the game in
    # rushing yards".
    ("who led this game in rushing", "NFL_GAME_LEADER", "RUSHING_LEADER"),
    # Product Growth + Real User Testing pass: "upsetty" (a real casual
    # adjective built from "upset") wasn't in the exact-word upset-signal
    # set, so a request combining a rankings word with it fell through to
    # the plain rankings capability instead of the upset one the "but make
    # it upsetty" qualifier clearly asked for.
    ("cfb rankings but make it upsetty", "CFB_UPSET", "RANKING_UPSET"),
]


@pytest.mark.parametrize("request_text,expected_domain,expected_predicate", CASES)
def test_casual_phrasing_routes_to_expected_capability(request_text, expected_domain, expected_predicate):
    translator = MockDeterministicTranslator()
    result = translator.translate(request_text)
    assert result["translation_status"] == "TRANSLATED", (
        f"{request_text!r} did not translate: {result.get('translator_notes')}"
    )
    spec = result["spec"]
    assert spec["domain"] == expected_domain, f"{request_text!r} routed to {spec['domain']!r}, expected {expected_domain!r}"
    if expected_predicate is not None:
        assert spec["relationship_predicate"] == expected_predicate
