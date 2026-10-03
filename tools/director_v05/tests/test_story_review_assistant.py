import sqlite3

from tools.director_v05 import story_review_assistant as review
from tools.director_v05.story_candidate_harvest import _ensure_schema as ensure_candidates
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    ensure_candidates(c)
    review._ensure_schema(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1","Player One"))
    return c


def _candidate(c, *, sensitive=0, family="PRESS_CONFERENCE"):
    c.execute(
        """INSERT INTO football_story_candidates(
           candidate_id,source_url,title,domain,seen_date,language,source_country,
           family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
           first_harvested_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "c1","https://www.nfl.com/story","Player One postgame comments",
            "nfl.com","20261003","English","US",family,"postgame",
            "PRIMARY",sensitive,
            "REVIEW_REQUIRED_SENSITIVE" if sensitive else "REVIEW_REQUIRED",
            "2026-10-03T00:00:00Z","2026-10-03T00:00:00Z",
        ),
    )
    c.commit()
    return c.execute("SELECT * FROM football_story_candidates").fetchone()


def test_review_assistant_suggests_explicit_nonpublication_event_date(monkeypatch):
    c = _conn()
    row = _candidate(c)
    article = {
        "final_url":"https://www.nfl.com/story",
        "domain":"nfl.com",
        "headline":"Player One addresses reporters after NFL game",
        "description":"Player One spoke in a postgame press conference.",
        "published":"2026-10-03T12:00:00Z",
        "text":(
            "On September 28, 2026, Player One addressed reporters in a postgame "
            "press conference after the NFL game. He answered questions about the result. "
        ) * 8,
        "text_chars":1200,
    }
    monkeypatch.setattr(review,"fetch_article",lambda url:article)

    out = review.suggest_candidate(c,row,review.build_subject_index(c))
    assert out["status"] == "SUGGESTED_ONLY"
    assert out["suggested_subject_id"] == "p1"
    assert out["suggested_event_type"] == "PRESS_CONFERENCE"
    assert out["suggested_event_date"] == "2026-09-28"
    assert out["publication_date"] == "2026-10-03"
    assert out["date_basis"] == "SINGLE_EXPLICIT_ARTICLE_DATE"

    event_count = c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0]
    assert event_count == 0


def test_sensitive_review_suggestion_never_becomes_approval(monkeypatch):
    c = _conn()
    row = _candidate(c,sensitive=1,family="DISCIPLINE_LEGAL")
    article = {
        "final_url":"https://www.nfl.com/story",
        "domain":"nfl.com",
        "headline":"Player One suspended by NFL",
        "description":"The NFL announced a suspension.",
        "published":"2026-10-03T12:00:00Z",
        "text":(
            "Player One was suspended by the NFL following league discipline. "
            "The suspension was announced by the league. "
        ) * 10,
        "text_chars":1000,
    }
    monkeypatch.setattr(review,"fetch_article",lambda url:article)

    out = review.suggest_candidate(c,row,review.build_subject_index(c))
    assert out["status"] == "SUGGESTED_ONLY"
    assert out["suggested_event_type"] == "LEAGUE_DISCIPLINE"
    assert out["suggested_legal_stage"] == "SUSPENSION"
    assert "SENSITIVE_MANUAL_REVIEW_REQUIRED" in out["risk_flags"]
    assert out["confidence"] <= 75

    stored = c.execute(
        "SELECT status,risk_flags_json FROM story_review_suggestions"
    ).fetchone()
    assert stored["status"] == "SUGGESTED_ONLY"
    assert "SENSITIVE_MANUAL_REVIEW_REQUIRED" in stored["risk_flags_json"]
    assert c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0] == 0


def test_multiple_dates_do_not_auto_suggest_chronology(monkeypatch):
    c = _conn()
    row = _candidate(c)
    article = {
        "final_url":"https://www.nfl.com/story",
        "domain":"nfl.com",
        "headline":"Player One postgame press conference",
        "description":"A media appearance.",
        "published":"2026-10-03T12:00:00Z",
        "text":(
            "Player One spoke to reporters after games on September 20, 2026 and "
            "September 28, 2026 during a postgame press conference discussion. "
        ) * 8,
        "text_chars":1100,
    }
    monkeypatch.setattr(review,"fetch_article",lambda url:article)

    out = review.suggest_candidate(c,row,review.build_subject_index(c))
    assert out["suggested_event_date"] is None
    assert "EVENT_DATE_REQUIRES_REVIEW" in out["risk_flags"]
