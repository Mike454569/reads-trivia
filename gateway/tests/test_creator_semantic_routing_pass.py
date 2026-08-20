"""Creator Semantic Routing + NFL/CFB Who Am I pass -- regression battery.

Covers the 13 real manual-failure prompts this pass was scoped around
(each reproduced from the actual real-user-language testing that found
them, not a synthetic paraphrase), plus the explicit routing-collision
tests, qualifier-preservation checks, and NFL/CFB domain-isolation checks
the pass's own completion standard requires. See tools/director_v02/
providers/mock.py's "Creator Semantic Routing + Who Am I pass" section and
tools/director_v04/cfb_player_from_clues.py for the real fixes/capability
these tests protect.
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


# ============================== the 13 real manual failures ==============================

def test_manual_failure_01_cfb_rankings_recognized_not_misrouted():
    """Creator Capability Completion pass: CFB_RANKING/RANKED_IN_POLL is now
    a real, GENERATION_VERIFIED capability -- this asserts the recognition
    the docstring's own name describes AND that it's no longer just
    recognized-but-unsupported."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me a game about college football rankings.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_RANKING"
    assert r["capability"]["relationship_predicate"] == "RANKED_IN_POLL"


def test_manual_failure_02_all_pro_routes_to_real_capability_not_team_of_season():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me guess which NFL player was First-Team All-Pro that season.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_ALL_PRO"
    assert r["capability"]["relationship_predicate"] == "SELECTED_ALL_PRO"


def test_manual_failure_03_offensive_coordinator_routes_correctly_not_lineup():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an NFL team and season and make me guess the offensive coordinator.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_OFFENSIVE_COORDINATOR"


def test_manual_failure_04_defensive_coordinator_routes_correctly_not_generic_clarification():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me guess the defensive coordinator for this NFL team.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_DEFENSIVE_COORDINATOR"


def test_manual_failure_05_first_touchdown_recognized_not_misrouted_to_won_game():
    """Creator Capability Completion pass: NFL_SCORING_PLAY/FIRST_TOUCHDOWN_SCORER
    is now real and GENERATION_VERIFIED -- the real protection this test
    guards (never silently downgraded to the unrelated WON_GAME capability)
    is asserted directly on the resolved domain now, not via capability=None."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an NFL game and make me guess who scored the first touchdown.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_SCORING_PLAY"
    assert r["capability"]["relationship_predicate"] == "FIRST_TOUCHDOWN_SCORER"


def test_manual_failure_06_cfb_same_week_stat_comparison_not_misrouted_to_weekly_pickem():
    """Creator Capability Completion pass: CFB_STAT_COMPARISON is now real
    and GENERATION_VERIFIED -- still asserts the original real protection
    (never silently routed to WEEKLY_PICKEM just because "week" appears)."""
    from gateway.services import creator
    r = creator.assess_feasibility(
        "Give me two college running backs from the same week and make me pick who rushed for more yards."
    )
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_STAT_COMPARISON"
    assert r["capability"].get("mechanic") != "WEEKLY_PICKEM"


def test_manual_failure_07_top_performer_not_misrouted_to_lineup():
    """Creator Capability Completion pass: NFL_GAME_LEADER is now real and
    GENERATION_VERIFIED -- still asserts the original real protection
    (never silently routed to the unrelated NFL_OFFENSE_LINEUP capability)."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me a team and game and make me guess their top offensive performer.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_GAME_LEADER"
    assert r["capability"]["domain"] != "NFL_OFFENSE_LINEUP"


def test_manual_failure_08_all_american_to_all_pro_composition_recognized_not_downgraded():
    """Creator Capability Completion pass: CROSS_LEAGUE_HONORS/
    ALL_AMERICAN_TO_ALL_PRO is now real and GENERATION_VERIFIED."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an All-American who later became an NFL All-Pro and make me guess the player.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CROSS_LEAGUE_HONORS"
    assert r["capability"]["relationship_predicate"] == "ALL_AMERICAN_TO_ALL_PRO"


def test_manual_failure_09_transfer_ordered_path_not_downgraded_to_plain_attended_college():
    """Creator Capability Completion pass: CFB_TRANSFER_PATH/
    ORDERED_PATH_NFL_BRIDGED is now real and GENERATION_VERIFIED -- still
    asserts the original real protection (the ORDERED relationship is the
    point, never silently downgraded to plain CFB_TRANSFER/ATTENDED_COLLEGE)."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me a transfer player who later made the NFL and make me guess his college path.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_TRANSFER_PATH"
    assert r["capability"]["relationship_predicate"] == "ORDERED_PATH_NFL_BRIDGED"


