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


# --- position+college proof-game fix -----------------------------------
# A real identity-bridge expansion (tools/data_refresh/
# nfl_college_identity_bridge.py) made this exact request genuinely
# data-backed (68 real team-seasons, 5 skill positions, OL honestly
# excluded) -- these tests replace the earlier "correctly reports
# MISSING_DATA" pass, which is now stale (the whole point of that pass's
# own live-measurement design was to start reporting SUPPORTED automatically
# once real coverage existed, with no one needing to remember to update a
# hardcoded string -- see feasibility.py's own module docstring).

def test_names_hidden_college_lineup_is_supported_not_missing_data():
    r = feasibility.assess(
        "Guess the NFL team from the colleges of the players on its offense, by position, with names hidden."
    )
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    # Never silently resolves to the names-based capability.
    assert r["capability"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP_BY_COLLEGE"
    assert r["capability"]["domain"] == "NFL_OFFENSE_LINEUP_COLLEGE"
    assert any("offensive line is not shown" in lim.lower() for lim in r["known_limitations"])


def test_names_hidden_college_lineup_composition_example_matches_mission_prompt():
    # The mission's own verbatim composition example.
    r = feasibility.assess(
        "Guess the NFL team from the colleges its offensive players attended. Show position + college only. "
        "Hide player names."
    )
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP_BY_COLLEGE"


def test_plain_college_lineup_request_unaffected_by_hidden_names_check():
    # No "hidden"/"hide"/"anonymous"/"no names" signal -- must NOT be
    # swept into the names-hidden MISSING_DATA path.
    r = feasibility.assess(
        "Make a game where I guess the NFL team from its starting offense by position, using the colleges."
    )
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP"


def test_bare_college_request_gets_updated_honest_reason_not_stale_claim():
    # No "guess the college"/"guess the player" directional phrase, no
    # lineup/position/nfl/team framing -- falls all the way through to
    # NO_MATCH and then the generic college fallback (a phrase with
    # "nfl"/"team" would instead hit the NEEDS_CLARIFICATION -> UNKNOWN path
    # before ever reaching it). Stale-college-feasibility fix: this reason
    # is now LIVE-measured against draft_facts every call, never a hardcoded
    # sentence, and must no longer cite the OLD, unrelated
    # cfb_nfl_identity_bridge_certified 2,542-row figure this bug used to.
    r = feasibility.assess("Make me a game about which college each player attended.")
    assert r["support_status"] == "MISSING_DATA"
    assert "draft_facts" in r["reason"]
    assert "12914" in r["reason"]  # live count, not the old stale 2,542 citation
    assert "2,542" not in r["reason"]
    assert "not reliably present" not in r["reason"]  # the old, now-false claim


def test_guess_college_of_player_is_supported_not_missing_data():
    # Stale-college-feasibility fix: a general "guess the college of an NFL
    # player" request (no team/lineup framing) now resolves to a real,
    # registered capability built on the draft_facts.college backfill
    # (12,914 of 12,927 real draft rows), not the old hardcoded MISSING_DATA
    # fallback.
    r = feasibility.assess("Make me a game where I guess the college of an NFL player.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "ATTENDED_COLLEGE"
    assert r["capability"]["domain"] == "NFL_DRAFT"
    assert any("12,914" in lim for lim in r["known_limitations"])


def test_guess_school_from_players_drafted_there_is_supported():
    r = feasibility.assess("Guess the school from NFL players drafted from there.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "ATTENDED_COLLEGE"


def test_guess_player_from_college_and_round_routes_to_player_from_clues():
    # The reverse direction -- "guess the PLAYER from his college and draft
    # round" -- routes to the already-registered IDENTIFY_FROM_CLUES
    # capability, which already supports "college" and "draft_round" as
    # real clue types; it just wasn't reachable from this phrasing before.
    r = feasibility.assess("Guess the NFL player from his college and draft round.")
    assert r["support_status"] == "SUPPORTED"
    assert r["capability"]["relationship_predicate"] == "IDENTIFY_FROM_CLUES"


def test_college_lineup_hidden_names_request_still_uses_narrower_capability():
    # The fourth acceptance prompt -- must still resolve to the narrower,
    # season-lineup-specific capability, not the new general one.
    r = feasibility.assess("Guess the NFL team from skill-position colleges, hide names.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP_BY_COLLEGE"


def test_lineup_college_coverage_measures_live_against_real_bridge():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import lineup as lineup_adapter

    c = engine.connect()
    try:
        coverage = lineup_adapter.lineup_college_coverage(c)
    finally:
        c.close()

    assert coverage["bridge_table"] == "cfb_nfl_identity_bridge_certified"
    assert coverage["bridge_entries"] > 5000  # real, expanded bridge (2,542 -> 7,745+) plus ATTENDED_BEFORE_DRAFT
    # total_candidate_team_seasons now counts only actually-generatable
    # (evaluate()-passing) team-seasons, not the raw structural candidate
    # count -- "success is measured by playable lineups," not structural
    # completeness (see lineup_college_coverage()'s own docstring).
    assert coverage["total_candidate_team_seasons"] == 412
    assert coverage["min_required_for_support"] == 20
    # Full 10-position coverage remains a real, measured, structural
    # ceiling: OL college coverage is far too sparse (~10% per player) for
    # all 5 OL players on any one team-season to ever be simultaneously
    # certified.
    assert coverage["full_lineup_college_coverage"] == 0
    # Skill-positions-only coverage, however, is now genuinely sufficient --
    # the real, data-backed reason NFL_OFFENSE_LINEUP_COLLEGE is registered.
    assert coverage["skill_positions_only_college_coverage"] >= coverage["min_required_for_support"]
    assert coverage["sufficient"] is True
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


def test_capability_summary_lists_all_twelve_registered_capabilities():
    # 12, not 10, since the NFL Wikipedia history import registered two new
    # capabilities (WON_CHAMPIONSHIP/NFL_SUPER_BOWL, WON_AWARD/NFL_AWARDS).
    summary = feasibility.list_capability_support_summary()
    assert len(summary) == 12
    for c in summary:
        assert c["support_status"] in ("SUPPORTED", "SUPPORTED_WITH_LIMITATIONS")
    lineup = next(c for c in summary if c["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP")
    assert lineup["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    lineup_college = next(c for c in summary if c["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP_BY_COLLEGE")
    assert lineup_college["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert lineup_college["domain"] == "NFL_OFFENSE_LINEUP_COLLEGE"
    heisman = next(c for c in summary if c["relationship_predicate"] == "WON_HEISMAN")
    assert heisman["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    game_results = [c for c in summary if c["relationship_predicate"] == "WON_GAME"]
    assert len(game_results) == 2
    assert {c["domain"] for c in game_results} == {"NFL_GAME_RESULT", "CFB_GAME_RESULT"}
    boxscore = next(c for c in summary if c["relationship_predicate"] == "HAD_MORE_YARDS")
    assert boxscore["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert boxscore["domain"] == "NFL_GAME_BOXSCORE"


def test_supported_with_limitations_for_boxscore_request():
    r = feasibility.assess("Make me a game about which NFL team had more total yards in the box score.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "HAD_MORE_YARDS"
    assert r["capability"]["domain"] == "NFL_GAME_BOXSCORE"


def test_supported_with_limitations_for_nfl_game_result_request():
    r = feasibility.assess("Make me a game about who won real NFL games.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "WON_GAME"
    assert r["capability"]["domain"] == "NFL_GAME_RESULT"


def test_supported_with_limitations_for_cfb_game_result_request():
    r = feasibility.assess("Make me a CFB game about game results and scores.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["relationship_predicate"] == "WON_GAME"
    assert r["capability"]["domain"] == "CFB_GAME_RESULT"
