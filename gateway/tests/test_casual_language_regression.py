"""P0 Accuracy + Reliability Hardening pass (Section 9): permanent coverage
for the exact casual-phrasing regression list this pass was asked to
retest. Real users don't type formal (mechanic, domain, predicate) prose --
these are the specific slang/incomplete phrasings that previously failed
(NO_MATCH or a wrong route) and must keep working."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.director_v02.providers.mock import MockDeterministicTranslator  # noqa: E402

CASES = [
    ("Give me two RBs from the same CFB week and make me choose who had the bigger day.",
     "CFB_STAT_COMPARISON", None),
    ("Who got the first tuddy?", "NFL_SCORING_PLAY", "FIRST_TOUCHDOWN_SCORER"),
    ("Give me some crazy CFB upsets.", "CFB_UPSET", None),
    ("Give me a team and make me guess the OC.", "NFL_OFFENSIVE_COORDINATOR", "COORDINATED_OFFENSE"),
    ("Make me an NFL Who Am I game.", "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"),
    ("Make me a CFB Who Am I game.", "CFB_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"),
]


@pytest.mark.parametrize("request_text,expected_domain,expected_predicate", CASES)
def test_casual_phrasing_translates_to_expected_capability(request_text, expected_domain, expected_predicate):
    translator = MockDeterministicTranslator()
    result = translator.translate(request_text)
    assert result["translation_status"] == "TRANSLATED", (
        f"{request_text!r} did not translate: {result.get('translator_notes')}"
    )
    spec = result["spec"]
    assert spec["domain"] == expected_domain, f"{request_text!r} routed to {spec['domain']!r}, expected {expected_domain!r}"
    if expected_predicate is not None:
        assert spec["relationship_predicate"] == expected_predicate, (
            f"{request_text!r} routed to {spec['relationship_predicate']!r}, expected {expected_predicate!r}"
        )
