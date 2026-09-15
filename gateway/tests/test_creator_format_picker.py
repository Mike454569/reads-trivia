"""Format Picker pass -- the Creator admin UI (creator-ui.js's own
CREATOR_FORMAT_CATALOG) now lists every real, already-shipped format as a
clickable row instead of requiring the admin to already know its exact
natural-language trigger phrase (the user's own reported gap: "I want it
to give me options ... without having to use a keyword or sum bs like
that"). 29 of the 32 rows call gateway.services.creator.generate_direct()
(POST /v1/creator/format/generate in production) with an EXPLICIT
taxonomy_id + variant -- no text, no regex bridge, no collision risk at
all. The remaining 3 rows (Weekly Pick'em / Fantasy Draft / Confidence
Pick) are schedule-driven and still use a real, proven natural-language
phrase (see generate_direct()'s own docstring for why those 3 are
deliberately excluded from the direct path).

This file keeps its own Python mirror of creator-ui.js's
CREATOR_FORMAT_CATALOG (there is no shared source of truth between JS and
Python in this codebase, same convention every other JS-side constant
here already follows) and is a regression guard, not new behavior: if a
future change ever breaks one of these taxonomy_id/variant pairs or one
of the 3 schedule-driven phrases, this test fails loudly instead of the
picker silently going dead for that row.
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

# Mirrors creator-ui.js's CREATOR_FORMAT_CATALOG entries that carry taxonomyId/variant.
CREATOR_FORMAT_CATALOG_DIRECT = [
    ("Matching", "MATCHING", "NFL_DRAFT_CLASS_MATCH"),
    ("Timeline Order", "SORTING_TIMELINE", "NFL_DRAFT_PICK_ORDER"),
    ("Stat Ladder", "SORTING_TIMELINE", "NFL_CAREER_PASSING_TD_LADDER"),
    ("Map the Career", "SORTING_TIMELINE", "NFL_PLAYER_CAREER_TEAM_ORDER"),
    ("Head to Head Duel", "PAIRWISE_COMPARE", "NFL_CAREER_PASSING_TD_DUEL"),
    ("Best of Seven Duel", "PAIRWISE_COMPARE", "NFL_CAREER_QB_BEST_OF_SEVEN"),
    ("Leaderboard Climb", "LEADERBOARD_CLIMB", "NFL_CAREER_PASSING_YARDS_CLIMB"),
    ("Higher or Lower", "HIGHER_LOWER_STREAK", "NFL_TEAM_SEASON_WINS"),
    ("Comparison Bracket", "COMPARISON_BRACKET", "NFL_TEAM_SEASON_WINS_BRACKET"),
    ("Pick the Impostor", "PICK_THE_IMPOSTOR", "NFL_TEAM_ROSTER_IMPOSTOR"),
    ("Unique One Out", "PICK_THE_IMPOSTOR", "NFL_DRAFT_CLASS_ONE_OUT"),
    ("Missing Piece", "MISSING_PIECE", "NFL_TEAM_ROSTER_MISSING_PIECE"),
    ("Blind Resume", "BLIND_RESUME", "NFL_QB_CAREER_BLIND_RESUME"),
    ("Lineup Builder", "ROSTER_BUILD", "NFL_2010S_OFFENSE_BUILDER"),
    ("Auction Draft", "ROSTER_BUILD", "NFL_AUCTION_DRAFT"),
    ("Cap Challenge", "ROSTER_BUILD", "NFL_CAP_CHALLENGE"),
    ("Lineup Grid", "POSITION_LINEUP_GRID", "NFL_OFFENSE_LINEUP_COLLEGE_TEAM_ONLY"),
    ("Risk It", "RISK_IT", "NFL_DRAFT_RISK_IT"),
    ("Wager Mode", "WAGER_MODE", "WAGER_MODE_MIXED"),
    ("Knockout Tournament", "KNOCKOUT_BRACKET", "NFL_TEAM_SEASON_WINS_KNOCKOUT_16"),
    ("Elimination", "ELIMINATION_SURVIVAL", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL"),
    ("Choose Your Path", "BRANCH_STATE", "NFL_TOPIC_PATH"),
    ("Career Path", "CAREER_PATH", "NFL_PLAYER_CAREER_PATH_IDENTIFY"),
    ("Before & After", "BEFORE_AFTER", "NFL_TEAM_CHANGE_BEFORE_AFTER"),
    ("Guess the Season", "GUESS_THE_SEASON", "NFL_SUPER_BOWL_SEASON"),
    ("Connection Grid", "GRID_CONSTRAINT_BOARD", "NFL_TEAM_DRAFT_ROUND_GRID"),
    ("Six Degrees", "RELATIONSHIP_CHAIN", "CFB_SCHOOL_TO_NFL_TEAM_CHAIN"),
    ("Chain Reaction", "RELATIONSHIP_CHAIN", "CFB_SCHOOL_TO_NFL_TEAM_CHAIN"),
    ("Perfect Drive", "DRIVE_PROGRESSION", "NFL_DRAFT_PERFECT_DRIVE"),
    ("Goal Line Stand", "DRIVE_PROGRESSION", "NFL_DRAFT_GOAL_LINE_STAND"),
    ("Double or Nothing", "DOUBLE_OR_NOTHING", "NFL_DRAFT_DOUBLE_OR_NOTHING"),
    ("King of the Hill", "KING_OF_THE_HILL", "NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL"),
    ("Fact or Fake", "FACT_OR_FAKE", "NFL_DRAFT_FACT_OR_FAKE"),
    ("Guess the Ranking", "GUESS_THE_RANKING", "NFL_CAREER_PASSING_YARDS_RANKING"),
    ("Stat Target", "STAT_TARGET", "NFL_SEASON_RUSHING_YARDS_TARGET"),
    ("Reverse Trivia", "REVERSE_TRIVIA", "NFL_DRAFT_REVERSE_TRIVIA"),
    ("Three Strikes", "THREE_STRIKES", "NFL_DRAFT_THREE_STRIKES"),
    ("Mystery Roster", "MYSTERY_ROSTER", "NFL_TEAM_SEASON_MYSTERY_ROSTER"),
    ("Draft Pick Ladder", "DRAFT_PICK_LADDER", "NFL_DRAFT_PICK_LADDER"),
]

# The 3 schedule-driven rows that still use a real, proven NL phrase.
CREATOR_FORMAT_CATALOG_PHRASE = [
    ("Weekly Pick'em", "Give me the NFL weekly pick'em.", "WEEKLY_PICKEM"),
    ("Fantasy Draft", "Give me a fantasy draft with NFL players.", "LIVE_WEEKLY_FANTASY_DRAFT"),
    ("Confidence Pick", "Give me a confidence pick game for this week's NFL games.", "CONFIDENCE_PICK"),
]


def test_creator_format_catalog_has_no_duplicate_titles():
    titles = [row[0] for row in CREATOR_FORMAT_CATALOG_DIRECT] + [row[0] for row in CREATOR_FORMAT_CATALOG_PHRASE]
    assert len(titles) == len(set(titles)), "the picker would show two rows with the same title"


@pytest.mark.parametrize("title,taxonomy_id,variant", CREATOR_FORMAT_CATALOG_DIRECT)
def test_creator_format_picker_direct_entry_generates_a_real_playable_round(title, taxonomy_id, variant):
    from gateway.services import creator

    result = creator.generate_direct(taxonomy_id=taxonomy_id, variant=variant, seed=f"pytest-picker-{title}")
    assert result["taxonomy_id"] == taxonomy_id, (title, result)
    assert result.get("round_id"), (title, result)
    assert result.get("view") is not None, (title, result)


@pytest.mark.parametrize("title,phrase,expected_taxonomy", CREATOR_FORMAT_CATALOG_PHRASE)
def test_creator_format_picker_schedule_driven_phrase_resolves_to_intended_format(title, phrase, expected_taxonomy):
    from gateway.services import creator

    result = creator.assess_feasibility(phrase)
    assert result["support_status"] in ("SUPPORTED", "SUPPORTED_WITH_LIMITATIONS"), (title, phrase, result)
    assert result["taxonomy_id"] == expected_taxonomy, (title, phrase, result.get("taxonomy_id"))


def test_creator_format_picker_covers_every_real_taxonomy_id_except_the_flexible_translator_ones():
    """Every taxonomy_id mechanic_engine.py knows about should have at
    least one picker row -- otherwise it is real, generatable, and
    playable but still only reachable by an admin who already knows its
    exact phrase/identifiers, which is the exact gap this picker exists
    to close. Exactly two taxonomy_ids are deliberately exempt:
    MULTIPLE_CHOICE_SINGLE_FACT and PROGRESSIVE_CLUE_IDENTIFY are reached
    exclusively through the OLD flexible guess/identify_player_from_clues
    translator (no narrow-anchored NL bridge exists for either, and
    generate_direct() deliberately does not cover them either -- see its
    own docstring), which already tolerates loose phrasing --
    CREATOR_EXAMPLE_PROMPTS was judged sufficient for that family instead
    of adding rows here."""
    from tools.director_v02 import mechanic_engine as me

    exempt = {"MULTIPLE_CHOICE_SINGLE_FACT", "PROGRESSIVE_CLUE_IDENTIFY"}
    expected = me.TAXONOMY_IDS - exempt
    catalog_taxonomies = {row[1] for row in CREATOR_FORMAT_CATALOG_DIRECT} | {row[2] for row in CREATOR_FORMAT_CATALOG_PHRASE}
    assert catalog_taxonomies == expected


# --- gateway.services.creator.generate_direct() -- direct behavior -------

def test_generate_direct_rejects_an_unknown_taxonomy_id():
    from gateway.services import creator
    from gateway.errors import GatewayError

    with pytest.raises(GatewayError):
        creator.generate_direct(taxonomy_id="NOT_A_REAL_TAXONOMY", variant="X")


def test_generate_direct_rejects_an_unknown_variant_for_a_real_taxonomy_id():
    from gateway.services import creator
    from gateway.errors import GatewayError

    with pytest.raises(GatewayError):
        creator.generate_direct(taxonomy_id="BLIND_RESUME", variant="NOT_A_REAL_VARIANT")


def test_generate_direct_rejects_schedule_driven_taxonomies():
    """WEEKLY_PICKEM/LIVE_WEEKLY_FANTASY_DRAFT/CONFIDENCE_PICK need a real
    (league, season, week) resolution generate_direct() deliberately does
    not duplicate -- confirming it fails closed (a clear error) rather
    than silently generating with a wrong/missing schedule context."""
    from gateway.services import creator
    from gateway.errors import GatewayError

    with pytest.raises(GatewayError):
        creator.generate_direct(taxonomy_id="WEEKLY_PICKEM", variant="NFL_WEEKLY_PICKEM")


def test_generate_direct_never_leaks_a_hidden_answer_in_the_view():
    """Same no-leakage discipline every mechanic's own tests already
    apply, spot-checked here for the direct-generation path specifically
    (proves generate_direct() really does return mechanic_engine's own
    client_safe_view(), never the raw private package)."""
    from gateway.services import creator

    result = creator.generate_direct(
        taxonomy_id="PICK_THE_IMPOSTOR", variant="NFL_TEAM_ROSTER_IMPOSTOR", seed="pytest-picker-leak")
    view = result["view"]
    assert "_impostor_item_id" not in str(view)


# --- POST /v1/creator/format/generate -- the real HTTP route -------------

def test_creator_format_generate_route_requires_admin_auth(client):
    r = client.post("/v1/creator/format/generate", json={"taxonomy_id": "BLIND_RESUME", "variant": "NFL_QB_CAREER_BLIND_RESUME"})
    assert r.status_code == 401


def test_creator_format_generate_route_generates_a_real_round_with_admin_auth(client, auth_headers):
    r = client.post(
        "/v1/creator/format/generate",
        json={"taxonomy_id": "BLIND_RESUME", "variant": "NFL_QB_CAREER_BLIND_RESUME", "seed": "pytest-picker-route"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["taxonomy_id"] == "BLIND_RESUME"
    assert body["round_id"].startswith("GGP27:")
