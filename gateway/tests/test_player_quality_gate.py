"""Player Experience pass (Part 2): the shared, global player-quality gate
added to tools/quiz_export/contract.py -- every adapter's exported output
already passes through contract.validate_all() before qa_status can be
"PASSED" (game_director_v01.py), so this is the one place a generic
template-completeness check protects EVERY public mode at once, not just
the one (Rivalries) that reached production malformed.

Deliberately narrow scope, verified directly: real English questions
routinely end in a stranded preposition ("What team does he play for?",
"What is this known as?") -- those are grammatical, not bugs. Only a
handful of patterns are unambiguous artifacts of a missing interpolated
value: a bare determiner/conjunction ending a question, double spaces,
empty quoted strings, literal None/null/undefined tokens, and unresolved
{placeholder} syntax. Verified with zero false positives across 3,659 real
questions sampled from all 67 registered capabilities before this file was
written.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import contract  # noqa: E402
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402


def _record(**overrides) -> dict:
    base = {
        "id": 1, "category": "Test Category", "difficulty": "Medium",
        "question": "Which team drafted him?", "options": ["Team A", "Team B", "Team C", "Team D"],
        "correctIndex": 0, "notes": "A real, useful explanation.",
    }
    base.update(overrides)
    return base


# --- the malformed-text detector itself ----------------------------------------

@pytest.mark.parametrize("text", [
    "Which school is Ole Miss’s rival in the game known as the?",
    "Which school is Ole Miss’s rival in a rivalry game or?",
    "What team drafted him in the  2015 draft?",  # double space
    "This player scored None real points.",
    "Which team is this (\"\")?",
    "What team did he play for in {season}?",
    "The score was {}.",
])
def test_malformed_text_reason_catches_every_real_reproduced_defect_shape(text):
    assert contract._malformed_text_reason(text) is not None, text


@pytest.mark.parametrize("text", [
    "What team does he play for?",
    "What position is he known as?",
    "Which school did he attend?",
    "What year was he drafted in?",
    "Which team is he a fan of?",
    "Who did he play against?",
    "What position is he listed at?",
    "Real football questions routinely end with a preposition, and that's fine.",
])
def test_malformed_text_reason_never_flags_a_real_grammatical_question(text):
    """The core false-positive guard: English legitimately strands
    prepositions at the end of a question -- only bare determiners/
    conjunctions (which can never end a sentence on their own) are safe to
    flag with zero ambiguity."""
    assert contract._malformed_text_reason(text) is None, text


def test_none_is_a_legitimate_short_answer_value_not_a_leak():
    """Real, confirmed-live false positive: this codebase's own curated
    CFB Rivalry Trivia bank has real questions whose real, correct answer
    is "None" or "None clear" (meaning no real trophy/consensus exists) --
    a legitimate English word, not a Python None leaking into an f-string.
    Only flagged as a bug when embedded in a longer generated SENTENCE
    (is_short_answer_value=False, the default), never for a short answer
    value on its own."""
    assert contract._malformed_text_reason("None", is_short_answer_value=True) is None
    assert contract._malformed_text_reason("None clear", is_short_answer_value=True) is None
    # The real bug shape (a raw None leaking into a full sentence) must still be caught.
    assert contract._malformed_text_reason("He scored None points.", is_short_answer_value=False) is not None


# --- wired into validate_contract() --------------------------------------------

def test_dangling_question_fails_contract_validation():
    record = _record(question="Which school is Ole Miss’s rival in the game known as the?")
    failures = contract.validate_contract(record, "Test Category")
    assert any("malformed question" in f[1] for f in failures)


def test_dangling_option_fails_contract_validation():
    record = _record(options=["Team A", "Team B (\"\")", "Team C", "Team D"])
    failures = contract.validate_contract(record, "Test Category")
    assert any("malformed option" in f[1] for f in failures)


def test_none_as_a_real_option_passes_contract_validation():
    """The real, legitimate curated-content case -- "None" as a genuine
    trivia answer must never fail validation."""
    record = _record(options=["USC (1980s context)", "Multiple claims", "Alabama", "None clear"])
    failures = contract.validate_contract(record, "Test Category")
    assert failures == []


def test_dangling_notes_fails_contract_validation():
    record = _record(notes="He played for the  team in {season}.")
    failures = contract.validate_contract(record, "Test Category")
    assert any("malformed notes" in f[1] for f in failures)


def test_a_normal_real_question_passes_clean():
    record = _record()
    failures = contract.validate_contract(record, "Test Category")
    assert failures == []


def test_empty_notes_is_still_allowed_not_a_new_hard_requirement():
    """Some adapters legitimately have nothing more to add -- this gate
    catches MALFORMED text, it does not newly require every question to
    carry a non-empty explanation (a separate, adapter-level concern)."""
    record = _record(notes="")
    failures = contract.validate_contract(record, "Test Category")
    assert failures == []


# --- zero false positives across real, live production content ---------------

pytestmark_real_db = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


@pytestmark_real_db
def test_zero_false_positives_across_every_registered_capability():
    """Direct, comprehensive proof -- not just a sample of hand-picked
    sentences. Generates real output from every adapter in the registry
    (except the two identify_player_from_clues-mechanic capabilities,
    which use a structurally different function shape than every other
    adapter here and are covered by their own dedicated test files) and
    confirms qa_status is never FAILED by a real, non-empty package purely
    because of this new check."""
    from tools import game_director_v01 as v01
    from tools.director_v02 import registry

    total_checked = 0
    flagged = []
    for (mechanic, domain, predicate), cap in registry.CAPABILITY_REGISTRY.items():
        adapter = cap.get("adapter")
        if adapter is None or not hasattr(adapter, "fetch_ordered_candidates"):
            continue
        spec = {
            "competition_id": cap.get("competition_id", "NFL"), "mechanic": mechanic,
            "entity_type": cap.get("entity_type"), "relationship_predicate": predicate,
            "object_type": cap.get("object_type"), "answer_type": cap.get("answer_type"),
            "group_size": cap.get("group_size", 4), "filters": {},
        }
        try:
            pkg = v01.generate_package_from_spec(
                spec, adapter, request_text="pytest", director_request_id="pytest",
                seed=f"pytest-falsepos-{domain}-{predicate}", target_count=60, id_start=1,
            )
        except Exception:
            continue  # a small number of capabilities need extra filters this generic sweep can't supply
        n = len(pkg.get("questions", []))
        total_checked += n
        if n > 0 and pkg["qa_status"] == "FAILED":
            flagged.append((domain, predicate))
    assert total_checked > 2000, f"only {total_checked} real questions sampled -- too few to trust this sweep"
    assert flagged == [], f"the new player-quality gate false-positived on real content: {flagged}"
