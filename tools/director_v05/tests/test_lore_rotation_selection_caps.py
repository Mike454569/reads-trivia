import sqlite3

from tools.director_v05.lore_rotation import select_rotated_questions
from tools.director_v05.universal_schema import install
from tools.director_v05.event_ingest import upsert_event

def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    install(c)
    return c

def _question(qid, answer, event_id, relation="SUBJECT_OF_EVENT"):
    return {
        "question_id":qid,
        "answer":{"id":answer,"label":answer,"type":"NFL_PLAYER"},
        "clues":[{"relation":relation,"text":"A sufficiently detailed clue here"}],
        "provenance":{"chain":{"hops":[{"object_type":"EVENT","object_id":event_id}]}},
        "rarity_score":10,
        "difficulty_score":50,
    }

def test_rotation_counts_only_actual_selections():
    c=_conn()
    for eid in ("e1","e2","e3"):
        upsert_event(c,{
            "event_id":eid,"event_type":"OFF_FIELD_ODDITY","league":"NFL",
            "event_date":"2020-01-01","title":eid,"neutral_summary":"Documented football event.",
            "source_url":"https://www.nfl.com/"+eid,"source_publisher":"NFL.com",
            "evidence_tier":"PRIMARY","verification_status":"VERIFIED",
            "subjects":[{"subject_type":"NFL_PLAYER","subject_id":eid,"role":"subject"}],
            "tags":["test"],"sensitive":False,
        })
    # q1 and q2 share the same answer. The scheduler may consider both, but
    # only the actually selected one is allowed to consume the answer cap.
    rows=[
        _question("q1","same","e1"),
        _question("q2","same","e2"),
        _question("q3","other","e3"),
    ]
    out=select_rotated_questions(c,rows,target=2,max_per_answer=1,max_per_signature=3)
    assert len(out["selected"])==2
    answers=[q["answer"]["id"] for q in out["selected"]]
    assert len(set(answers))==2
    assert out["answer_counts"]["same"]==1
