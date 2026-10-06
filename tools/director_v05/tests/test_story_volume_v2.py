import datetime as dt
import sqlite3

from tools.director_v05 import story_candidate_harvest as harvest
from tools.director_v05 import story_candidate_triage as triage
from tools.director_v05.story_corpus_growth import FAMILY_GROUPS


def _candidate_conn(path):
    c=sqlite3.connect(path)
    c.row_factory=sqlite3.Row
    harvest._ensure_schema(c)
    return c


def test_growth_family_groups_cover_expanded_safe_and_sensitive_families():
    covered={x for values in FAMILY_GROUPS.values() for x in values}
    required={
        "DRAFT_CHAOS","TRADE_CHAOS","BUST_REDEMPTION","COMEBACK_RETURN",
        "GAME_ODDITY","RIVALRY_ODDITY","COACHING_ODDITY","RULE_ODDITY",
        "PRESS_CONFERENCE","OFF_FIELD_ODDITY","CELEBRATION_FAN","DISCIPLINE_LEGAL",
    }
    assert required <= covered
    assert covered <= set(harvest.QUERY_FAMILIES)


def test_sensitive_title_overrides_safe_harvest_family(monkeypatch,tmp_path):
    db=tmp_path/"stories.sqlite"
    c=_candidate_conn(db)
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    c.execute(
        """INSERT INTO football_story_candidates(
           candidate_id,source_url,title,domain,seen_date,language,source_country,
           family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
           first_harvested_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "cand1","https://www.nfl.com/story1",
            "NFL player suspended after sideline celebration incident",
            "nfl.com","20261005T120000Z","English","US",
            "CELEBRATION_FAN","football celebration","PRIMARY",0,
            "REVIEW_REQUIRED",now,now,
        ),
    )
    c.commit()
    c.close()
    def connect():
        x=sqlite3.connect(db); x.row_factory=sqlite3.Row; return x
    monkeypatch.setattr(triage.engine_bootstrap,"connect",connect)
    out=triage.triage_candidates(minimum_priority_score=0)
    check=connect()
    row=check.execute(
        "SELECT status FROM football_story_candidates WHERE candidate_id='cand1'"
    ).fetchone()
    assert row["status"]=="REVIEW_REQUIRED_SENSITIVE"
    assert out["status_counts"]["REVIEW_REQUIRED_SENSITIVE"]==1
    check.close()


def test_non_sensitive_expanded_family_can_reach_priority(monkeypatch,tmp_path):
    db=tmp_path/"stories.sqlite"
    c=_candidate_conn(db)
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    c.execute(
        """INSERT INTO football_story_candidates(
           candidate_id,source_url,title,domain,seen_date,language,source_country,
           family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
           first_harvested_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "cand2","https://www.nfl.com/story2",
            "NFL quarterback completes remarkable career comeback",
            "nfl.com","20261005T120000Z","English","US",
            "COMEBACK_RETURN","NFL comeback retirement player","PRIMARY",0,
            "REVIEW_REQUIRED",now,now,
        ),
    )
    c.commit()
    c.close()
    def connect():
        x=sqlite3.connect(db); x.row_factory=sqlite3.Row; return x
    monkeypatch.setattr(triage.engine_bootstrap,"connect",connect)
    triage.triage_candidates(minimum_priority_score=30)
    check=connect()
    row=check.execute(
        "SELECT status FROM football_story_candidates WHERE candidate_id='cand2'"
    ).fetchone()
    assert row["status"]=="REVIEW_PRIORITY"
    check.close()
