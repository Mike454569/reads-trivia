import sqlite3

from tools.director_v05 import story_candidate_harvest as harvest
from tools.director_v05 import story_candidate_triage as triage


def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    harvest._ensure_schema(c)
    return c


def test_harvest_schema_and_url_canonicalization():
    c=_conn()
    url="https://www.espn.com/nfl/story?id=1&utm_source=test&fbclid=x"
    canon=harvest._canonical_url(url)
    assert "utm_source" not in canon
    assert "fbclid" not in canon
    assert harvest._domain(canon)=="espn.com"


def test_triage_rejects_betting_and_prioritizes_primary(monkeypatch):
    c=_conn()
    now="2026-10-03T00:00:00+00:00"
    rows=[
        ("a","https://www.nfl.com/a","Coach postgame press conference after wild NFL win","nfl.com","20261003",None,None,"PRESS_CONFERENCE","postgame","PRIMARY",0,"REVIEW_REQUIRED",now,now),
        ("b","https://www.espn.com/b","NFL betting odds and picks for Sunday","espn.com","20261003",None,None,"OFF_FIELD_ODDITY","weird","REPUTABLE_MEDIA",0,"REVIEW_REQUIRED",now,now),
    ]
    c.executemany(
        """INSERT INTO football_story_candidates(
        candidate_id,source_url,title,domain,seen_date,language,source_country,
        family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
        first_harvested_at,last_seen_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",rows)
    c.commit()
    monkeypatch.setattr(triage.engine_bootstrap,"connect",lambda:c)
    out=triage.triage_candidates(minimum_priority_score=30)
    assert out["status_counts"]["REVIEW_PRIORITY"]==1
    assert out["status_counts"]["REJECT_LOW_SIGNAL"]==1


def test_sensitive_candidates_never_auto_priority(monkeypatch):
    c=_conn()
    now="2026-10-03T00:00:00+00:00"
    c.execute(
        """INSERT INTO football_story_candidates(
        candidate_id,source_url,title,domain,seen_date,language,source_country,
        family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
        first_harvested_at,last_seen_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("s","https://www.nfl.com/s","NFL player suspended after league discipline","nfl.com","20261003",None,None,"DISCIPLINE_LEGAL","suspension","PRIMARY",1,"REVIEW_REQUIRED",now,now))
    c.commit()
    monkeypatch.setattr(triage.engine_bootstrap,"connect",lambda:c)
    out=triage.triage_candidates(minimum_priority_score=1)
    assert out["status_counts"]["REVIEW_REQUIRED_SENSITIVE"]==1
