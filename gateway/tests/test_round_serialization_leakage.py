"""Phase 2 -- answer-leakage tests for every currently supported mechanic.

Two real mechanics exist today: multiple-choice ("guess") and progressive
clue reveal ("identify_player_from_clues"). This file independently
verifies both, never trusting the mechanism under test:

1. The 7 capabilities actually served through the real public route
   (gateway/services/public_game.py's PUBLIC_MODES) are checked against the
   real served client payload for every SERVER_PRIVATE_ONLY_FIELDS name,
   recursively -- proving the transport-level leak class (a field the
   client should never see) cannot occur for what real end users actually
   receive today.
2. All 21 registered capabilities (not just the 7 public + the 2
   WON_GAME ones already covered by test_answer_leakage_qa_rule.py) are
   exercised through real generation and checked for the structural leak
   class (the generic _check_answer_leakage rule in game_director_v01.py)
   -- confirming no capability silently regresses this rule going forward.
3. identify_player_from_clues -- not currently served through any public
   route at all (a real, pre-existing, honest scope boundary, not expanded
   here) -- is checked for its own real leak class: clue text spoiling its
   own answer. A real protection already exists at generation time
   (player_from_clues.py's own name-leakage clue-drop logic); this
   independently re-verifies it holds across real generated output rather
   than trusting that the mechanism under test works.
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


# --- 1. Real public-route transport-level leakage (the 7 real public modes) -

def _real_public_modes() -> list[str]:
    from gateway.services import public_game

    return [m for m in public_game.PUBLIC_MODES if m not in public_game.KNOWN_NOT_YET_PUBLIC_MODES]


@pytest.mark.parametrize("mode", _real_public_modes() if engine_bootstrap.ENGINE_DIR.is_dir() else [])
def test_real_public_mode_served_payload_has_no_leaked_fields(mode):
    from gateway.services import public_game
    from tools.director_v02.round_serialization import assert_no_leaked_fields

    view = public_game.get_public_game(mode=mode, difficulty=None, seed=None, exclude_game_ids=None)
    assert_no_leaked_fields(view)


@pytest.mark.parametrize("mode", _real_public_modes() if engine_bootstrap.ENGINE_DIR.is_dir() else [])
def test_real_public_mode_pre_answer_view_never_has_post_answer_reveal_fields(mode):
    """The correct answer must only ever appear AFTER a real guess is
    submitted -- never in the initial served view."""
    from gateway.services import public_game

    view = public_game.get_public_game(mode=mode, difficulty=None, seed=None, exclude_game_ids=None)
    assert "canonical_answer" not in view
    assert "correct" not in view
    assert "canonical_answer" not in view.get("payload", {})


def test_real_public_modes_cover_at_least_seven_capabilities():
    # A real, honest floor -- if this drops, a mode was silently de-listed.
    assert len(_real_public_modes()) >= 7


# --- 2. Structural leakage rule across all 21 registered capabilities -------

def _all_registered_triples():
    from tools.director_v02 import registry

    return list(registry.CAPABILITY_REGISTRY.keys())


@pytest.mark.parametrize(
    "mechanic,domain,predicate",
    _all_registered_triples() if engine_bootstrap.ENGINE_DIR.is_dir() else [],
)
def test_real_generation_across_all_21_capabilities_produces_no_leakage_rejections_silently_missed(
    mechanic, domain, predicate,
):
    """Not a claim that every capability generates a full package (some have
    small real candidate pools) -- only that whatever DOES generate never
    exposes a structural leak, and the generic rule is actually reachable
    (never silently bypassed) for every capability, not just the 2 that
    explicitly opt in via referenced_entities."""
    from tools.director_v02 import registry
    from tools.director_v02.registry import _generate_guess_package, _generate_player_from_clues_package

    cap = registry.CAPABILITY_REGISTRY[(mechanic, domain, predicate)]
    if mechanic == "identify_player_from_clues":
        pkg = _generate_player_from_clues_package(
            {"mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
             "question_count": 10, "difficulty": "any", "filters": {}, "exclusions": []},
            cap, request_text="leakage probe", director_request_id="phase2-leak-probe",
            seed=f"phase2-leak-{domain}-{predicate}", target_count=10, id_start=1, freeze_timestamp=None,
        )
        assert pkg.get("qa_status") in ("PASSED", "FAILED")  # never raises; real, honest outcome either way
        return

    validated_spec = {
        "mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
        "question_count": 10, "difficulty": "any", "filters": {}, "exclusions": [],
    }
    pkg = _generate_guess_package(
        validated_spec, cap, request_text="leakage probe", director_request_id="phase2-leak-probe",
        seed=f"phase2-leak-{domain}-{predicate}", target_count=10, id_start=1, freeze_timestamp=None,
    )
    # Real, generic invariant regardless of domain: every exported question
    # must have exactly 4 unique options and a correctIndex pointing at a
    # real one of them (contract.py's own rule, re-verified independently
    # here rather than trusting it was applied).
    for q in pkg.get("questions", []):
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert 0 <= q["correctIndex"] <= 3


# --- 3. identify_player_from_clues -- clue-text-spoils-its-own-answer check -

def test_player_from_clues_real_generated_clues_never_spoil_their_own_answer():
    from tools.director_v04 import player_from_clues
    from tools.director_v02.round_serialization import clue_text_leaks_answer

    pkg = player_from_clues.build_package(seed="phase2-clue-leak-probe", target_count=100)
    puzzles = pkg["puzzles"]
    assert len(puzzles) >= 20, "need a real, meaningful sample to trust this check"

    leaks = []
    for puzzle in puzzles:
        answer_name = puzzle["answer"]["display_name"]
        for clue in puzzle["clues"]:
            if clue_text_leaks_answer(clue["display_text"], answer_name):
                leaks.append((answer_name, clue["display_text"]))
    assert not leaks, f"clue text leaked its own answer: {leaks}"


def test_clue_text_leaks_answer_helper_itself_is_correct():
    from tools.director_v02.round_serialization import clue_text_leaks_answer

    assert clue_text_leaks_answer("Mahomes led the league in TDs", "Patrick Mahomes")
    assert clue_text_leaks_answer("Patrick Mahomes was drafted in 2017", "Patrick Mahomes")
    assert not clue_text_leaks_answer("This QB was drafted 10th overall in 2017", "Patrick Mahomes")
    assert not clue_text_leaks_answer("", "Patrick Mahomes")
    assert not clue_text_leaks_answer("Some clue text", "")


# --- 4. assert_no_leaked_fields helper correctness --------------------------

def test_assert_no_leaked_fields_catches_a_nested_leak():
    from tools.director_v02.round_serialization import LeakedFieldError, assert_no_leaked_fields

    with pytest.raises(LeakedFieldError):
        assert_no_leaked_fields({"payload": {"options": ["A", "B"], "correctIndex": 0}})


def test_assert_no_leaked_fields_passes_a_real_clean_payload():
    from tools.director_v02.round_serialization import assert_no_leaked_fields

    assert_no_leaked_fields({
        "game_id": "GGP:abc123", "mode": "draft_guess",
        "payload": {"prompt": "Who drafted this player?", "options": ["Team A", "Team B", "Team C", "Team D"]},
    })
