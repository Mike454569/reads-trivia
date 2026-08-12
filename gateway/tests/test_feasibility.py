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


# --- feasibility-logic correction: "position + college, names hidden" ------
# A real bug this pass fixed: the plain college-phrased lineup request above
# must keep working exactly as before (names-based, SUPPORTED_WITH_LIMITATIONS)
# -- but a request that ALSO explicitly asks for names to be hidden must never
# silently fall back to that names-based capability. It must independently
# measure the real, certified NFL<->CFB identity bridge and report the truth.

def test_names_hidden_college_lineup_is_missing_data_not_silent_fallback():
    r = feasibility.assess(
        "Guess the NFL team from the colleges of the players on its offense, by position, with names hidden."
    )
    assert r["support_status"] == "MISSING_DATA"
    # Never silently resolves to the names-based capability.
    assert r["capability"] is None
    assert "cfb_nfl_identity_bridge_certified" in r["reason"]
    assert "never silently substituted with player names" in r["reason"]


def test_names_hidden_college_lineup_reason_has_real_live_numbers():
    r = feasibility.assess("Make a game with the position and college of each player, but hide the names.")
    assert r["support_status"] == "MISSING_DATA"
    # The exact real numbers measured this pass -- if the bridge is ever
    # enriched further, this test (not a hardcoded claim in feasibility.py
    # itself) is what should start failing, which is the correct signal to
    # re-measure rather than a stale string quietly staying "true" forever.
    assert "0 of 415" in r["reason"]
    assert "only 6" in r["reason"]


def test_plain_college_lineup_request_unaffected_by_hidden_names_check():
    # No "hidden"/"hide"/"anonymous"/"no names" signal -- must NOT be
    # swept into the names-hidden MISSING_DATA path.
    r = feasibility.assess(
        "Make a game where I guess the NFL team from its starting offense by position, using the colleges."
    )
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP"


def test_bare_college_request_gets_updated_honest_reason_not_stale_claim():
    # No lineup/position/nfl/team framing at all -- falls all the way
    # through to NO_MATCH and then the generic KNOWN_MISSING_DATA_SIGNALS
    # entry (a phrase with "nfl"/"team" would instead hit the NEEDS_
    # CLARIFICATION -> UNKNOWN path before ever reaching that fallback).
    # The reason must no longer claim college data is entirely absent (it
    # isn't, since the bridge hardening).
    r = feasibility.assess("Make me a game about which college each player attended.")
    assert r["support_status"] == "MISSING_DATA"
    assert "cfb_nfl_identity_bridge_certified" in r["reason"]
    assert "not reliably present" not in r["reason"]  # the old, now-false claim


def test_lineup_college_coverage_measures_live_against_real_bridge():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import lineup as lineup_adapter

    c = engine.connect()
    try:
        coverage = lineup_adapter.lineup_college_coverage(c)
    finally:
        c.close()

    assert coverage["bridge_table"] == "cfb_nfl_identity_bridge_certified"
    assert coverage["bridge_entries"] > 2000  # real bridge, not the old ~124-row one
    assert coverage["total_candidate_team_seasons"] == 415
    assert coverage["min_required_for_support"] == 20
    # Real measured state as of this pass -- genuinely insufficient.
    assert coverage["full_lineup_college_coverage"] < coverage["min_required_for_support"]
    assert coverage["sufficient"] is False
    assert set(coverage["per_slot_hit_counts"]) == {"QB", "RB", "WR", "TE", "OL"}


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
