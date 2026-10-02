import sqlite3
import pytest

from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.lore_trivia import compile_event_question, gameplay_eligibility
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    return c


def _seed_distractors(c):
    for i, typ in enumerate(("TRADE", "CONTRACT", "TRANSFER", "RECORD_EVENT"), start=1):
        upsert_event(c, {
            "event_type": typ,
            "league": "NFL",
            "event_date": f"{2010+i}-01-01",
            "title": f"Seed {typ}",
            "neutral_summary": f"Verified seed event {i}.",
            "source_url": f"https://example.com/{i}",
            "source_publisher": "Example",
            "evidence_tier": "AUTHORITATIVE",
            "verification_status": "VERIFIED",
            "subjects": [{"subject_type":"NFL_TEAM","subject_id":f"T{i}","role":"team"}],
        })


def test_verified_story_compiles_to_season_question():
    c = _conn()
    _seed_distractors(c)
    eid = upsert_event(c, {
        "event_type": "ON_FIELD_ODDITY",
        "league": "NFL",
        "event_date": "2022-01-01",
        "title": "Wild finish",
        "neutral_summary": "A verified game featured an unusual sequence of events.",
        "source_url": "https://example.com/wild",
        "source_publisher": "Example",
        "evidence_tier": "AUTHORITATIVE",
        "verification_status": "VERIFIED",
        "subjects": [{"subject_type":"GAME","subject_id":"g1","role":"game"}],
    })
    q = compile_event_question(c, eid, "SEASON")
    assert q["answer"]["id"] == "2022"
    assert q["question_family"] == "LORE_EVENT"
    assert len(q["options"]) == 4
    assert q["provenance"]["provenance_complete"] is True


def test_single_reputable_source_legal_event_is_not_gameplay_eligible():
    c = _conn()
    eid = upsert_event(c, {
        "event_type": "CHARGE",
        "league": "NFL",
        "event_date": "2020-01-01",
        "title": "Legal event",
        "neutral_summary": "A charge was reported.",
        "source_url": "https://example.com/report",
        "source_publisher": "News",
        "evidence_tier": "REPUTABLE_MEDIA",
        "verification_status": "VERIFIED",
        "legal_stage": "CHARGED",
        "allegation_or_offense": "Example offense",
        "jurisdiction": "Example County",
        "sensitive": True,
    })
    row = dict(c.execute("SELECT * FROM universal_event WHERE event_id=?", (eid,)).fetchone())
    gate = gameplay_eligibility(c, row)
    assert gate["eligible"] is False
    assert "SENSITIVE_NEEDS_CORROBORATION" in gate["reasons"]


def test_authoritative_legal_event_preserves_precise_stage_wording():
    c = _conn()
    _seed_distractors(c)
    eid = upsert_event(c, {
        "event_type": "CHARGE",
        "league": "NFL",
        "event_date": "2020-01-01",
        "title": "Legal event",
        "neutral_summary": "A charge was recorded.",
        "source_url": "https://example.gov/case",
        "source_publisher": "Court",
        "evidence_tier": "AUTHORITATIVE",
        "verification_status": "VERIFIED",
        "legal_stage": "CHARGED",
        "allegation_or_offense": "Example offense",
        "jurisdiction": "Example County",
        "sensitive": True,
    })
    q = compile_event_question(c, eid, "EVENT_TYPE")
    joined = " ".join(q["clues"])
    assert "Recorded legal stage: Charged." in joined
    assert "Reported allegation or offense: Example offense." in joined
    assert "convicted" not in joined.casefold()
