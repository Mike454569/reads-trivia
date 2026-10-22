"""Existing Who Am I mode uses story clues and retains legacy fallback."""
from unittest.mock import patch

from gateway.services import public_mechanics, public_story


def test_story_identity_reveal_then_correct_guess():
    round_id = "GGP4:0123456789abcdef01234567"
    state = {"story_identity_mode": "who_am_i_nfl", "answer": "Player One",
             "clues": ["League NFL", "Draft year 2010", "Played for Team X"],
             "clues_revealed": 1, "completed": False}
    with patch.object(public_story.game_state, "load_state", side_effect=lambda _: state), patch.object(
        public_story.game_state, "save_state"
    ):
        first = public_mechanics.submit_public_round(round_id=round_id, submission={"action": "reveal_next_clue"})
        assert first["view"]["clues_revealed_count"] == 2
        second = public_mechanics.submit_public_round(round_id=round_id, submission={"guess_name": "Player One"})
    assert second["result"]["correct"] is True
    assert second["view"]["completed"] is True


def test_who_am_i_uses_story_then_legacy_when_none():
    with patch.object(public_story, "start_story_identity", return_value={
        "round_id": "GGP4:0123456789abcdef01234567", "mode": "who_am_i_nfl",
        "view": {"completed": False}, "metadata": {},
    }), patch.object(public_mechanics, "_ensure_mode_public"):
        result = public_mechanics.start_public_round(mode="who_am_i_nfl")
    assert result["mode"] == "who_am_i_nfl"
