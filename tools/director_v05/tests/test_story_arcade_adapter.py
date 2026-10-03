import json
import sqlite3

from tools.director_v04.story_arcade_adapter import load_story_mcqs
from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.story_to_trivia_factory import _ensure_schema
from tools.director_v05.universal_schema import install


def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    install(c)
    _ensure_schema(c)
    return c


def _seed_question(c, qid, eid, subject_type, subject_id, league):
    upsert_event(c,{
        "event_id":eid,"event_type":"OFF_FIELD_ODDITY","league":league,
        "event_date":None,"title":"Story","neutral_summary":"Documented story.",
        "source_url":"https://www.nfl.com/"+eid if league=="NFL" else "https://www.ncaa.org/"+eid,
        "source_publisher":"NFL.com" if league=="NFL" else "NCAA",
        "evidence_tier":"PRIMARY","verification_status":"VERIFIED",
        "subjects":[{"subject_type":subject_type,"subject_id":subject_id,"role":"subject"}],
        "tags":["story_factory"],"sensitive":False,
    })
    q={
        "question_id":qid,"mechanic":"MULTIPLE_CHOICE","question":"Who am I?",
        "clues":[{"text":"A"},{"text":"B"},{"text":"C"}],
        "answer":{"id":subject_id,"label":"Answer "+subject_id,"type":subject_type},
        "options":["Answer "+subject_id,"Wrong A","Wrong B","Wrong C"],
    }
    c.execute(
        """INSERT INTO story_generated_questions(
           question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
           difficulty_band,question_json,status,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (qid,"cand-"+qid,eid,subject_type,subject_id,"MULTIPLE_CHOICE","HARD",
         json.dumps(q),"READY_FOR_BANK","2026-10-03T00:00:00Z"),
    )
    c.commit()


def test_story_adapter_uses_event_league_for_coaches():
    c=_conn()
    _seed_question(c,"q-nfl","e-nfl","COACH","coach-nfl","NFL")
    _seed_question(c,"q-cfb","e-cfb","COACH","coach-cfb","CFB")

    nfl=load_story_mcqs(c,limit=10,league="NFL")
    cfb=load_story_mcqs(c,limit=10,league="CFB")
    assert [q["question_id"] for q in nfl]==["q-nfl"]
    assert [q["question_id"] for q in cfb]==["q-cfb"]


def test_story_adapter_rejects_unknown_league_for_league_specific_shell():
    c=_conn()
    # No event row on purpose; an ambiguous coach question must not enter an
    # NFL- or CFB-only shell merely because the answer type is COACH.
    q={
        "question_id":"q-amb","mechanic":"MULTIPLE_CHOICE","question":"Who am I?",
        "clues":[{"text":"A"},{"text":"B"},{"text":"C"}],
        "answer":{"id":"coach-x","label":"Coach X","type":"COACH"},
        "options":["Coach X","A","B","C"],
    }
    c.execute(
        """INSERT INTO story_generated_questions(
           question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
           difficulty_band,question_json,status,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        ("q-amb","c","missing","COACH","coach-x","MULTIPLE_CHOICE","HARD",
         json.dumps(q),"READY_FOR_BANK","2026-10-03T00:00:00Z"),
    )
    c.commit()
    assert load_story_mcqs(c,limit=10,league="NFL")==[]
    assert load_story_mcqs(c,limit=10,league="CFB")==[]