def test_manual_failure_10_all_pro_plus_college_composition_not_misleading_missing_data():
    """Creator Capability Completion pass: NFL_ALL_PRO_COLLEGE/
    ATTENDED_COLLEGE_ALL_PRO is now real and GENERATION_VERIFIED."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me guess which NFL All-Pro attended this college.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_ALL_PRO_COLLEGE"
    assert r["capability"]["relationship_predicate"] == "ATTENDED_COLLEGE_ALL_PRO"


def test_manual_failure_11_cfb_upsets_recognized_never_no_match():
    """Creator Capability Completion pass: CFB_UPSET (ranking + betting
    variants) is now real and GENERATION_VERIFIED. Generic "upsets" phrasing
    with no explicit betting signal resolves to the ranking-based definition."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me something about crazy college football upsets.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_UPSET"
    assert r["capability"]["relationship_predicate"] == "RANKING_UPSET"


def test_manual_failure_12_fuzzy_college_to_nfl_stardom_grounded_not_downgraded():
    """Creator Capability Completion pass: fuzzy "great in college / star in
    the NFL" language is now grounded in the real CROSS_LEAGUE_HONORS
    composition (All-American -> All-Pro), never a fabricated subjective
    "stardom" score."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me a game about dudes who were great in college and then became stars in the NFL.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CROSS_LEAGUE_HONORS"


def test_manual_failure_13_cfb_who_am_i_now_genuinely_supported():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Guess the CFB player from clues.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_PLAYER_IDENTITY"


# ============================== paraphrase coverage ==============================

@pytest.mark.parametrize("text", [
    "Who made first team AP that year?",
    "Give me an All-Pro game.",
    "Which dude was first-team All-Pro?",
    "Who got first-team honors that season?",
])
def test_all_pro_paraphrases_route_correctly(text):
    from tools.director_v02 import feasibility
    r = feasibility.assess(text)
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS", text
    assert r["capability"]["domain"] == "NFL_ALL_PRO", text


@pytest.mark.parametrize("text", [
    "Who was a Pro Bowler this year?",
    "Give me a Pro Bowl game.",
    "Which player made the pro bowl?",
])
def test_pro_bowl_paraphrases_route_correctly(text):
    from tools.director_v02 import feasibility
    r = feasibility.assess(text)
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS", text
    assert r["capability"]["domain"] == "NFL_PRO_BOWL", text


@pytest.mark.parametrize("text", [
    "Who's in the Hall of Fame?",
    "Give me a Hall of Famer guessing game.",
    "Which player got inducted into Canton?",
])
def test_hall_of_fame_paraphrases_route_correctly(text):
    from tools.director_v02 import feasibility
    r = feasibility.assess(text)
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS", text
    assert r["capability"]["domain"] == "NFL_HALL_OF_FAME", text


@pytest.mark.parametrize("text,expected_domain", [
    ("Who's the OC for this team?", "NFL_OFFENSIVE_COORDINATOR"),
    ("Guess the offensive coordinator.", "NFL_OFFENSIVE_COORDINATOR"),
    ("Who's the DC for this team?", "NFL_DEFENSIVE_COORDINATOR"),
    ("Guess the defensive coordinator.", "NFL_DEFENSIVE_COORDINATOR"),
])
def test_coordinator_paraphrases_route_to_correct_side(text, expected_domain):
    from tools.director_v02 import feasibility
    r = feasibility.assess(text)
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS", text
    assert r["capability"]["domain"] == expected_domain, text


def test_coordinator_with_no_side_signal_asks_for_clarification():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Guess the coordinator for this NFL team.")
    assert r["support_status"] == "UNKNOWN"
    assert r["clarifying_question"]


# ============================== routing collision tests (Section 26) ==============================

def test_collision_all_pro_beats_player_season_team():
    """Prompt contains player + season + All-Pro -> All-Pro must win."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Guess which NFL player, in this season, was named All-Pro.")
    assert r["capability"]["domain"] == "NFL_ALL_PRO"


def test_collision_coordinator_beats_lineup():
    """Prompt contains team + offense + season + coordinator -> coordinator must win."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an NFL team's offense this season and make me guess their offensive coordinator.")
    assert r["capability"]["domain"] == "NFL_OFFENSIVE_COORDINATOR"


def test_collision_pbp_scoring_beats_game_result():
    """Prompt contains NFL + game + touchdown + first scorer -> PBP scoring
    intent must win (never silently answered as WON_GAME). Creator
    Capability Completion pass: NFL_SCORING_PLAY is now real -- the
    collision protection is asserted directly against WON_GAME now."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("In this NFL game, guess who scored the first touchdown.")
    assert r["capability"]["domain"] == "NFL_SCORING_PLAY"
    assert r["capability"]["relationship_predicate"] != "WON_GAME"
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"


def test_collision_stat_comparison_beats_weekly_pickem():
    """Prompt contains CFB + week + running backs + rushing yards + more ->
    stat comparison must win (never silently routed to Weekly Pick'em)."""
    from gateway.services import creator
    r = creator.assess_feasibility(
        "CFB, same week, two running backs, who had more rushing yards?"
    )
    assert r.get("capability") is None or r["capability"].get("mechanic") != "WEEKLY_PICKEM"


