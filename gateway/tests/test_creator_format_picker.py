"""Format Picker pass -- the Creator admin UI (creator-ui.js's own
CREATOR_FORMAT_CATALOG) now lists every real, already-shipped format as a
clickable row instead of requiring the admin to already know its exact
natural-language trigger phrase (the user's own reported gap: "I want it
to give me options ... not just strictly to you having to say the
format"). Each row's phrase is a plain JS string literal with no backend
counterpart to import, so this file keeps its own Python mirror of that
exact phrase list and asserts every one of them still resolves, through
the real gateway.services.creator.assess_feasibility() pipeline, to its
intended taxonomy_id with SUPPORTED status.

This is a regression guard, not new behavior: if a future change to any
of the three NL bridges (nl_new_taxonomy_bridge.py / nl_mechanic_bridge.py
/ nl_schedule_bridge.py) narrows or breaks one of these phrases, this
test fails loudly instead of the picker silently going dead for that row.
Keep this list in sync with creator-ui.js's own CREATOR_FORMAT_CATALOG by
hand -- there is no shared source of truth between JS and Python in this
codebase (same convention every other JS-side constant in this repo
already follows).
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

# Mirrors creator-ui.js's CREATOR_FORMAT_CATALOG (title, phrase, expected taxonomy_id).
CREATOR_FORMAT_CATALOG = [
    ("Matching", "Give me a matching game with NFL draft picks.", "MATCHING"),
    ("Timeline Order", "Give me a timeline game with NFL Draft picks.", "SORTING_TIMELINE"),
    ("Stat Ladder", "Give me a stat ladder with quarterbacks.", "SORTING_TIMELINE"),
    ("Map the Career", "Map the career of a real NFL player.", "SORTING_TIMELINE"),
    ("Head to Head Duel", "Give me a head to head duel between two real quarterbacks.", "PAIRWISE_COMPARE"),
    ("Best of Seven Duel", "Give me a best of seven duel between two real quarterbacks.", "PAIRWISE_COMPARE"),
    ("Leaderboard Climb", "Give me a leaderboard climb game with real NFL passers.", "LEADERBOARD_CLIMB"),
    ("Higher or Lower", "Give me a higher or lower game with NFL team win totals.", "HIGHER_LOWER_STREAK"),
    ("Comparison Bracket", "Give me a bracket game with NFL teams.", "COMPARISON_BRACKET"),
    ("Pick the Impostor", "Give me a pick the impostor game with real NFL players.", "PICK_THE_IMPOSTOR"),
    ("Unique One Out", "Give me a unique one out game with real NFL players.", "PICK_THE_IMPOSTOR"),
    ("Missing Piece", "Give me a missing piece game with real NFL players.", "MISSING_PIECE"),
    ("Blind Resume", "Give me a blind resume game with a real NFL quarterback.", "BLIND_RESUME"),
    ("Lineup Builder", "Build me a skill position lineup.", "ROSTER_BUILD"),
    ("Auction Draft", "Give me an auction draft.", "ROSTER_BUILD"),
    ("Cap Challenge", "Give me a salary cap challenge.", "ROSTER_BUILD"),
    ("Lineup Grid", "Guess the team from its starting lineup.", "POSITION_LINEUP_GRID"),
    ("Risk It", "Give me a risk it game with real NFL Draft picks.", "RISK_IT"),
    ("Wager Mode", "Give me a wager mode game.", "WAGER_MODE"),
    ("Knockout Tournament", "Give me a 16-team knockout tournament.", "KNOCKOUT_BRACKET"),
    ("Elimination", "Give me an elimination game.", "ELIMINATION_SURVIVAL"),
    ("Choose Your Path", "Give me a choose-your-path game.", "BRANCH_STATE"),
    ("Career Path", "Give me a career path game with a real NFL player.", "CAREER_PATH"),
    ("Before & After", "Give me a before and after game with a real NFL player.", "BEFORE_AFTER"),
    ("Guess the Season", "Guess the season this real NFL team won it all.", "GUESS_THE_SEASON"),
    ("Connection Grid", "Give me a connection grid game.", "GRID_CONSTRAINT_BOARD"),
    ("Six Degrees", "Connect these two players.", "RELATIONSHIP_CHAIN"),
    ("Chain Reaction", "Give me a chain reaction game.", "RELATIONSHIP_CHAIN"),
    ("Perfect Drive", "Give me a perfect drive game.", "DRIVE_PROGRESSION"),
    ("Goal Line Stand", "Give me a goal line stand game.", "DRIVE_PROGRESSION"),
    ("Weekly Pick'em", "Give me the NFL weekly pick'em.", "WEEKLY_PICKEM"),
    ("Fantasy Draft", "Give me a fantasy draft with NFL players.", "LIVE_WEEKLY_FANTASY_DRAFT"),
    ("Confidence Pick", "Give me a confidence pick game for this week's NFL games.", "CONFIDENCE_PICK"),
]


def test_creator_format_catalog_has_no_duplicate_titles():
    titles = [row[0] for row in CREATOR_FORMAT_CATALOG]
    assert len(titles) == len(set(titles)), "the picker would show two rows with the same title"


@pytest.mark.parametrize("title,phrase,expected_taxonomy", CREATOR_FORMAT_CATALOG)
def test_creator_format_picker_phrase_resolves_to_intended_format(title, phrase, expected_taxonomy):
    from gateway.services import creator

    result = creator.assess_feasibility(phrase)
    assert result["support_status"] in ("SUPPORTED", "SUPPORTED_WITH_LIMITATIONS"), (title, phrase, result)
    assert result["taxonomy_id"] == expected_taxonomy, (title, phrase, result.get("taxonomy_id"))


def test_creator_format_picker_covers_every_real_taxonomy_id_except_the_flexible_translator_ones():
    """Every taxonomy_id mechanic_engine.py knows about should have at
    least one picker row -- otherwise it is real, generatable, and
    playable but still only reachable by an admin who already knows its
    exact phrase, which is the exact gap this picker exists to close.
    Exactly two taxonomy_ids are deliberately exempt: MULTIPLE_CHOICE_
    SINGLE_FACT and PROGRESSIVE_CLUE_IDENTIFY are reached exclusively
    through the OLD flexible guess/identify_player_from_clues translator
    (no narrow-anchored NL bridge exists for either), which already
    tolerates loose phrasing -- CREATOR_EXAMPLE_PROMPTS was judged
    sufficient for that family instead of adding rows here."""
    from tools.director_v02 import mechanic_engine as me

    exempt = {"MULTIPLE_CHOICE_SINGLE_FACT", "PROGRESSIVE_CLUE_IDENTIFY"}
    expected = me.TAXONOMY_IDS - exempt
    catalog_taxonomies = {row[2] for row in CREATOR_FORMAT_CATALOG}
    assert catalog_taxonomies == expected
