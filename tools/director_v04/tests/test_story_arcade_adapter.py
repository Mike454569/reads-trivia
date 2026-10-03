import json
import sqlite3

from tools.director_v04.story_arcade_adapter import load_story_mcqs


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE universal_event(
        event_id TEXT PRIMARY KEY,
        league TEXT,
        verification_status TEXT,
        sensitive INTEGER
    )""")
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


def _q(qid, aid, atype="COACH"):
    return {
        "question_id": qid,
        "mechanic": "MULTIPLE_CHOICE",
        "question": "Who am I?",
        "answer": {"id": aid, "label": "Coach One", "type": atype},
        "options": ["Coach One", "Coach Two", "Coach Three", "Coach Four"],
        "clues": [{"text":"A"},{"text":"B"},{"text":"C"}],
    }


def _insert(c, *, eid, league, verified="VERIFIED", sensitive=0, qid="q1"):
    c.execute(
        "INSERT INTO universal_event VALUES(?,?,?,?)",
        (eid, league, verified, sensitive),
    )
    q = _q(qid, "coach1")
    c.execute(
        "INSERT INTO story_generated_questions VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            qid, "cand", eid, "COACH", "coach1", "MULTIPLE_CHOICE", "HARD",
            json.dumps(q), "READY_FOR_BANK", "2026-10-03T00:00:00Z",
        ),
    )
    c.commit()


def test_coach_story_uses_verified_event_league():
    c = _conn()
    _insert(c, eid="e1", league="NFL")
    assert len(load_story_mcqs(c, league="NFL")) == 1
    assert load_story_mcqs(c, league="CFB") == []


def test_unverified_or_sensitive_story_never_enters_game_shell():
    c = _conn()
    _insert(c, eid="e1", league="NFL", verified="UNVERIFIED", qid="q1")
    _insert(c, eid="e2", league="NFL", sensitive=1, qid="q2")
    assert load_story_mcqs(c, league="NFL") == []
