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


def test_understood_but_unsupported_for_mixed_request():
    r = feasibility.assess("Give me a game where I guess both a QB's team and his favorite food.")
    assert r["support_status"] == "UNDERSTOOD_BUT_UNSUPPORTED"


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
