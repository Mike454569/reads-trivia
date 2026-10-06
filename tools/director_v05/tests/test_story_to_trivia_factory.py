import json
import sqlite3

from tools.director_v05 import story_to_trivia_factory as factory
from tools.director_v05.story_candidate_harvest import _ensure_schema as ensure_candidate_schema
from tools.director_v05.story_to_trivia_factory import _ensure_schema as ensure_factory_schema
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    ensure_candidate_schema(c)
    ensure_factory_schema(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1","Player One"))
    return c


def _candidate(c, *, cid="c1", sensitive=0, family="PRESS_CONFERENCE", domain="nfl.com"):
    c.execute(
        """INSERT INTO football_story_candidates(
           candidate_id,source_url,title,domain,seen_date,language,source_country,
           family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
           first_harvested_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            cid,
            "https://" + domain + "/story",
            "Player One postgame press conference",
            domain,
            "20261003",
            "English",
            "United States",
            family,
            "postgame",
            "PRIMARY" if domain == "nfl.com" else "REPUTABLE_MEDIA",
            sensitive,
            "REVIEW_PRIORITY",
            "2026-10-03T00:00:00+00:00",
            "2026-10-03T00:00:00+00:00",
        ),
    )
    c.commit()
    return c.execute(
        "SELECT * FROM football_story_candidates WHERE candidate_id=?", (cid,)
    ).fetchone()


def _article():
    return {
        "final_url":"https://nfl.com/story",
        "domain":"nfl.com",
        "headline":"Player One addresses reporters after NFL win",
        "description":"Player One spoke to reporters after the game.",
        "published":"2026-10-03T04:00:00Z",
        "text":(
            "Player One spoke to reporters during a postgame press conference after the NFL game. "
            "The quarterback answered questions about the offense and the final drive. " * 8
        ),
        "text_chars":1200,
    }


def test_sensitive_candidate_never_fetches_or_promotes(monkeypatch):
    c = _conn()
    row = _candidate(c, sensitive=1, family="DISCIPLINE_LEGAL")

    def boom(*a, **k):
        raise AssertionError("sensitive candidate should not fetch")
    monkeypatch.setattr(factory, "fetch_article", boom)

    out = factory.process_candidate(c, row, factory.build_subject_index(c))
    assert out["decision"] == "REVIEW_REQUIRED_SENSITIVE"
    assert c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0] == 0


def test_high_confidence_primary_story_promotes_and_generates(monkeypatch):
    c = _conn()
    row = _candidate(c)
    monkeypatch.setattr(factory, "fetch_article", lambda url: _article())
    fake_q = {
        "question_id":"q-story-1",
        "mechanic":"MULTIPLE_CHOICE",
        "question":"Who am I?",
        "clues":[{"text":"Clue A"},{"text":"Clue B"},{"text":"Clue C"}],
        "answer":{"id":"p1","label":"Player One","type":"NFL_PLAYER"},
        "options":["Player One","Player Two","Player Three","Player Four"],
        "difficulty_band":"HARD",
    }
    monkeypatch.setattr(
        factory,
        "generate_questions_for_event",
        lambda c, candidate_id, event_id, subject, **kwargs: [fake_q],
    )
    monkeypatch.setattr(
        factory,
        "generate_story_formats_for_event",
        lambda *a, **k: {"generated_count":0,"generated":[],"rejected":[]},
    )

    out = factory.process_candidate(c, row, factory.build_subject_index(c))
    assert out["decision"] == "AUTO_PROMOTED"
    assert out["generated"] == 1

    event = c.execute("SELECT * FROM universal_event").fetchone()
    assert event["event_type"] == "PRESS_CONFERENCE"
    assert event["event_date"] is None
    assert event["source_date"].startswith("2026-10-03")
    assert "Player One" in event["neutral_summary"]

    enriched = c.execute(
        "SELECT decision,generated_question_count FROM football_story_enrichment"
    ).fetchone()
    assert enriched["decision"] == "AUTO_PROMOTED"
    assert enriched["generated_question_count"] == 1


def test_ambiguous_subject_stays_review_required(monkeypatch):
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p2","Second Player"))
    row = _candidate(c)
    article = _article()
    article["headline"] = "Player One and Second Player address reporters"
    article["text"] = (
        "Player One and Second Player spoke to reporters in a postgame press conference. " * 20
    )
    monkeypatch.setattr(factory, "fetch_article", lambda url: article)

    out = factory.process_candidate(c, row, factory.build_subject_index(c))
    assert out["decision"] == "REVIEW_REQUIRED"
    assert c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0] == 0


def test_generated_question_persistence_marks_ready_for_bank():
    c = _conn()
    q = {
        "question_id":"q1",
        "mechanic":"MULTIPLE_CHOICE",
        "question":"Who am I?",
        "clues":[{"text":"A"},{"text":"B"},{"text":"C"}],
        "answer":{"id":"p1","label":"Player One","type":"NFL_PLAYER"},
        "options":["Player One","A","B","C"],
        "difficulty_band":"HARD",
    }
    factory._persist_question(
        c,
        "candidate-1",
        "event-1",
        {"entity_type":"NFL_PLAYER","entity_id":"p1"},
        q,
    )
    row = c.execute("SELECT * FROM story_generated_questions").fetchone()
    assert row["status"] == "READY_FOR_BANK"
    assert json.loads(row["question_json"])["question_id"] == "q1"
