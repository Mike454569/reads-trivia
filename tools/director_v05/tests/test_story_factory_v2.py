import sqlite3
import pytest

from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.story_factory_v2 import prepare_story_question
from tools.director_v05.story_multiformat import compile_what_happened_next
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("CREATE TABLE canonical_players(player_id TEXT PRIMARY KEY, display_name TEXT)")
    c.execute("INSERT INTO canonical_players VALUES('p1','Player One')")
    return c


def _event(c, eid, date, title):
    upsert_event(c, {
        "event_id": eid,
        "event_type": "OFF_FIELD_ODDITY",
        "league": "NFL",
        "event_date": date,
        "title": title,
        "neutral_summary": title + " was documented during the NFL season.",
        "source_url": "https://www.nfl.com/" + eid,
        "source_publisher": "NFL.com",
        "evidence_tier": "PRIMARY",
        "verification_status": "VERIFIED",
        "subjects": [{"subject_type":"NFL_PLAYER","subject_id":"p1","role":"subject"}],
        "tags": ["story_factory"],
        "sensitive": False,
    })


def test_story_v2_rejects_internal_metadata_copy():
    q = {
        "question_id":"bad",
        "mechanic":"FACT_OR_FAKE",
        "question_family":"LORE_EVENT",
        "question":"This event was classified as a Trade.",
        "answer":{"id":"FACT","label":"Fact","type":"BOOLEAN"},
    }
    with pytest.raises(ValueError, match="STORY_V2_ROBOTIC_COPY"):
        prepare_story_question(q)


def test_what_happened_next_uses_immediate_verified_event():
    c = _conn()
    _event(c, "e1", "2018-01-01", "Player One had an unusual offseason moment")
    _event(c, "e2", "2020-01-01", "Player One made headlines during training camp")
    _event(c, "e3", "2021-01-01", "Player One returned with another memorable football story")
    _event(c, "e4", "2023-01-01", "Player One appeared in a later documented team story")
    _event(c, "e5", "2025-01-01", "Player One was featured in another verified NFL story")
    q = compile_what_happened_next(c, "NFL_PLAYER", "p1", "e2")
    assert q["mechanic"] == "MULTIPLE_CHOICE"
    assert q["question_family"] == "STORY_WHAT_HAPPENED_NEXT"
    assert q["answer"]["id"] == "e3"
    assert len(q["options"]) == 4
    assert len(set(q["options"])) == 4
    assert q["story_factory_v2"]["version"] == 2
    assert q["story_factory_v2"]["score"] >= 42


def test_what_happened_next_requires_real_chronology_depth():
    c = _conn()
    _event(c, "e1", "2020-01-01", "First documented story")
    _event(c, "e2", "2021-01-01", "Second documented story")
    _event(c, "e3", "2022-01-01", "Third documented story")
    with pytest.raises(ValueError, match="WHAT_NEXT_NEEDS_FOUR_DATED_SUBJECT_EVENTS"):
        compile_what_happened_next(c, "NFL_PLAYER", "p1", "e1")
