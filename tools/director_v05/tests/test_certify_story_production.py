import sqlite3

from tools.director_v05 import certify_story_production as cert


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE football_story_candidates(
        candidate_id TEXT PRIMARY KEY,status TEXT,title TEXT,domain TEXT,family_hint TEXT
    )""")
    c.execute("""CREATE TABLE football_story_enrichment(
        candidate_id TEXT PRIMARY KEY,decision TEXT,decision_reason TEXT,
        promoted_event_id TEXT
    )""")
    c.execute("""CREATE TABLE story_review_suggestions(
        candidate_id TEXT PRIMARY KEY,status TEXT,risk_flags_json TEXT,
        confidence INTEGER,suggested_subject_id TEXT
    )""")
    return c


def test_rejection_breakdown_counts_identity_and_fetch_failures():
    c = _conn()
    c.executemany(
        "INSERT INTO football_story_candidates VALUES(?,?,?,?,?)",
        [
            ("c1","REVIEW_REQUIRED","A","nfl.com","PRESS_CONFERENCE"),
            ("c2","REVIEW_REQUIRED","B","espn.com","OFF_FIELD_ODDITY"),
        ],
    )
    c.executemany(
        "INSERT INTO football_story_enrichment VALUES(?,?,?,?)",
        [
            ("c1","REVIEW_REQUIRED","NO_SINGLE_CANONICAL_PERSON_SUBJECT",None),
            ("c2","REVIEW_REQUIRED","ARTICLE_FETCH:ValueError:ARTICLE_TEXT_TOO_THIN",None),
        ],
    )
    c.executemany(
        "INSERT INTO story_review_suggestions VALUES(?,?,?,?,?)",
        [
            ("c1","SUGGESTED_ONLY",'["NO_SINGLE_CANONICAL_PERSON_SUBJECT"]',40,None),
            ("c2","SUGGESTED_ONLY",'["EVENT_DATE_REQUIRES_REVIEW"]',60,"p2"),
        ],
    )
    out = cert._rejection_breakdown(c)
    assert out["identity_failures"] == 1
    assert out["article_fetch_failures"] == 1
    assert out["review_risk_flags"]["NO_SINGLE_CANONICAL_PERSON_SUBJECT"] == 1


def test_remediation_queue_prioritizes_qa_before_scale():
    health = {
        "candidate_total": 500,
        "promoted_events": 5,
        "ready_for_bank": 3,
        "ready_for_format_bank": 2,
        "review_backlog": 20,
        "sensitive_backlog": 5,
        "league_balance": {"NFL": 5, "CFB": 0},
    }
    quality = {"status":"FAILED","failed":7}
    reach = {
        "corpus_ready":True,
        "promotion_ready":False,
        "games_with_story_content":3,
        "games_tested":20,
    }
    rejects = {
        "identity_failures":12,
        "article_fetch_failures":0,
        "family_evidence_failures":0,
    }
    queue = cert._remediation_queue(health, quality, reach, rejects)
    assert queue[0]["code"] == "QUESTION_QA_FAILURES"
    codes = {x["code"] for x in queue}
    assert "CORPUS_TOO_SMALL" in codes
    assert "IDENTITY_RESOLUTION_GAP" in codes
    assert "TOO_FEW_PLAYABLE_MCQS" in codes
    assert "GAME_REACH_INCOMPLETE" in codes
