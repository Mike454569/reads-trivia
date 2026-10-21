"""Story Factory integration through the established public game API."""
from unittest.mock import patch

from gateway.services import public_game, public_story


def test_story_launch_uses_existing_public_game_contract():
    stub = {
        "round_id": "GGP4:0123456789abcdef01234567",
        "mode": "story_lore_nfl", "competition": "NFL",
        "title": "Football Story Room", "instructions": "Pick one.",
        "view": {"prompt": "What happened?", "options": ["A", "B", "C", "D"]},
        "metadata": {"source": "certified_story_bank"},
    }
    with patch.object(public_story, "start_story_round", return_value=stub) as start:
        with patch.object(public_game, "_ensure_public_gameplay_enabled"):
            payload = public_game.get_public_game(
                mode="story_lore_nfl", difficulty=None, seed=None,
                exclude_game_ids=[], client_id=None,
            )
    start.assert_called_once_with("story_lore_nfl")
    assert payload["game_id"] == stub["round_id"]
    assert payload["payload"]["options"] == ["A", "B", "C", "D"]
    assert "correctIndex" not in payload["payload"]
    assert "answer" not in payload["payload"]


def test_story_answers_use_server_owned_game_state():
    game_id = "GGP4:0123456789abcdef01234567"
    with patch.object(public_game, "_ensure_public_gameplay_enabled"):
        with patch.object(public_game.game_state, "load_state", return_value={
            "story_bank_mode": "story_lore_nfl", "answer": "B",
        }):
            response = public_game.validate_public_answer(game_id=game_id, answer="B")
    assert response["correct"] is True
    assert response["canonical_answer"] == "B"


def test_legacy_games_remain_on_existing_generator():
    with patch.object(public_story, "start_story_round") as start:
        with patch.object(public_game, "_ensure_mode_public", side_effect=RuntimeError("legacy path")):
            try:
                public_game.get_public_game(
                    mode="draft_guess", difficulty=None, seed=None,
                    exclude_game_ids=[], client_id=None,
                )
            except RuntimeError as error:
                assert str(error) == "legacy path"
    start.assert_not_called()
