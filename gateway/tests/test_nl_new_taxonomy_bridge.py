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
