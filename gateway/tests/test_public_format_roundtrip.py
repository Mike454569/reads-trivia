"""Unified gameplay contract tests for launch, submission and progression routing."""
from unittest.mock import patch

import pytest

from gateway.errors import GatewayError
from gateway.services import public_formats


def test_question_launch_and_answer_use_same_round_id():
    game = {
        "game_id": "GGP:0123456789abcdef01234567",
        "mode": "draft_guess", "title": "Draft", "instructions": "Choose",
        "payload": {"prompt": "Which?", "options": ["A", "B", "C", "D"]},
    }
    with patch.object(public_formats.public_game, "get_public_game", return_value=game):
        started = public_formats.start_public_format(mode="draft_guess")
    assert started["round_id"] == game["game_id"]
    with patch.object(public_formats.game_state, "load_state", return_value=None), patch.object(
        public_formats.public_game, "validate_public_answer", return_value={"correct": True}
    ) as grade:
        submitted = public_formats.submit_public_format(
            round_id=started["round_id"], submission={"answer": "A"}
        )
    assert submitted["engine_kind"] == "question"
    grade.assert_called_once_with(game_id=started["round_id"], answer="A")


def test_mechanic_submission_returns_new_round_view():
    progress = {"public_mode": "matching_nfl_draft", "taxonomy_id": "MATCHING"}
    graded = {
        "mode": "matching_nfl_draft", "result": {"correct": True},
        "view": {"completed": True},
    }
    with patch.object(public_formats.game_state, "load_state", return_value=progress), patch.object(
        public_formats.public_mechanics, "submit_public_round", return_value=graded
    ) as grade:
        submitted = public_formats.submit_public_format(
            round_id="GGP4:0123456789abcdef01234567",
            submission={"pairs": [0, 1]},
        )
    assert submitted["engine_kind"] == "mechanic"
    assert submitted["view"]["completed"] is True
    grade.assert_called_once()


def test_question_submission_requires_answer():
    with patch.object(public_formats.game_state, "load_state", return_value=None):
        with pytest.raises(GatewayError):
            public_formats.submit_public_format(
                round_id="GGP:0123456789abcdef01234567", submission={}
            )
