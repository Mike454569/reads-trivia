import json
import sqlite3

from tools.director_v05.certify_story_question_quality import certify_story_question_quality
from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.story_to_trivia_factory import _ensure_schema
from tools.director_v05.universal_schema import install


def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    install(c)
    _ensure_schema(c)
    return c


def _event(c,eid,sensitive=False):
    upsert_event(c,{
        "event_id":eid,"event_type":"OFF_FIELD_ODDITY","league":"NFL",
        "event_date":None,"title":"Story","neutral_summary":"A documented football story.",
        "source_url":"https://www.nfl.com/"+eid,"source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY","verification_status":"VERIFIED",
        "subjects":[{"subject_type":"NFL_PLAYER","subject_id":"p1","role":"subject"}],
        "tags":["story_factory"],"sensitive":sensitive,
    })


def _insert(c,q,eid,status="READY_FOR_BANK"):
    c.execute(
        """INSERT INTO story_generated_questions(
           question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
           difficulty_band,question_json,status,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (q["question_id"],"cand",eid,"NFL_PLAYER","p1",q["mechanic"],"HARD",
         json.dumps(q),status,"2026-10-03T00:00:00Z"),
    )
    c.commit()


def test_quality_cert_accepts_clean_story_mcq():
    c=_conn();_event(c,"e1")
    q={
        "question_id":"q1","mechanic":"MULTIPLE_CHOICE","question_family":"LORE_IDENTITY",
        "question":"Who am I?","clues":[{"text":"Clue one"},{"text":"Clue two"},{"text":"Clue three"}],
        "answer":{"id":"p1","label":"Player One","type":"NFL_PLAYER"},
        "options":["Player One","Player Two","Player Three","Player Four"],
        "event_id":"e1","provenance":{"event_ids":["e1"]},
    }
    _insert(c,q,"e1")
    out=certify_story_question_quality(c)
    assert out["status"]=="PASSED"
    assert out["passed"]==1
    assert out["failed"]==0


def test_quality_cert_accepts_progressive_artifact_without_mcq_options():
    c=_conn();_event(c,"e1")
    q={
        "question_id":"q1","mechanic":"PROGRESSIVE_CLUE","question_family":"LORE_IDENTITY",
        "question":"Who am I?","clues":[{"text":"One"},{"text":"Two"},{"text":"Three"}],
        "answer":{"id":"p1","label":"Player One","type":"NFL_PLAYER"},
        "event_id":"e1","provenance":{"event_ids":["e1"]},
    }
    _insert(c,q,"e1")
    out=certify_story_question_quality(c)
    assert out["failed"]==0


def test_quality_cert_rejects_sensitive_fact_fake():
    c=_conn();_event(c,"e1",sensitive=True)
    q={
        "question_id":"q1","mechanic":"FACT_OR_FAKE","question_family":"LORE_EVENT",
        "question":"This happened.","answer":{"id":"FACT","label":"Fact","type":"BOOLEAN"},
        "event_id":"e1","provenance":{"event_ids":["e1"]},
    }
    _insert(c,q,"e1","READY_FOR_FORMAT_BANK")
    out=certify_story_question_quality(c)
    assert out["failed"]==1
    assert any(k.startswith("SENSITIVE_FACT_FAKE") for k in out["failure_reasons"])



def test_quality_cert_rejects_identity_answer_leakage():
    c=_conn();_event(c,"e1")
    q={
        "question_id":"q-leak","mechanic":"PROGRESSIVE_CLUE","question_family":"LORE_IDENTITY",
        "question":"Who am I?",
        "clues":[
            {"text":"League: NFL."},
            {"text":"Player One was featured in a documented media appearance."},
            {"text":"This player discussed an unusual football moment."},
        ],
        "answer":{"id":"p1","label":"Player One","type":"NFL_PLAYER"},
        "event_id":"e1","provenance":{"event_ids":["e1"]},
    }
    _insert(c,q,"e1","READY_FOR_FORMAT_BANK")
    out=certify_story_question_quality(c)
    assert out["failed"]==1
    assert "PROGRESSIVE_ANSWER_LEAKAGE" in out["failure_reasons"]
