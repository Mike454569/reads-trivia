"""Real defects found and fixed during the final Creator pipeline audit
(post Phase 7B). Each test reproduces the exact failure mode found, not a
synthetic case -- the phrasing/behavior here is what actually broke.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_super_bowl_default_question_count_is_clamped_to_capability_bounds():
    """Real bug: the translator's own default question_count (25, used
    whenever no explicit number is in the request text) exceeded
    NFL_SUPER_BOWL/WON_CHAMPIONSHIP's real max_question_count (24, the
    exact size of its resolved candidate pool) -- so the single most
    natural phrasing of a fully real, working request failed validator.py's
    bounds check and reported UNKNOWN. A real capability, unreachable by
    its own default phrasing."""
    from tools.director_v02 import translator as translator_mod, feasibility

    t = translator_mod.translate("Who won a real Super Bowl?", provider="mock")
    assert t["translation_status"] == "TRANSLATED"
    assert t["spec"]["domain"] == "NFL_SUPER_BOWL"
    assert t["spec"]["question_count"] == 24  # clamped down from the translator's own default of 25

    f = feasibility.assess("Who won a real Super Bowl?", provider="mock")
    assert f["support_status"] in ("SUPPORTED", "SUPPORTED_WITH_LIMITATIONS")


def test_question_count_clamp_never_fires_for_unregistered_specs():
    """The clamp only touches specs that resolve to a REAL registered
    capability -- it must never invent bounds for a schema-valid-but-
    unregistered concept (that stays validator.py's job, via
    UNDERSTOOD_BUT_UNSUPPORTED)."""
    from tools.director_v02.providers.mock import _clamp_question_count_to_capability_bounds

    spec = {"mechanic": "guess", "domain": "NOT_A_REAL_DOMAIN", "relationship_predicate": "NOT_REAL", "question_count": 25}
    result = _clamp_question_count_to_capability_bounds(dict(spec))
    assert result["question_count"] == 25  # untouched


def test_college_football_phrase_does_not_trigger_college_attendance_fallback():
    """Real bug: "college football" is the SPORT NAME, not a claim about a
    player's college attendance -- but the bare word-overlap check in
    feasibility.py's _missing_data_reason() fired on the word "college"
    inside "college football" regardless of context, showing a completely
    unrelated draft_facts.college-coverage explanation for requests that
    had nothing to do with it (a real CFB game-result request, a real
    WEEKLY_PICKEM-shaped request)."""
    from tools.director_v02 import feasibility

    for text in (
        "Guess the winner of a real college football game.",
        "Give me a pick'em slate for this week's college football games.",
    ):
        f = feasibility.assess(text, provider="mock")
        assert "draft_facts" not in (f.get("reason") or ""), (text, f.get("reason"))
        assert "known college on record" not in (f.get("reason") or ""), (text, f.get("reason"))


def test_genuine_college_attendance_mention_still_gets_the_real_reason():
    """The fix above must not blunt the real, intentional fallback for a
    request that genuinely IS about college attendance -- only the sport-
    name phrase "college football" is stripped, not a standalone mention."""
    from tools.director_v02 import feasibility

    f = feasibility.assess("I want to know what college a drafted player went to.", provider="mock")
    assert f["support_status"] == "MISSING_DATA"
    assert "draft_facts" in (f.get("reason") or "")


def test_winner_noun_phrasing_translates_the_same_as_won_verb_phrasing():
    """Real gap: "guess the winner of a game" (a completely natural
    phrasing) didn't translate at all, because only the verb forms
    won/win were recognized, not the noun "winner"/"winners" -- for a
    capability (WON_GAME) confirmed real and working."""
    from tools.director_v02 import translator as translator_mod

    for text, expected_domain in (
        ("Guess the winner of a real college football game.", "CFB_GAME_RESULT"),
        ("Guess the winner of a real NFL game.", "NFL_GAME_RESULT"),
    ):
        t = translator_mod.translate(text, provider="mock")
        assert t["translation_status"] == "TRANSLATED", text
        assert t["spec"]["domain"] == expected_domain, text
        assert t["spec"]["relationship_predicate"] == "WON_GAME", text


def test_super_bowl_specific_phrasing_still_wins_over_the_broader_won_game_pattern():
    """Regression guard for the winner/winners addition above -- a request
    specifically about the Super Bowl must still route to
    NFL_SUPER_BOWL/WON_CHAMPIONSHIP, never get swallowed by the newly
    broadened WON_GAME pattern."""
    from tools.director_v02 import translator as translator_mod

    t = translator_mod.translate("Guess which team won the Super Bowl.", provider="mock")
    assert t["spec"]["domain"] == "NFL_SUPER_BOWL"
    assert t["spec"]["relationship_predicate"] == "WON_CHAMPIONSHIP"
