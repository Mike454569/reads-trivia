import sqlite3

from gateway.services import story_review
from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.story_candidate_harvest import _ensure_schema as ensure_candidates
from tools.director_v05.story_review_assistant import _ensure_schema as ensure_suggestions
from tools.director_v05.story_to_trivia_factory import _ensure_schema as ensure_factory
from tools.director_v05.universal_schema import install


def _connect_factory(path):
    def _connect():
        c = sqlite3.connect(path)
        c.row_factory = sqlite3.Row
        return c
    return _connect


def _seed(path):
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    install(c)
    ensure_candidates(c)
    ensure_factory(c)
    ensure_suggestions(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1","Player One"))
    c.execute(
        """INSERT INTO football_story_candidates(
           candidate_id,source_url,title,domain,seen_date,language,source_country,
           family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
           first_harvested_at,last_seen_at,promoted_event_id)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "c1","https://www.nfl.com/story","Player One story","nfl.com",
            "20261003","English","US","OFF_FIELD_ODDITY","weird","PRIMARY",
            0,"PROMOTED","2026-10-03T00:00:00Z","2026-10-03T00:00:00Z","e1",
        ),
    )
    upsert_event(c, {
        "event_id":"e1",
        "event_type":"OFF_FIELD_ODDITY",
        "league":"NFL",
        "event_date":None,
        "title":"Player One unusual story",
        "neutral_summary":"Player One was involved in a documented unusual football story.",
        "source_url":"https://www.nfl.com/story",
        "source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY",
        "verification_status":"VERIFIED",
        "subjects":[{"subject_type":"NFL_PLAYER","subject_id":"p1","role":"subject"}],
        "tags":["story_factory"],
        "sensitive":False,
    })
    c.execute(
        """INSERT INTO football_story_enrichment(
           candidate_id,subject_type,subject_id,decision,promoted_event_id,
           generated_question_count,processed_at,evidence_terms_json)
           VALUES(?,?,?,?,?,?,?,?)""",
        (
            "c1","NFL_PLAYER","p1","AUTO_PROMOTED","e1",0,
            "2026-10-03T00:00:00Z","[]",
        ),
    )
    c.execute(
        """INSERT INTO story_review_suggestions(
           candidate_id,source_url,family_hint,suggested_event_type,
           suggested_league,suggested_subject_type,suggested_subject_id,
           suggested_subject_label,suggested_event_date,date_basis,
           publication_date,suggested_legal_stage,evidence_terms_json,
           risk_flags_json,confidence,status,generated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "c1","https://www.nfl.com/story","OFF_FIELD_ODDITY",
            "OFF_FIELD_ODDITY","NFL","NFL_PLAYER","p1","Player One",
            "2026-09-28","SINGLE_EXPLICIT_ARTICLE_DATE","2026-10-03",
            None,"[]",'["EVENT_DATE_REQUIRES_REVIEW"]',90,
            "SUGGESTED_ONLY","2026-10-03T00:00:00Z",
        ),
    )
    c.commit()
    c.close()


def test_confirm_event_date_updates_promoted_event_and_suggestion(tmp_path, monkeypatch):
    path = str(tmp_path / "story.sqlite")
    _seed(path)
    monkeypatch.setattr(story_review.engine_bootstrap, "connect", _connect_factory(path))

    result = story_review.confirm_event_date(
        candidate_id="c1",
        event_date="2026-09-28",
    )
    assert result["event_date"] == "2026-09-28"
    assert result["event_id"] == "e1"

    c = _connect_factory(path)()
    event = c.execute("SELECT event_date FROM universal_event WHERE event_id='e1'").fetchone()
    suggestion = c.execute(
        "SELECT status FROM story_review_suggestions WHERE candidate_id='c1'"
    ).fetchone()
    c.close()
    assert event["event_date"] == "2026-09-28"
    assert suggestion["status"] == "DATE_CONFIRMED"


def test_confirm_event_date_refuses_conflicting_second_date(tmp_path, monkeypatch):
    path = str(tmp_path / "story.sqlite")
    _seed(path)
    monkeypatch.setattr(story_review.engine_bootstrap, "connect", _connect_factory(path))

    story_review.confirm_event_date(candidate_id="c1", event_date="2026-09-28")
    try:
        story_review.confirm_event_date(candidate_id="c1", event_date="2026-09-29")
        assert False, "expected conflicting date rejection"
    except ValueError as exc:
        assert str(exc) == "EVENT_DATE_ALREADY_CONFIRMED_DIFFERENTLY"


def test_review_queue_exposes_suggestions_without_article_body(tmp_path, monkeypatch):
    path = str(tmp_path / "story.sqlite")
    _seed(path)
    c = _connect_factory(path)()
    c.execute(
        "UPDATE football_story_candidates SET status='REVIEW_REQUIRED' WHERE candidate_id='c1'"
    )
    c.commit()
    c.close()
    monkeypatch.setattr(story_review.engine_bootstrap, "connect", _connect_factory(path))

    out = story_review.review_queue(limit=10, include_sensitive=True)
    assert out["count"] == 1
    item = out["items"][0]
    assert item["candidate_id"] == "c1"
    assert item["suggested_subject_label"] == "Player One"
    assert item["suggested_event_date"] == "2026-09-28"
    assert "risk_flags" in item
    assert "article_text" not in item
