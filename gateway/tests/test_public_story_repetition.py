"""Story-bank recency selection and source safety without a live DB."""
import json
from unittest.mock import patch

from gateway.services import public_story


class FakeRows(list):
    def fetchall(self):
        return list(self)


class FakeDB:
    def execute(self, sql, params=()):
        if "sqlite_master" in sql:
            return FakeRows([("story_generated_questions",), ("universal_event",)])
        return FakeRows([
            {"event_id": "event-1", "question_json": json.dumps(_question("story-1"))},
            {"event_id": "event-1", "question_json": json.dumps(_question("story-2"))},
        ])
    def close(self):
        pass


def _question(identifier):
    return {
        "question_id": identifier, "event_id": "event-1",
        "mechanic": "MULTIPLE_CHOICE", "question": "Which team?",
        "options": ["A", "B", "C", "D"],
        "answer": {"id": "b", "label": "B"},
        "provenance": {"provenance_complete": True, "event_ids": ["event-1"], "evidence": ["URL"]},
    }


def test_same_client_does_not_repeat_first_story():
    public_story._recent_by_client.clear()
    with patch.object(public_story.engine_bootstrap, "connect", return_value=FakeDB()):
        with patch.object(public_story.game_state, "create_state"):
            first = public_story.start_story_round("story_lore_nfl", client_id="test-client-123")
            second = public_story.start_story_round("story_lore_nfl", client_id="test-client-123")
    assert first["round_id"] != second["round_id"]
    assert list(public_story._recent_by_client[("test-client-123", "story_lore_nfl")]) == ["story-1", "story-2"]
