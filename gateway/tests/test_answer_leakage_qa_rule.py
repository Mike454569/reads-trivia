"""Tests for the generic, permanent answer-leakage QA rule
(tools/game_director_v01.py's _check_answer_leakage) and the two adapters
that opt into it (nfl_game_result.py, cfb_game_result.py).

Real, confirmed-live incident this guards against (found and fixed in a
prior session, commit 37a90df, but shipped with NO test coverage of its
own -- these tests close that gap): nfl_game_result.py/cfb_game_result.py's
distractor pools used to exclude BOTH the winner and loser from the option
set, so a "who won when the X played the Y" question's four options were
the winner plus three teams that never played in the game -- the loser
(the other team actually named in the question) could never appear,
letting a player identify the correct answer purely from which named team
was present, no football knowledge required. Independently re-confirmed
live during this session: the STATIC exported file the app actually serves
(data/quiz-engine-game-result-production.js) was still showing this exact
leak after the source fix landed, because it had never been regenerated --
a separate, real gap from the source-code fix itself, also closed here.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools import game_director_v01 as v01  # noqa: E402
from tools.director_v02 import pipeline  # noqa: E402

_MATCHUP_RE = re.compile(r"when (?:the )?(.+?) played (?:the )?(.+?) in")


# --- unit tests: the generic rule itself, in isolation ----------------------

def test_leakage_rule_rejects_partial_referenced_entity_overlap():
    result = {"options": ["Team A", "Team X", "Team Y", "Team Z"], "_audit": {"referenced_entities": ["Team A", "Team B"]}}
    assert v01._check_answer_leakage(result) == "ANSWER_LEAKAGE_PARTIAL_REFERENCED_ENTITIES"


def test_leakage_rule_passes_when_both_referenced_entities_present():
    result = {"options": ["Team A", "Team B", "Team X", "Team Y"], "_audit": {"referenced_entities": ["Team A", "Team B"]}}
    assert v01._check_answer_leakage(result) is None


def test_leakage_rule_passes_when_neither_referenced_entity_present():
    # A capability whose options are drawn from an entirely different
    # category than the entities named in its question text (not this
    # domain's shape, but the rule must not falsely flag it).
    result = {"options": ["Won", "Lost"], "_audit": {"referenced_entities": ["Team A", "Team B"]}}
    assert v01._check_answer_leakage(result) is None


def test_leakage_rule_is_a_noop_for_adapters_that_never_opt_in():
    # No `referenced_entities` key at all -- every capability that predates
    # this rule (Draft, Heisman, Championship, etc.) must be completely
    # unaffected, per the rule's own opt-in design.
    result = {"options": ["A", "B", "C", "D"], "_audit": {}}
    assert v01._check_answer_leakage(result) is None
    assert v01._check_answer_leakage({"options": ["A"], "_audit": None}) is None


# --- integration: real generation against the real, current database -------

def _check_no_leakage(questions: list[dict]) -> tuple[int, int, list[dict]]:
    """Independently re-derives ground truth from the question TEXT itself
    (never from _audit.referenced_entities, which is the mechanism under
    test) -- for every question that names two teams via the "X played Y"
    pattern, both must appear in options, or neither may."""
    checked = 0
    leaked = 0
    examples = []
    for q in questions:
        m = _MATCHUP_RE.search(q["question"])
        if not m:
            continue
        team_a, team_b = m.group(1), m.group(2)
        checked += 1
        options = set(q["options"])
        present = (team_a in options, team_b in options)
        if present[0] != present[1]:
            leaked += 1
            examples.append(q)
    return checked, leaked, examples


def test_nfl_game_result_generates_100_real_questions_with_zero_leakage():
    pkg = pipeline.run(
        "Guess which NFL team won the game.", provider="mock",
        seed="test-nfl-game-result-leakage-guard", question_count_override=100,
    )
    assert pkg.get("qa_status") == "PASSED"
    questions = pkg.get("questions") or []
    assert len(questions) == 100
    checked, leaked, examples = _check_no_leakage(questions)
    assert checked >= 100
    assert leaked == 0, f"leaked questions: {examples}"


def test_cfb_game_result_generates_100_real_questions_with_zero_leakage():
    pkg = pipeline.run(
        "Guess which CFB team won the game.", provider="mock",
        seed="test-cfb-game-result-leakage-guard", question_count_override=100,
    )
    assert pkg.get("qa_status") == "PASSED"
    questions = pkg.get("questions") or []
    assert len(questions) == 100
    checked, leaked, examples = _check_no_leakage(questions)
    assert checked >= 100
    assert leaked == 0, f"leaked questions: {examples}"


# --- the served static files (the actual bug the user hit live) ------------

def _load_static_js_array(path: Path) -> list[dict]:
    src = path.read_text()
    start = src.index("[")
    end = src.rindex("]") + 1
    return json.loads(src[start:end])


def test_static_nfl_game_result_file_has_zero_leakage():
    """Regression guard for the real gap found live during this session:
    the source-code fix (37a90df) did not, by itself, fix the actual data
    the app serves -- data/quiz-engine-game-result-production.js is a
    STATIC export that must be independently regenerated
    (tools/generate_quiz_engine_game_result_production.py) after any adapter
    change. This test would have caught that gap immediately."""
    path = REPO_ROOT / "data" / "quiz-engine-game-result-production.js"
    rows = _load_static_js_array(path)
    assert len(rows) >= 100
    checked, leaked, examples = _check_no_leakage(rows)
    assert checked >= 100
    assert leaked == 0, f"leaked questions in the served static file: {examples}"


def test_static_cfb_game_result_file_has_zero_leakage():
    path = REPO_ROOT / "data" / "quiz-engine-cfb-game-result-production.js"
    rows = _load_static_js_array(path)
    assert len(rows) >= 100
    checked, leaked, examples = _check_no_leakage(rows)
    assert checked >= 100
    assert leaked == 0, f"leaked questions in the served static file: {examples}"
