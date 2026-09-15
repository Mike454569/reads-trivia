"""40-Format Expansion pass -- real tests for tools/director_v04/
nl_new_taxonomy_bridge.py and its wiring into gateway/services/creator.py
(assess_feasibility()/generate_for_review()). Covers the user's own
explicit example phrases for the 6 new taxonomies' 10 format names, plus
regression guards proving the new bridge never shadows any pre-existing
request (checked BEFORE this bridge in the documented fixed order:
nl_schedule_bridge -> nl_mechanic_bridge -> nl_new_taxonomy_bridge -> normal
translator pipeline).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = __import__("pytest").mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_detect_matches_every_new_format_casual_phrase():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    cases = {
        "make me a connection grid game": ("GRID_CONSTRAINT_BOARD", "CONNECTION_GRID"),
        "give me a perfect drive game": ("DRIVE_PROGRESSION", "PERFECT_DRIVE"),
        "a goal line stand challenge, four downs": ("DRIVE_PROGRESSION", "GOAL_LINE_STAND"),
        "build an offense with 2010s players": ("ROSTER_BUILD", "LINEUP_BUILDER"),
        "auction draft, give everyone a budget": ("ROSTER_BUILD", "AUCTION_DRAFT"),
        "salary cap challenge": ("ROSTER_BUILD", "CAP_CHALLENGE"),
        "knockout tournament with 16 teams": ("KNOCKOUT_BRACKET", "KNOCKOUT_TOURNAMENT"),
        "six degrees of separation, connect these two players": ("RELATIONSHIP_CHAIN", "SIX_DEGREES"),
        "chain reaction game": ("RELATIONSHIP_CHAIN", "CHAIN_REACTION"),
        "choose your path trivia": ("BRANCH_STATE", "CHOOSE_YOUR_PATH"),
    }
    for phrase, (taxonomy_id, format_id) in cases.items():
        result = bridge.detect(phrase)
        assert result is not None, f"expected a match for {phrase!r}"
        assert result["taxonomy_id"] == taxonomy_id, phrase
        assert result["format"] == format_id, phrase


def test_knockout_tournament_size_signal():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    assert bridge.detect("knockout tournament with 16 teams")["variant"] == "NFL_TEAM_SEASON_WINS_KNOCKOUT_16"
    assert bridge.detect("elimination bracket")["variant"] == "NFL_TEAM_SEASON_WINS_KNOCKOUT_4"
    assert bridge.detect("cfb knockout tournament, sixteen teams")["variant"] == "CFB_TEAM_SEASON_WINS_KNOCKOUT_16"


def test_detect_returns_none_for_unrelated_text():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    for phrase in ["make me an NFL draft game", "make me a bracket game", "who is this team's coach",
                   "guess the college of this NFL player", "match these draft picks to their teams"]:
        assert bridge.detect(phrase) is None, phrase


def test_creator_assess_feasibility_routes_new_formats_end_to_end():
    from gateway.services import creator

    r = creator.assess_feasibility("make me a connection grid game")
    assert r["support_status"] == "SUPPORTED"
    assert r["taxonomy_id"] == "GRID_CONSTRAINT_BOARD"
    assert r["format_id"] == "CONNECTION_GRID"


def test_creator_generate_for_review_produces_a_real_playable_package():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="give me a perfect drive game", puzzle_count=None, difficulty=None, seed="pytest-drive-bridge",
    )
    assert r["taxonomy_id"] == "DRIVE_PROGRESSION"
    assert r["format_id"] == "PERFECT_DRIVE"
    assert "round_id" in r and r["round_id"]
    assert r["view"]["prompt"]


def test_new_taxonomy_bridge_never_shadows_a_plain_draft_request():
    """Real regression guard: the whole point of checking this bridge AFTER
    nl_mechanic_bridge and the normal pipeline's own routing is that an
    ordinary, already-working request must resolve exactly as it always
    has -- this is the same shadow-bug class this session already hit and
    fixed twice for mock.py (CFB_2026_HEAD_COACH)."""
    from gateway.services import creator

    r = creator.assess_feasibility("make me a game where I guess which team drafted a player")
    assert r["support_status"] == "SUPPORTED"
    assert r["capability"]["domain"] == "NFL_DRAFT"
    assert r.get("taxonomy_id") is None


def test_new_taxonomy_bridge_never_shadows_a_plain_bracket_request():
    from gateway.services import creator

    r = creator.assess_feasibility("make me a bracket game")
    assert r["taxonomy_id"] == "COMPARISON_BRACKET"
    assert r["format_id"] == "BRACKET_TREE"


# --- GUESS_THE_SEASON (15-Format Expansion Part 2, format #2) -------------

def test_detect_guess_the_season_real_phrasing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    for phrase in ["guess the season", "guess the year", "what season was this",
                   "what year is this", "name the season", "identify the year"]:
        r = bridge.detect(phrase)
        assert r is not None, f"expected a match for {phrase!r}"
        assert r["taxonomy_id"] == "GUESS_THE_SEASON"
        assert r["format"] == "GUESS_THE_SEASON"
        assert r["variant"] == "NFL_SUPER_BOWL_SEASON"


def test_guess_the_season_creator_generate_for_review_is_a_real_playable_round():
    """Real end-to-end proof through the same admin Creator entry point a
    live request actually uses -- catches the class of bug the SB_MVP
    off-by-one fix + the GGP17 package-id allowlist fix were both found
    through (neither surfaced when calling build_package() directly)."""
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="guess the season", puzzle_count=None, difficulty=None, seed="pytest-season-bridge",
    )
    assert r["taxonomy_id"] == "GUESS_THE_SEASON"
    assert r["format_id"] == "GUESS_THE_SEASON"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP17:")
    assert len(r["view"]["clues"]) >= 2


def test_new_taxonomy_bridge_never_shadows_a_plain_guess_request():
    """Real ordinary 'guess' requests unrelated to seasons must keep routing
    exactly as they always have -- this bridge is checked last in the fixed
    order and must never accidentally swallow an unrelated phrase."""
    from gateway.services import creator

    r = creator.assess_feasibility("make me a game where I guess which team drafted a player")
    assert r.get("taxonomy_id") is None


# --- HEAD_TO_HEAD_DUEL / PAIRWISE_COMPARE (15-Format Expansion Part 2, format #3) ---

def test_detect_head_to_head_duel_real_phrasing_and_variant_routing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    r = bridge.detect("give me a head to head duel")
    assert r is not None
    assert r["taxonomy_id"] == "PAIRWISE_COMPARE"
    assert r["format"] == "HEAD_TO_HEAD_DUEL"
    assert r["variant"] == "NFL_SEASON_RUSHING_YARDS_DUEL"

    r2 = bridge.detect("head to head duel with quarterbacks, who threw more passing touchdowns")
    assert r2["variant"] == "NFL_CAREER_PASSING_TD_DUEL"

    r3 = bridge.detect("college football head to head duel, who had more rushing yards")
    assert r3["variant"] == "CFB_CAREER_RUSHING_YARDS_DUEL"

    r4 = bridge.detect("1v1 duel")
    assert r4["taxonomy_id"] == "PAIRWISE_COMPARE"


def test_head_to_head_duel_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="head to head duel", puzzle_count=None, difficulty=None, seed="pytest-duel-bridge",
    )
    assert r["taxonomy_id"] == "PAIRWISE_COMPARE"
    assert r["format_id"] == "HEAD_TO_HEAD_DUEL"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP18:")
    assert r["view"]["entity_a"]["label"] and r["view"]["entity_b"]["label"]


def test_new_taxonomy_bridge_never_shadows_a_plain_guess_request_with_duel_bridge_active():
    """Regression guard for the new HEAD_TO_HEAD_DUEL bridge specifically --
    ordinary 2-option guess requests (no real duel/head-to-head signal) must
    keep routing exactly as they always have."""
    from gateway.services import creator

    r = creator.assess_feasibility("make me a game where I guess which team drafted a player")
    assert r.get("taxonomy_id") is None


# --- BEST_OF_SEVEN_DUEL / PAIRWISE_COMPARE (15-Format Expansion Part 2, format #4) ---

def test_detect_best_of_seven_duel_real_phrasing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    for phrase in ["give me a best of seven duel", "best of 7 duel between two quarterbacks",
                   "best of seven"]:
        r = bridge.detect(phrase)
        assert r is not None, f"expected a match for {phrase!r}"
        assert r["taxonomy_id"] == "PAIRWISE_COMPARE"
        assert r["format"] == "BEST_OF_SEVEN_DUEL"
        assert r["variant"] == "NFL_CAREER_QB_BEST_OF_SEVEN"


def test_best_of_seven_duel_checked_before_head_to_head_duel_since_both_contain_the_word_duel():
    """Real ordering regression guard: 'best of seven duel' contains the
    bare word 'duel', which would otherwise match the plain
    HEAD_TO_HEAD_DUEL pattern first if checked out of order."""
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    r = bridge.detect("give me a best of seven duel")
    assert r["format"] == "BEST_OF_SEVEN_DUEL"

    r2 = bridge.detect("give me a head to head duel")
    assert r2["format"] == "HEAD_TO_HEAD_DUEL"


def test_best_of_seven_duel_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="give me a best of seven duel", puzzle_count=None, difficulty=None, seed="pytest-b7-bridge",
    )
    assert r["taxonomy_id"] == "PAIRWISE_COMPARE"
    assert r["format_id"] == "BEST_OF_SEVEN_DUEL"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP18:")
    assert r["view"]["round_count"] >= 3
    assert r["view"]["entity_a"]["label"] and r["view"]["entity_b"]["label"]


# --- PICK_THE_IMPOSTOR (15-Format Expansion Part 2, format #5) -----------

def test_detect_pick_the_impostor_real_phrasing_and_league_routing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    r = bridge.detect("give me a pick the impostor game")
    assert r is not None
    assert r["taxonomy_id"] == "PICK_THE_IMPOSTOR"
    assert r["format"] == "PICK_THE_IMPOSTOR"
    assert r["variant"] == "NFL_TEAM_ROSTER_IMPOSTOR"

    r2 = bridge.detect("which one doesn't belong on this real roster")
    assert r2["taxonomy_id"] == "PICK_THE_IMPOSTOR"

    r3 = bridge.detect("college football, which one wasn't really on this team")
    assert r3["variant"] == "CFB_SCHOOL_ROSTER_IMPOSTOR"


def test_pick_the_impostor_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="pick the impostor", puzzle_count=None, difficulty=None, seed="pytest-impostor-bridge",
    )
    assert r["taxonomy_id"] == "PICK_THE_IMPOSTOR"
    assert r["format_id"] == "PICK_THE_IMPOSTOR"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP19:")
    assert len(r["view"]["items"]) == 4


def test_pick_the_impostor_is_never_shadowed_by_weekly_pickem_despite_the_word_pick():
    """Real regression guard for a real bug caught live this pass:
    nl_schedule_bridge (checked BEFORE this module in the fixed pipeline
    order) has a has_slate_or_league + bare 'pick(s)' fallback for
    WEEKLY_PICKEM -- "pick the impostor" contains "pick", and naming a
    league (as any real request for this format naturally would) used to
    satisfy that fallback and misroute here before this bridge ever ran.
    Fixed with a real _IMPOSTOR_EXCLUSION_RE in nl_schedule_bridge.py."""
    from gateway.services import creator

    r = creator.assess_feasibility("Give me a pick the impostor game with real NFL players.")
    assert r["support_status"] == "SUPPORTED"
    assert r["taxonomy_id"] == "PICK_THE_IMPOSTOR"


# --- UNIQUE_ONE_OUT (15-Format Expansion Part 2, format #6) --------------

def test_detect_unique_one_out_real_phrasing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    for phrase in ["give me a unique one out game", "odd one out"]:
        r = bridge.detect(phrase)
        assert r is not None, f"expected a match for {phrase!r}"
        assert r["taxonomy_id"] == "PICK_THE_IMPOSTOR"
        assert r["format"] == "UNIQUE_ONE_OUT"
        assert r["variant"] == "NFL_DRAFT_CLASS_ONE_OUT"


def test_unique_one_out_checked_before_pick_the_impostor_generic_pattern():
    """Real ordering guard: UNIQUE_ONE_OUT's own trigger must resolve to
    its own format, not fall through to PICK_THE_IMPOSTOR's more generic
    roster-membership variant just because both share this taxonomy."""
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    r = bridge.detect("give me a unique one out game")
    assert r["format"] == "UNIQUE_ONE_OUT"

    r2 = bridge.detect("pick the impostor")
    assert r2["format"] == "PICK_THE_IMPOSTOR"


def test_unique_one_out_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="give me a unique one out game", puzzle_count=None, difficulty=None,
        seed="pytest-oneout-bridge",
    )
    assert r["taxonomy_id"] == "PICK_THE_IMPOSTOR"
    assert r["format_id"] == "UNIQUE_ONE_OUT"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP19:")
    assert len(r["view"]["items"]) == 4


# --- MISSING_PIECE (15-Format Expansion Part 2, format #7) ---------------

def test_detect_missing_piece_real_phrasing_and_league_routing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    r = bridge.detect("give me a missing piece game")
    assert r is not None
    assert r["taxonomy_id"] == "MISSING_PIECE"
    assert r["format"] == "MISSING_PIECE"
    assert r["variant"] == "NFL_TEAM_ROSTER_MISSING_PIECE"

    r2 = bridge.detect("who's missing from this real roster")
    assert r2["taxonomy_id"] == "MISSING_PIECE"

    r3 = bridge.detect("college football, missing piece game")
    assert r3["variant"] == "CFB_SCHOOL_ROSTER_MISSING_PIECE"


def test_missing_piece_never_shadowed_by_pick_the_impostor_or_weekly_pickem():
    """Real ordering + cross-module regression guard: MISSING_PIECE's own
    trigger must resolve to its own format (not PICK_THE_IMPOSTOR's, even
    though both are real "group membership" games), and -- since this
    format's natural phrasing has no bare "pick" in it -- must not need
    the same WEEKLY_PICKEM exclusion PICK_THE_IMPOSTOR itself needed."""
    from gateway.services import creator

    r = creator.assess_feasibility("Give me a missing piece game with real NFL players.")
    assert r["support_status"] == "SUPPORTED"
    assert r["taxonomy_id"] == "MISSING_PIECE"


def test_missing_piece_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="give me a missing piece game", puzzle_count=None, difficulty=None,
        seed="pytest-missing-bridge",
    )
    assert r["taxonomy_id"] == "MISSING_PIECE"
    assert r["format_id"] == "MISSING_PIECE"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP20:")
    assert len(r["view"]["group_members"]) == 3
    assert len(r["view"]["items"]) == 4


# --- BEFORE_AFTER (15-Format Expansion Part 2, format #8) ----------------

def test_detect_before_after_real_phrasing_and_league_routing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    r = bridge.detect("give me a before and after game")
    assert r is not None
    assert r["taxonomy_id"] == "BEFORE_AFTER"
    assert r["format"] == "BEFORE_AFTER"
    assert r["variant"] == "NFL_TEAM_CHANGE_BEFORE_AFTER"

    r2 = bridge.detect("which team did they play for first")
    assert r2["taxonomy_id"] == "BEFORE_AFTER"

    r3 = bridge.detect("college football, before and after game")
    assert r3["variant"] == "CFB_SCHOOL_TRANSFER_BEFORE_AFTER"


def test_before_after_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="give me a before and after game", puzzle_count=None, difficulty=None,
        seed="pytest-before-after-bridge",
    )
    assert r["taxonomy_id"] == "BEFORE_AFTER"
    assert r["format_id"] == "BEFORE_AFTER"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP21:")
    assert r["view"]["entity_a"]["label"] and r["view"]["entity_b"]["label"]


def test_before_after_never_shadowed_by_any_prior_bridge():
    """Real ordering regression guard: an ordinary request unrelated to
    before/after career questions must keep routing exactly as it always
    has -- this bridge is checked last in the fixed order."""
    from gateway.services import creator

    r = creator.assess_feasibility("make me a game where I guess which team drafted a player")
    assert r.get("taxonomy_id") is None


# --- CAREER_PATH (15-Format Expansion Part 2, format #10) ----------------

def test_detect_career_path_real_phrasing_and_league_routing():
    from tools.director_v04 import nl_new_taxonomy_bridge as bridge

    r = bridge.detect("career path game")
    assert r is not None
    assert r["taxonomy_id"] == "CAREER_PATH"
    assert r["format"] == "CAREER_PATH"
    assert r["variant"] == "NFL_PLAYER_CAREER_PATH_IDENTIFY"

    r2 = bridge.detect("which player had this path")
    assert r2["taxonomy_id"] == "CAREER_PATH"

    r3 = bridge.detect("college football, career path game")
    assert r3["variant"] == "CFB_PLAYER_CAREER_PATH_IDENTIFY"


def test_career_path_never_confused_with_map_the_career():
    """Real cross-format regression guard: CAREER_PATH (identify the
    player from an already-ordered path) and MAP_THE_CAREER (order the
    real teams for a named player) must never resolve to each other --
    they live in different bridges (nl_new_taxonomy_bridge.py vs.
    nl_mechanic_bridge.py) and have deliberately non-overlapping trigger
    phrases."""
    from tools.director_v04 import nl_new_taxonomy_bridge as new_bridge
    from tools.director_v04 import nl_mechanic_bridge as mechanic_bridge

    r = new_bridge.detect("career path game")
    assert r["taxonomy_id"] == "CAREER_PATH"
    assert mechanic_bridge.detect("career path game") is None

    r2 = mechanic_bridge.detect("map the career game")
    assert r2["format"] == "MAP_THE_CAREER"
    assert new_bridge.detect("map the career game") is None


def test_career_path_creator_generate_for_review_is_a_real_playable_round():
    from gateway.services import creator

    r = creator.generate_for_review(
        request_text="career path game", puzzle_count=None, difficulty=None, seed="pytest-career-path-bridge",
    )
    assert r["taxonomy_id"] == "CAREER_PATH"
    assert r["format_id"] == "CAREER_PATH"
    assert "round_id" in r and r["round_id"]
    assert r["round_id"].startswith("GGP22:")
    assert len(r["view"]["path"]) == 3
    assert len(r["view"]["options"]) == 4
