import json
import sqlite3
from pathlib import Path

from tools.quiz_export import engine as engine_bootstrap

if not hasattr(engine_bootstrap, "DATA_DIR"):
    engine_bootstrap.DATA_DIR = Path(".")
if not hasattr(engine_bootstrap, "ENGINE_DIR"):
    engine_bootstrap.ENGINE_DIR = None
if not hasattr(engine_bootstrap, "seeded"):
    engine_bootstrap.seeded = lambda seed: __import__("random").Random(seed)

from tools.director_v04 import deep_trivia
from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.story_to_trivia_factory import _ensure_schema
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    _ensure_schema(c)
    upsert_event(c, {
        "event_id":"e1",
        "event_type":"OFF_FIELD_ODDITY",
        "league":"NFL",
        "event_date":None,
        "title":"Story",
        "neutral_summary":"A documented football story.",
        "source_url":"https://www.nfl.com/e1",
        "source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY",
        "verification_status":"VERIFIED",
        "subjects":[{"subject_type":"NFL_PLAYER","subject_id":"p1","role":"subject"}],
        "tags":["story_factory"],
        "sensitive":False,
    })
    q = {
        "question_id":"qstory-1",
        "mechanic":"MULTIPLE_CHOICE",
        "question":"Who am I?",
        "clues":[{"text":"A"},{"text":"B"},{"text":"C"}],
        "answer":{"id":"p1","label":"Player One","type":"NFL_PLAYER"},
        "options":["Player One","Wrong A","Wrong B","Wrong C"],
        "difficulty_band":"HARD",
    }
    c.execute(
        """INSERT INTO story_generated_questions(
           question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
           difficulty_band,question_json,status,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        ("qstory-1","c1","e1","NFL_PLAYER","p1","MULTIPLE_CHOICE","HARD",
         json.dumps(q),"READY_FOR_BANK","2026-10-03T00:00:00Z"),
    )
    c.commit()
    return c


def test_shared_deep_trivia_pool_can_be_filled_by_story_factory(monkeypatch):
    c = _conn()
    monkeypatch.setattr(deep_trivia.engine_bootstrap, "connect", lambda: c)
    rounds = deep_trivia.generate_rounds("story-shared", 1)
    assert len(rounds) == 1
    assert rounds[0]["category"] == "Football Lore"
    assert rounds[0]["depth_source"] == "STORY_FACTORY"
    assert rounds[0]["prompt"] == "Who am I?"
