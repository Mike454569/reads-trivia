import json
import sqlite3

from tools.director_v05.story_question_pool import load_ready_story_questions


def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    c.execute("""CREATE TABLE story_generated_questions(
        question_id TEXT PRIMARY KEY,
        candidate_id TEXT,
        event_id TEXT,
        subject_type TEXT,
        subject_id TEXT,
        mechanic TEXT,
        difficulty_band TEXT,
        question_json TEXT,
        status TEXT,
        created_at TEXT
    )""")
    return c


def _q(qid, aid, mechanic="MULTIPLE_CHOICE"):
    return {
        "question_id":qid,
        "mechanic":mechanic,
        "question":"Who am I?",
        "clues":[{"text":"A"},{"text":"B"},{"text":"C"}],
        "answer":{"id":aid,"label":"Player "+aid,"type":"NFL_PLAYER"},
        "options":["Player "+aid,"Wrong A","Wrong B","Wrong C"] if mechanic=="MULTIPLE_CHOICE" else [],
    }


def test_story_pool_returns_only_ready_playable_mcq():
    c=_conn()
    for i,(status,mechanic) in enumerate([
        ("READY_FOR_BANK","MULTIPLE_CHOICE"),
        ("READY_FOR_BANK","PROGRESSIVE_CLUE"),
        ("REJECTED","MULTIPLE_CHOICE"),
    ],start=1):
        q=_q("q"+str(i),"p"+str(i),mechanic)
        c.execute("INSERT INTO story_generated_questions VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (q["question_id"],"c","e","NFL_PLAYER",q["answer"]["id"],mechanic,"HARD",
                   json.dumps(q),status,"2026-10-03T00:00:00Z"))
    out=load_ready_story_questions(c,limit=10)
    assert [q["question_id"] for q in out]==["q1"]


def test_story_pool_respects_recent_question_and_answer_ids():
    c=_conn()
    for i in range(1,3):
        q=_q("q"+str(i),"p"+str(i))
        c.execute("INSERT INTO story_generated_questions VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (q["question_id"],"c","e","NFL_PLAYER",q["answer"]["id"],q["mechanic"],"HARD",
                   json.dumps(q),"READY_FOR_BANK","2026-10-03T00:00:00Z"))
    out=load_ready_story_questions(
        c,
        recent_question_ids={"q1"},
        recent_answer_ids={"p2"},
        limit=10,
    )
    assert out==[]
