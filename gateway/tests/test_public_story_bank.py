"""Story Bank public gateway contract tests (no production database)."""
from unittest.mock import patch

from gateway.services import public_story, public_formats


def _question():
    return {
        "question_id": "test-1", "event_id": "event-1",
        "mechanic": "MULTIPLE_CHOICE", "question": "What happened next?",
        "options": ["One", "Two", "Three", "Four"],
        "answer": {"id": "2", "label": "Two"},
        "provenance": {"provenance_complete": True, "evidence": ["source"],
                       "event_ids": ["event-1"]},
    }


def test_story_question_certification_shape():
    assert public_story._eligible(_question(), "event-1")
    altered = _question()
    altered["options"] = ["One", "One", "Three", "Four"]
    assert not public_story._eligible(altered, "event-1")
    altered = _question()
    altered["provenance"] = {}
    assert not public_story._eligible(altered, "event-1")


def test_story_round_submission_is_server_authoritative():
    state = {"story_bank_mode": "story_lore_nfl", "answer": "Two", "notes": "Verified source"}
    with patch.object(public_story.game_state, "load_state", return_value=state):
        response = public_formats.submit_public_format(
            round_id="GGP4:0123456789abcdef01234567",
            submission={"answer": "One"},
        )
    assert response["engine_kind"] == "story"
    assert response["result"]["correct"] is False
    assert response["result"]["canonical_answer"] == "Two"


def test_new_story_modes_are_discoverable():
    with patch.object(public_formats.public_game, "list_public_modes", return_value=[]), patch.object(
        public_formats.public_mechanics, "list_public_mechanic_modes", return_value=[]
    ):
        modes = public_formats.list_public_formats()
    assert {m["mode"] for m in modes} == {"story_lore_nfl", "story_lore_cfb"}
