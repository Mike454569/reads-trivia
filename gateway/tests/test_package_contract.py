"""P0 Accuracy + Reliability Hardening pass: tests for the shared global
supported-game contract (tools/director_v02/package_contract.py) and its
real enforcement point (gateway/services/packages.py's save_package()).

The core claim under test: qa_status="PASSED" must be impossible for an
empty or structurally broken package to reach persistence, REGARDLESS of
what the generator itself claims -- these tests deliberately construct
generator output a buggy/future generate_fn might produce (qa_status=
"PASSED" set unconditionally) to prove the independent check still catches
it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from tools.director_v02.package_contract import validate_package_contract, is_valid_package


def _base_guess_package(**overrides) -> dict:
    pkg = {
        "package_id": "GGP:aaaaaaaaaaaaaaaaaaaaaaaa",
        "qa_status": "PASSED",
        "review_status": "GENERATED",
        "questions": [
            {
                "id": 1, "question": "Which team?", "options": ["Team A", "Team B", "Team C", "Team D"],
                "correctIndex": 0, "answer": "Team A",
            },
        ],
    }
    pkg.update(overrides)
    return pkg


def test_valid_guess_package_passes():
    assert validate_package_contract(_base_guess_package()) == []
    assert is_valid_package(_base_guess_package()) is True


def test_empty_questions_list_rejected_even_if_generator_claims_passed():
    pkg = _base_guess_package(questions=[])
    violations = validate_package_contract(pkg)
    assert violations
    assert any("empty" in v for v in violations)


def test_missing_content_key_entirely_rejected():
    pkg = _base_guess_package()
    del pkg["questions"]
    violations = validate_package_contract(pkg)
    assert violations
    assert any("no recognized non-empty content list" in v for v in violations)


def test_answer_mismatched_with_correct_index_rejected():
    pkg = _base_guess_package()
    pkg["questions"][0]["answer"] = "Team Z"
    violations = validate_package_contract(pkg)
    assert any("does not match options[correctIndex]" in v for v in violations)


def test_duplicate_options_rejected():
    pkg = _base_guess_package()
    pkg["questions"][0]["options"] = ["Team A", "team a ", "Team C", "Team D"]
    violations = validate_package_contract(pkg)
    assert any("duplicate options" in v for v in violations)


def test_correct_index_out_of_range_rejected():
    pkg = _base_guess_package()
    pkg["questions"][0]["correctIndex"] = 9
    violations = validate_package_contract(pkg)
    assert any("not a valid index" in v for v in violations)


def test_blank_review_status_rejected():
    pkg = _base_guess_package(review_status="")
    violations = validate_package_contract(pkg)
    assert any("review_status" in v for v in violations)


def test_blank_qa_status_rejected():
    pkg = _base_guess_package(qa_status=None)
    violations = validate_package_contract(pkg)
    assert any("qa_status" in v for v in violations)


def test_missing_package_id_rejected():
    pkg = _base_guess_package(package_id="")
    violations = validate_package_contract(pkg)
    assert any("package_id" in v for v in violations)


def test_valid_puzzle_package_passes():
    pkg = {
        "package_id": "GGP4:bbbbbbbbbbbbbbbbbbbbbbbb",
        "qa_status": "PASSED",
        "review_status": "UNREVIEWED",
        "puzzles": [
            {"answer": {"player_id": "p1", "display_name": "Real Player"}, "clues": [{"text": "clue 1"}]},
        ],
    }
    assert validate_package_contract(pkg) == []


def test_puzzle_with_blank_answer_rejected():
    pkg = {
        "package_id": "GGP4:cccccccccccccccccccccccc",
        "qa_status": "PASSED",
        "review_status": "UNREVIEWED",
        "puzzles": [{"answer": {"player_id": "p1", "display_name": ""}, "clues": [{"text": "clue 1"}]}],
    }
    violations = validate_package_contract(pkg)
    assert any("answer entity is missing or blank" in v for v in violations)


def test_puzzle_with_empty_clues_rejected():
    pkg = {
        "package_id": "GGP4:dddddddddddddddddddddddd",
        "qa_status": "PASSED",
        "review_status": "UNREVIEWED",
        "puzzles": [{"answer": {"player_id": "p1", "display_name": "Real Player"}, "clues": []}],
    }
    violations = validate_package_contract(pkg)
    assert any("clues list is empty" in v for v in violations)


def test_coach_connections_graph_puzzle_passes():
    pkg = {
        "package_id": "GGP:eeeeeeeeeeeeeeeeeeeeeeee", "mode": "coach_connections",
        "qa_status": "PASSED", "review_status": "GENERATED",
        "start": {"type": "player", "id": "p1"}, "end": {"type": "player", "id": "p2"},
        "canonical_path": [{"a": 1}, {"b": 2}],
    }
    assert validate_package_contract(pkg) == []


def test_coach_connections_empty_path_rejected():
    pkg = {
        "package_id": "GGP:ffffffffffffffffffffffff", "mode": "coach_connections",
        "qa_status": "PASSED", "review_status": "GENERATED",
        "start": {"type": "player", "id": "p1"}, "end": {"type": "player", "id": "p2"},
        "canonical_path": [],
    }
    violations = validate_package_contract(pkg)
    assert any("canonical_path is empty" in v for v in violations)


def test_higher_lower_sequence_shape_passes():
    # Real gap found this pass: tools/director_v02/mechanic_engine.py wraps
    # HIGHER_LOWER_STREAK/ELIMINATION_SURVIVAL under "sequence", a different
    # key than the raw director_v04 modules' own "items" -- both real
    # shapes must be recognized.
    pkg = {
        "package_id": "GGP8:1111111111111111111111bb", "qa_status": "PASSED", "review_status": "GENERATED",
        "sequence": [{"label": "Team A", "value": 10}, {"label": "Team B", "value": 8}],
    }
    assert validate_package_contract(pkg) == []


def test_empty_sequence_rejected():
    pkg = {
        "package_id": "GGP8:2222222222222222222222bb", "qa_status": "PASSED", "review_status": "GENERATED",
        "sequence": [],
    }
    violations = validate_package_contract(pkg)
    assert any("empty" in v for v in violations)


def test_fantasy_draft_players_shape_passes():
    pkg = {
        "package_id": "GGP10:3333333333333333333333bb", "qa_status": "PASSED", "review_status": "GENERATED",
        "players": [{"player_id": "p1", "position": "QB"}], "draft_slots": ["QB", "RB", "RB"],
    }
    assert validate_package_contract(pkg) == []


def test_six_degrees_steps_shape_passes():
    pkg = {
        "package_id": "GGP:0000000000000000000000aa", "mode": "six_degrees_guess",
        "qa_status": "PASSED", "review_status": "GENERATED",
        "start": {}, "end": {}, "steps": [{"current": {}, "correct_id": "a", "options": [{"id": "a"}]}],
    }
    assert validate_package_contract(pkg) == []


def test_not_a_dict_rejected():
    violations = validate_package_contract("not a dict")
    assert violations
    assert any("not a dict" in v for v in violations)


# --- real enforcement point: save_package() must refuse to persist -------

def test_save_package_rejects_empty_questions_even_with_qa_status_passed(tmp_path, monkeypatch):
    from gateway import config
    from gateway.services import packages

    monkeypatch.setattr(config, "PACKAGES_DIR", tmp_path)
    broken = {
        "package_id": "GGP:1111111111111111111111aa",
        "qa_status": "PASSED",  # a buggy/future generator claiming PASSED anyway
        "questions": [],
    }
    with pytest.raises(ValueError, match="global supported-game contract"):
        packages.save_package(broken)
    assert not (tmp_path / "GGP_1111111111111111111111aa.json").exists()


def test_save_package_accepts_real_valid_package(tmp_path, monkeypatch):
    from gateway import config
    from gateway.services import packages

    monkeypatch.setattr(config, "PACKAGES_DIR", tmp_path)
    good = _base_guess_package(package_id="GGP:2222222222222222222222aa")
    del good["review_status"]  # save_package sets this itself
    stored = packages.save_package(good)
    assert stored["review_status"] == "GENERATED"
    assert (tmp_path / "GGP_2222222222222222222222aa.json").exists()
