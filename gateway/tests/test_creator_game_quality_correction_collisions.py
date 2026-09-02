"""Creator/Game Quality Correction pass -- the 6 collision-prone routing
prompts explicitly named in this pass's own brief. Each one has a real,
plausible WRONG capability it could silently fall into if a broader,
earlier-checked keyword pattern swallowed it first (a lineup/team-of-season
match, a generic game-winner match, Weekly Pick'em, or a downgraded
single-school "which school did he attend" match). Verified directly
against the live mock translator before writing these assertions -- every
one already routes correctly; this locks that behavior in as a permanent
regression guard, not a fix in itself.
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


def _assert_routes_to(request_text: str, domain: str, predicate: str, *, expected_answer_type: str | None = None):
    from tools.director_v02 import feasibility, registry

    r = feasibility.assess(request_text)
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS", r
    cap = r["capability"]
    assert cap["domain"] == domain, f"expected domain {domain!r}, got {cap['domain']!r} for {request_text!r}"
    assert cap["relationship_predicate"] == predicate, (
        f"expected predicate {predicate!r}, got {cap['relationship_predicate']!r} for {request_text!r}"
    )
    if expected_answer_type is not None:
        reg_entry = registry.CAPABILITY_REGISTRY[("guess", domain, predicate)]
        assert reg_entry["answer_type"] == expected_answer_type


def test_collision_01_all_pro_answers_with_player_not_team():
    """Must NOT become Player + Season -> Team."""
    _assert_routes_to(
        "Give me an NFL player and season who was All-Pro and make me guess the player.",
        "NFL_ALL_PRO", "SELECTED_ALL_PRO", expected_answer_type="player",
    )


def test_collision_02_coordinator_answers_with_coach_not_lineup_or_team():
    """Must NOT become Starting Lineup or guess-the-team -- 'team' + 'offense'
    + 'season' is exactly the phrase shape a lineup/offense-of-season match
    could otherwise swallow."""
    _assert_routes_to(
        "Give me an NFL team, offense, and season and make me guess the coordinator.",
        "NFL_OFFENSIVE_COORDINATOR", "COORDINATED_OFFENSE", expected_answer_type="coach",
    )


def test_collision_03_first_touchdown_scorer_answers_with_player_not_won_game():
    """Must NOT become Guess the Winner (NFL_GAME_RESULT/WON_GAME)."""
    _assert_routes_to(
        "Give me an NFL game and make me guess the first touchdown scorer.",
        "NFL_SCORING_PLAY", "FIRST_TOUCHDOWN_SCORER", expected_answer_type="player",
    )


def test_collision_04_cfb_rb_comparison_not_weekly_pickem_or_no_match():
    """Must NOT become Weekly Pick'em (a same-week signal alone is not a
    matchup-pick request) or NO_MATCH."""
    _assert_routes_to(
        "Give me two CFB RBs from the same week and make me choose who had the bigger day.",
        "CFB_STAT_COMPARISON", "RUSHING_COMPARISON", expected_answer_type="player",
    )
    # And it's a true 2-option comparison, not 4-way multiple choice.
    from tools.director_v02 import pipeline
    pkg = pipeline.run(
        "Give me two CFB RBs from the same week and make me choose who had the bigger day.",
        provider="mock", seed="collision-04-rb-compare", question_count_override=5,
    )
    assert pkg["qa_status"] == "PASSED"
    for q in pkg["questions"]:
        assert len(q["options"]) == 2


def test_collision_05_ranked_upset_not_generic_game_result_or_no_match():
    """Must NOT become generic NFL/CFB_GAME_RESULT trivia or NO_MATCH."""
    _assert_routes_to(
        "Make me a game about a ranked college team getting upset.",
        "CFB_UPSET", "RANKING_UPSET", expected_answer_type="school",
    )


def test_collision_06_transfer_path_preserves_ordered_school_path_not_single_school():
    """Must preserve BOTH real qualifiers: 'later made the NFL' and an
    ORDERED multi-school path -- must NOT downgrade to the plain
    single-school 'which school did he attend' capability (CFB_TRANSFER/
    ATTENDED_COLLEGE), even though both nominally involve 'college'."""
    _assert_routes_to(
        "Give me a transfer player who later made the NFL and make me guess his college path.",
        "CFB_TRANSFER_PATH", "ORDERED_PATH_NFL_BRIDGED", expected_answer_type="ordered_path",
    )
