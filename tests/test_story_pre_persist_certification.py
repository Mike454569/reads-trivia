"""Story format persistence must fail closed before inserting defective artifacts."""
import pytest
from unittest.mock import MagicMock, patch
from tools.director_v05.story_multiformat import _persist


def valid():
    return {"question_id":"q1","event_id":"evt-a","mechanic":"MULTIPLE_CHOICE",
            "question":"Which player was involved in the documented incident?",
            "options":["Player A","Player B","Player C","Player D"],
            "answer":{"id":"p1","label":"Player A"},
            "provenance":{"provenance_complete":True,
                          "event_ids":["evt-a"],"evidence":[{"url":"https://example.com/article"}]}}


def test_wrong_event_id_is_never_persisted():
    c=MagicMock()
    q=valid()
    q["event_id"]="evt-b"
    with patch("tools.director_v05.story_multiformat._tables",return_value={"story_generated_questions"}), patch(
        "tools.director_v05.story_multiformat.prepare_story_question",side_effect=lambda q:q):
        with pytest.raises(ValueError,match="WRONG_EVENT_ID"):
            _persist(c,"candidate","evt-a","PLAYER","p1",q,status="READY_FOR_BANK")
    c.execute.assert_not_called()


def test_incomplete_provenance_never_persisted():
    c=MagicMock()
    q=valid()
    q["provenance"]={}
    with patch("tools.director_v05.story_multiformat._tables",return_value={"story_generated_questions"}), patch(
        "tools.director_v05.story_multiformat.prepare_story_question",side_effect=lambda q:q):
        with pytest.raises(ValueError,match="INCOMPLETE_SOURCE_PROVENANCE"):
            _persist(c,"candidate","evt-a","PLAYER","p1",q,status="READY_FOR_BANK")
    c.execute.assert_not_called()


def test_valid_source_backed_question_is_persisted():
    c=MagicMock()
    with patch("tools.director_v05.story_multiformat._tables",return_value={"story_generated_questions"}), patch(
        "tools.director_v05.story_multiformat.prepare_story_question",side_effect=lambda q:q):
        _persist(c,"candidate","evt-a","PLAYER","p1",valid(),status="READY_FOR_BANK")
    c.execute.assert_called_once()
