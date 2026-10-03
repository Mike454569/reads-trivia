import sqlite3

from tools.director_v05.story_factory_health import story_factory_health


def test_story_factory_health_reports_full_funnel():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    c.execute("CREATE TABLE football_story_candidates(candidate_id TEXT,status TEXT)")
    c.execute("CREATE TABLE football_story_enrichment(candidate_id TEXT,decision TEXT)")
    c.execute("CREATE TABLE story_generated_questions(question_id TEXT,mechanic TEXT,status TEXT)")
    c.executemany("INSERT INTO football_story_candidates VALUES(?,?)",[
        ("c1","PROMOTED"),("c2","REVIEW_REQUIRED"),("c3","REVIEW_REQUIRED_SENSITIVE")
    ])
    c.executemany("INSERT INTO football_story_enrichment VALUES(?,?)",[
        ("c1","AUTO_PROMOTED"),("c2","REVIEW_REQUIRED")
    ])
    c.executemany("INSERT INTO story_generated_questions VALUES(?,?,?)",[
        ("q1","MULTIPLE_CHOICE","READY_FOR_BANK"),
        ("q2","PROGRESSIVE_CLUE","READY_FOR_BANK"),
    ])
    out=story_factory_health(c)
    assert out["candidate_total"]==3
    assert out["promoted_events"]==1
    assert out["generated_question_total"]==2
    assert out["ready_for_bank"]==2
    assert out["promotion_rate"]==0.5
    assert out["questions_per_promoted_event"]==2.0
