import sqlite3
import pytest

from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.lore_mechanics import (
    compile_common_link,
    compile_fact_or_fake,
    compile_timeline,
)
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    return c


def _event(c, *, event_type, season, subject_type="NFL_TEAM", subject_id="AAA", sensitive=False,
           evidence_tier="AUTHORITATIVE", legal_stage=None, allegation_or_offense=None, jurisdiction=None):
    return upsert_event(c, {
        "event_type": event_type,
        "league": "NFL",
        "event_date": str(season) + "-01-01",
        "title": event_type.replace("_", " ").title() + " story",
        "neutral_summary": "Verified football story for testing.",
        "source_url": f"https://example.com/{event_type.lower()}-{season}-{subject_id}",
        "source_publisher": "Example",
        "evidence_tier": evidence_tier,
        "verification_status": "VERIFIED",
        "legal_stage": legal_stage,
        "allegation_or_offense": allegation_or_offense,
        "jurisdiction": jurisdiction,
        "sensitive": sensitive,
        "subjects": [{"subject_type": subject_type, "subject_id": subject_id, "role": "subject"}],
    })


def test_fact_or_fake_mutates_only_safe_structural_fact():
    c = _conn()
    eid = _event(c, event_type="ON_FIELD_ODDITY", season=2021)
    q = compile_fact_or_fake(c, eid, fake=True)
    assert q["answer"]["id"] == "FAKE"
    assert q["mutation"]["field"] == "season"
    assert q["mutation"]["actual"] == "2021"
    assert q["mutation"]["shown"] == "2022"


def test_sensitive_legal_lore_cannot_generate_fake_variant():
    c = _conn()
    eid = _event(
        c,
        event_type="CHARGE",
        season=2020,
        subject_type="NFL_PLAYER",
        subject_id="p1",
        sensitive=True,
        legal_stage="CHARGED",
        allegation_or_offense="Example offense",
        jurisdiction="Example County",
    )
    with pytest.raises(ValueError, match="NO_FAKE_VARIANTS_FOR_SENSITIVE_LORE"):
        compile_fact_or_fake(c, eid, fake=True)


def test_timeline_requires_unique_seasons():
    c = _conn()
    ids = [
        _event(c, event_type="TRADE", season=2019, subject_id="A"),
        _event(c, event_type="CONTRACT", season=2020, subject_id="B"),
        _event(c, event_type="TRANSFER", season=2020, subject_id="C"),
        _event(c, event_type="RECORD_EVENT", season=2022, subject_id="D"),
    ]
    with pytest.raises(ValueError, match="TIMELINE_REQUIRES_UNIQUE_SEASONS"):
        compile_timeline(c, ids)


def test_common_link_requires_three_verified_events():
    c = _conn()
    _event(c, event_type="TRADE", season=2019, subject_type="NFL_PLAYER", subject_id="p1")
    _event(c, event_type="CONTRACT", season=2020, subject_type="NFL_PLAYER", subject_id="p1")
    with pytest.raises(ValueError, match="INSUFFICIENT_COMMON_LINK_EVENTS"):
        compile_common_link(c, "NFL_PLAYER", "p1")


def test_common_link_builds_from_three_verified_events():
    c = _conn()
    for season, typ in [(2019, "TRADE"), (2020, "CONTRACT"), (2021, "RECORD_EVENT")]:
        _event(c, event_type=typ, season=season, subject_type="NFL_PLAYER", subject_id="p1")
    q = compile_common_link(c, "NFL_PLAYER", "p1")
    assert q["mechanic"] == "COMMON_LINK"
    assert q["answer"]["id"] == "p1"
    assert len(q["clues"]) == 3
    assert q["provenance"]["provenance_complete"] is True
