"""v1.8, Part C -- tests for tools/director_v02/feasibility.py, the Game
Creator's support-status layer. Pure Python tests (no HTTP) since this
module has no Gateway route dependency by itself -- gateway/app.py's
POST /v1/creator/feasibility route (tested in test_creator.py) is a thin
wrapper that just calls assess() under require_admin.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.director_v02 import feasibility  # noqa: E402


def test_supported_no_limitations_for_draft():
    r = feasibility.assess("Make a guessing game where I see an NFL player and have to guess which NFL team drafted him.")
    assert r["support_status"] == "SUPPORTED"
    assert r["known_limitations"] == []
    assert r["capability"]["relationship_predicate"] == "DRAFTED_BY"


def test_supported_with_limitations_for_college_phrased_lineup_request():
    r = feasibility.assess(
        "Guess the NFL team from the colleges attended by the players on its offense, displayed by position."
    )
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert len(r["known_limitations"]) == 3
    assert any("not colleges" in lim for lim in r["known_limitations"])
    assert r["visual_template"] == "POSITION_LINEUP"


def test_supported_with_limitations_for_heisman_request():
    # Real gap found by actually testing the Creator against this exact
    # request during the CFB expansion operation: cfb_heisman_guess was
    # registered in CAPABILITY_REGISTRY (reachable via direct spec-based
    # generation) but had no translator keyword recognition at all, so this
    # request used to report NO_MATCH for a real, fully-certified
    # capability. Fixed in providers/mock.py; this test guards the fix.
    r = feasibility.assess("Make me a CFB Heisman guessing game.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "WON_HEISMAN"
    assert r["capability"]["domain"] == "CFB_HEISMAN"


def test_understood_but_unsupported_for_mixed_request():
    r = feasibility.assess("Give me a game where I guess both a QB's team and his favorite food.")
    assert r["support_status"] == "UNDERSTOOD_BUT_UNSUPPORTED"


def test_understood_but_unsupported_for_cfb_worded_clue_request():
    # Mission A5 fix: a CFB-worded player-from-clues request used to
    # silently resolve to SUPPORTED against the NFL-only IDENTIFY_FROM_CLUES
    # capability, since the translator never checked for a league signal at
    # all. Now competition-aware: an explicit "cfb" token, "college
    # football" phrase, or "college"/"colleges" word (with no contradicting
    # "nfl" token) reports the real, honest gap instead of silently
    # generating NFL content for a CFB-worded ask.
    for text in [
        "Make me a CFB game where I identify a player from his college career.",
        "Identify a CFB player from clues about his career.",
        "Give me a who am i game about a college football player.",
    ]:
        r = feasibility.assess(text)
        assert r["support_status"] == "UNDERSTOOD_BUT_UNSUPPORTED", text


def test_supported_for_nfl_clue_request_even_with_incidental_college_mention():
    # An explicit "nfl" token always wins over an incidental "college"
    # mention -- the request is genuinely about an NFL player whose bio
    # happens to reference college.
    r = feasibility.assess(
        "Identify a player from clues about his college career, he later played in the NFL."
    )
    assert r["support_status"] == "SUPPORTED"
    assert r["capability"]["domain"] == "NFL_PLAYER_IDENTITY"


def test_supported_for_bare_clue_request_with_no_league_signal():
    # No "nfl" and no "cfb"/"college" signal at all still defaults to the
    # NFL capability, consistent with every other pattern in the translator
    # (Draft/Championship/Lineup also default to NFL without requiring an
    # explicit "nfl" token).
    r = feasibility.assess("Give me a who am i game about a player.")
    assert r["support_status"] == "SUPPORTED"
    assert r["capability"]["domain"] == "NFL_PLAYER_IDENTITY"


def test_missing_data_for_salary_request():
    r = feasibility.assess("Make me a game about player salaries and contracts.")
    assert r["support_status"] == "MISSING_DATA"
    assert "salary" in r["reason"].lower() or "contract" in r["reason"].lower()


def test_missing_data_for_injury_request():
    r = feasibility.assess("Guess which players suffered a major injury each season.")
    assert r["support_status"] == "MISSING_DATA"


def test_unknown_for_gibberish():
    r = feasibility.assess("asdkjaslkdj random nonsense")
    assert r["support_status"] == "UNKNOWN"


def test_unknown_for_ambiguous_needs_clarification():
    r = feasibility.assess("Make me some NFL player trivia.")
    assert r["support_status"] == "UNKNOWN"
    assert r["clarifying_question"]


def test_every_status_is_in_the_official_vocabulary():
    requests = [
        "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him.",
        "Guess the NFL team from the colleges attended by the players on its offense, displayed by position.",
        "Give me a game where I guess both a QB's team and his favorite food.",
        "Make me a game about player salaries and contracts.",
        "asdkjaslkdj random nonsense",
    ]
    for req in requests:
        r = feasibility.assess(req)
        assert r["support_status"] in feasibility.SUPPORT_STATUSES


def test_unsafe_status_is_mechanically_reachable_via_registry_flag(monkeypatch):
    # UNSAFE is not reachable through any registered capability today (Part C's
    # own module docstring) -- prove the enforcement path is real, not just
    # documentation, by actually flipping the flag on a real registry entry.
    from tools.director_v02 import registry
    key = ("guess", "NFL_DRAFT", "DRAFTED_BY")
    original = dict(registry.CAPABILITY_REGISTRY[key])
    registry.CAPABILITY_REGISTRY[key]["unsafe"] = True
    try:
        r = feasibility.assess("Make a guessing game where I see an NFL player and have to guess which NFL team drafted him.")
        assert r["support_status"] == "UNSAFE"
    finally:
        registry.CAPABILITY_REGISTRY[key] = original


def test_capability_summary_lists_all_five_registered_capabilities():
    summary = feasibility.list_capability_support_summary()
    assert len(summary) == 5
    for c in summary:
        assert c["support_status"] in ("SUPPORTED", "SUPPORTED_WITH_LIMITATIONS")
    lineup = next(c for c in summary if c["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP")
    assert lineup["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    heisman = next(c for c in summary if c["relationship_predicate"] == "WON_HEISMAN")
    assert heisman["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
