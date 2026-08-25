"""Universal Data Reuse + Missing Data pass (follow-up audit): a real
routing gap found while auditing "game -> player stats/PBP" reuse --
"who led the game in rushing yards" / "who had more rushing yards in the
game" fell through to NFL_GAME_BOXSCORE/HAD_MORE_YARDS (team TOTAL yards,
any category combined) instead of NFL_GAME_LEADER/RUSHING_LEADER (the
specific single-game rushing leader the request actually named). Not a
false fact -- the generated HAD_MORE_YARDS question honestly says "total
yards" -- but a real semantic misroute: the generated relationship didn't
match what was asked, the same class of bug Section 8's semantic-
fulfillment checks exist to catch."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.director_v02.providers.mock import MockDeterministicTranslator  # noqa: E402

CATEGORY_CASES = [
    ("who led the game in rushing yards", "NFL_GAME_LEADER", "RUSHING_LEADER"),
    ("who had more rushing yards in the game", "NFL_GAME_LEADER", "RUSHING_LEADER"),
    ("who led the game in passing yards", "NFL_GAME_LEADER", "PASSING_LEADER"),
    ("who had more receiving yards in the game", "NFL_GAME_LEADER", "RECEIVING_LEADER"),
]


@pytest.mark.parametrize("request_text,expected_domain,expected_predicate", CATEGORY_CASES)
def test_category_specific_yards_request_routes_to_game_leader_not_total_yards(
    request_text, expected_domain, expected_predicate
):
    translator = MockDeterministicTranslator()
    result = translator.translate(request_text)
    assert result["translation_status"] == "TRANSLATED"
    spec = result["spec"]
    assert spec["domain"] == expected_domain
    assert spec["relationship_predicate"] == expected_predicate


def test_genuine_total_yards_request_still_routes_to_boxscore():
    """The fix must stay scoped to rushing/passing/receiving-specific
    phrasing -- a real "total yards" request must keep routing to
    NFL_GAME_BOXSCORE/HAD_MORE_YARDS, not get swept into the leader
    pattern."""
    translator = MockDeterministicTranslator()
    result = translator.translate("which team had more total yards in the game")
    assert result["translation_status"] == "TRANSLATED"
    assert result["spec"]["domain"] == "NFL_GAME_BOXSCORE"
    assert result["spec"]["relationship_predicate"] == "HAD_MORE_YARDS"