def test_collision_upset_beats_generic_game_result():
    """Prompt contains CFB + game + upset + ranked -> upset/ranking intent
    must win (never silently answered as plain WON_GAME). Creator
    Capability Completion pass: CFB_UPSET is now real -- the collision
    protection is asserted directly against WON_GAME now."""
    from tools.director_v02 import feasibility
    r = feasibility.assess("CFB game, a real ranked-team upset -- make me guess it.")
    assert r["capability"]["domain"] == "CFB_UPSET"
    assert r["capability"]["relationship_predicate"] != "WON_GAME"
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"


def test_collision_cfb_who_am_i_never_routes_to_nfl():
    from tools.director_v02 import feasibility
    r = feasibility.assess("College football who am I -- guess the player from clues.")
    assert r["capability"]["domain"] == "CFB_PLAYER_IDENTITY"


def test_collision_nfl_who_am_i_stays_nfl_even_with_incidental_college_mention():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Identify this NFL player from clues, including which college he attended.")
    assert r["capability"]["domain"] == "NFL_PLAYER_IDENTITY"


# ============================== qualifier preservation (Section 18) ==============================

def test_first_team_qualifier_preserved_in_translator_notes():
    from tools.director_v02.providers import mock as mock_translator
    result = mock_translator.MockDeterministicTranslator().translate(
        "Guess which player was First-Team All-Pro."
    )
    assert result["translation_status"] == "TRANSLATED"
    assert "FIRST_TEAM" in result["translator_notes"] or "First-Team" in result["translator_notes"]


def test_offensive_side_qualifier_not_confused_with_defensive():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Guess the offensive coordinator for this team.")
    assert r["capability"]["relationship_predicate"] == "COORDINATED_OFFENSE"


# ============================== NFL/CFB domain isolation (Section 33) ==============================

def test_nfl_all_pro_capability_never_uses_cfb_only_tables():
    from tools.director_v02 import registry
    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_ALL_PRO", "SELECTED_ALL_PRO")]
    assert cap["competition_id"] == "NFL"


def test_cfb_who_am_i_capability_is_cfb_only():
    from tools.director_v02 import registry
    cap = registry.CAPABILITY_REGISTRY[("identify_player_from_clues", "CFB_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES")]
    assert cap["competition_id"] == "CFB"


def test_cfb_who_am_i_generation_never_yields_nfl_players():
    """Real, direct check: every generated CFB Who Am I puzzle's answer
    must resolve back to the real cfb_roster_seasons_real/
    canonical_cfb_players universe this module builds from, never an NFL
    canonical_players id (the two identity tables use disjoint id schemes,
    confirmed here by re-resolving each answer against the real universe)."""
    from tools.director_v04 import cfb_player_from_clues
    from tools.quiz_export import engine

    pkg = cfb_player_from_clues.build_package(seed="domain-isolation-check", target_count=10)
    assert pkg["qa_status"] == "PASSED"

    c = engine.connect()
    try:
        _facts, _indexes, universe_ids = cfb_player_from_clues.build_universe(c)
    finally:
        c.close()

    for p in pkg["puzzles"]:
        assert p["answer"]["player_id"] in universe_ids


# ============================== end-to-end playability (Section 31) ==============================

@pytest.mark.parametrize("request_text,expected_domain", [
    ("Make me guess which NFL player was First-Team All-Pro that season.", "NFL_ALL_PRO"),
    ("Which player was selected to the Pro Bowl?", "NFL_PRO_BOWL"),
    ("Which player was inducted into the Hall of Fame?", "NFL_HALL_OF_FAME"),
    ("Give me an NFL team and season and make me guess the offensive coordinator.", "NFL_OFFENSIVE_COORDINATOR"),
    ("Make me guess the defensive coordinator for this NFL team.", "NFL_DEFENSIVE_COORDINATOR"),
])
def test_new_guess_capabilities_generate_real_playable_questions(request_text, expected_domain):
    from gateway.services import creator
    result = creator.generate_for_review(request_text=request_text, puzzle_count=3, difficulty="any", seed=f"e2e-{expected_domain}")
    assert result.get("qa_status") == "PASSED", result
    questions = result.get("questions", [])
    assert len(questions) == 3
    for q in questions:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert 0 <= q["correctIndex"] <= 3


def test_cfb_who_am_i_generates_real_playable_puzzle():
    from gateway.services import creator
    result = creator.generate_for_review(request_text="Guess the CFB player from clues.", puzzle_count=3, difficulty="any", seed="e2e-cfb-wai")
    assert result.get("qa_status") == "PASSED", result
    puzzles = result.get("puzzles", [])
    assert len(puzzles) == 3
    for p in puzzles:
        assert 3 <= len(p["clues"]) <= 5
        answer_name = p["answer"]["display_name"].lower()
        for clue in p["clues"]:
            assert answer_name not in clue["display_text"].lower(), "answer leaked into a clue"
