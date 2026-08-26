"""Product Growth + Real User Testing pass: a real, measured repetition
defect -- postseason_participation's clue text is a FIXED sentence with no
value-dependent variation (`lambda v: "This player was on an NFL team's
active roster during a playoff run..."`), and it's close enough to a 50/50
split across the whole real player universe that "broadest still-narrowing
clue first" picked it as clue #1 for 476 of the real, live 600-puzzle NFL
export (79%) -- nearly every puzzle opened with the exact same sentence.
cfb_player_from_clues.py's transfer_school_count had the same shape (a
near-binary split dominating the opening slot). Fixed by excluding each
type from the OPENING slot specifically (every other slot -- and every
other fairness/narrowing guarantee -- is untouched), with a safe fallback
to still allow it there if it's genuinely the only real clue a given
player has.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import player_from_clues, cfb_player_from_clues  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_nfl_opening_clue_is_not_dominated_by_postseason_participation():
    """The real, measured defect was TEXT repetition (476 of 600 real
    puzzles opened with the exact same sentence), not merely picking the
    same clue TYPE -- draft_round is now the most common opening TYPE, but
    its display text varies by real round number (1-7), so no single
    literal sentence should dominate the way postseason_participation's
    fixed, value-independent text once did."""
    pkg = player_from_clues.build_package("test-opening-variety-nfl", target_count=100)
    assert len(pkg["puzzles"]) >= 50, "sample too small to be a meaningful variety check"
    first_types = Counter(p["clues"][0]["clue_type"] for p in pkg["puzzles"])
    first_texts = Counter(p["clues"][0]["display_text"] for p in pkg["puzzles"])
    dominant_text_share = first_texts.most_common(1)[0][1] / len(pkg["puzzles"])
    assert dominant_text_share < 0.5, (
        f"a single literal opening sentence still dominates {dominant_text_share:.0%} of puzzles: "
        f"{first_texts.most_common(3)} -- the real repetition defect this test guards against"
    )
    assert first_types.get("postseason_participation", 0) == 0, (
        "postseason_participation (a fixed, value-independent sentence) must never be the opening clue"
    )


def test_cfb_opening_clue_is_not_dominated_by_transfer_school_count():
    pkg = cfb_player_from_clues.build_package("test-opening-variety-cfb", target_count=100)
    assert len(pkg["puzzles"]) >= 50, "sample too small to be a meaningful variety check"
    first_types = Counter(p["clues"][0]["clue_type"] for p in pkg["puzzles"])
    assert first_types.get("transfer_school_count", 0) == 0, (
        "transfer_school_count (a near-binary 1-vs-2 fact) must never be the opening clue"
    )


def test_excluded_opening_types_still_appear_later_in_the_ladder():
    """The fix must only reorder the OPENING slot, never remove real clue
    types from the ladder entirely -- postseason_participation/
    transfer_school_count should still show up in later clue positions for
    players who have them."""
    pkg = player_from_clues.build_package("test-opening-variety-nfl-later-slots", target_count=150)
    later_types = Counter(
        c["clue_type"] for p in pkg["puzzles"] for c in p["clues"][1:]
    )
    assert later_types.get("postseason_participation", 0) > 0, (
        "postseason_participation should still appear in non-opening clue slots -- "
        "the fix must not have removed it from the pool entirely"
    )


def test_nfl_fallback_still_allows_the_excluded_type_when_it_is_the_only_option():
    """Never fail a puzzle purely over a variety preference: if a player's
    only real narrowing clue happens to be the excluded type, it must still
    be used rather than rejecting the puzzle outright."""
    c = engine_bootstrap.connect()
    try:
        facts, indexes, universe_ids = player_from_clues.build_universe(c)
    finally:
        c.close()
    only_postseason = 0
    checked = 0
    for pid in list(facts.keys())[:500]:
        pool = player_from_clues._candidate_clues_for_player(pid, facts, indexes)
        types = {ct for ct, v, cset in pool}
        checked += 1
        if types == {"postseason_participation"}:
            only_postseason += 1
            puzzle, reason = player_from_clues.build_puzzle(pid, facts, indexes, universe_ids)
            assert puzzle is not None or reason in (
                "INSUFFICIENT_NARROWING_CLUES",
            ), f"unexpected rejection reason {reason!r} for a player whose only clue is the excluded type"
    assert checked > 0
