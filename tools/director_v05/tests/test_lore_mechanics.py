import sqlite3
import pytest

from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.lore_mechanics import (
    compile_common_link,
    compile_fact_or_fake,
    compile_mixed_lore_stat,
    compile_progressive_identity,
    compile_timeline,
)
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("""CREATE TABLE draft_facts(
        player_key TEXT, draft_season INTEGER, draft_round INTEGER,
        draft_pick_overall INTEGER, draft_team TEXT,
        verification_status TEXT
    )""")
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


def test_undated_story_cannot_fabricate_metadata_fake():
    c = _conn()
    eid = upsert_event(c, {
        "event_id": "story-undated",
        "event_type": "OFF_FIELD_ODDITY",
        "league": "NFL",
        "event_date": None,
        "title": "Documented story",
        "neutral_summary": "A player was the subject of a documented off-field football story.",
        "source_url": "https://example.com/story-undated",
        "source_publisher": "Example",
        "evidence_tier": "AUTHORITATIVE",
        "verification_status": "VERIFIED",
        "subjects": [{"subject_type": "NFL_PLAYER", "subject_id": "p1", "role": "subject"}],
    })
    with pytest.raises(ValueError, match="NO_PLAYER_FACING_FAKE_MUTATION"):
        compile_fact_or_fake(c, eid, fake=True)


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
    with pytest.raises(ValueError, match="SENSITIVE_LORE_EXCLUDED_FROM_FACT_OR_FAKE"):
        compile_fact_or_fake(c, eid, fake=True)
    with pytest.raises(ValueError, match="SENSITIVE_LORE_EXCLUDED_FROM_FACT_OR_FAKE"):
        compile_fact_or_fake(c, eid, fake=False)


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



def test_progressive_identity_resolves_human_label():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1", "Human Player"))
    eid = upsert_event(c, {
        "event_type":"ON_FIELD_ODDITY",
        "league":"NFL",
        "event_date":"2022-01-01",
        "title":"Wild play",
        "neutral_summary":"A player scored after a broken play changed direction twice.",
        "source_url":"https://example.com/progressive",
        "source_publisher":"Example",
        "evidence_tier":"AUTHORITATIVE",
        "verification_status":"VERIFIED",
        "subjects":[{"subject_type":"NFL_PLAYER","subject_id":"p1","role":"player"}],
    })
    q = compile_progressive_identity(c, eid)
    assert q["answer"]["label"] == "Human Player"
    assert q["answer"]["label"] != "p1"


def test_common_link_rejects_second_shared_subject():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1", "Player One"))
    for season, typ in [(2019,"TRADE"),(2020,"CONTRACT"),(2021,"RECORD_EVENT")]:
        eid = upsert_event(c, {
            "event_type":typ,
            "league":"NFL",
            "event_date":f"{season}-01-01",
            "title":typ,
            "neutral_summary":"Football event.",
            "source_url":f"https://example.com/amb-{season}",
            "source_publisher":"Example",
            "evidence_tier":"AUTHORITATIVE",
            "verification_status":"VERIFIED",
            "subjects":[
                {"subject_type":"NFL_PLAYER","subject_id":"p1","role":"player"},
                {"subject_type":"NFL_TEAM","subject_id":"AAA","role":"team"},
            ],
        })
    with pytest.raises(ValueError, match="AMBIGUOUS_COMMON_LINK"):
        compile_common_link(c, "NFL_PLAYER", "p1")


def test_mixed_lore_stat_has_three_distinct_clues_and_human_answer():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1", "Human Player"))
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?,?)",
              ("p1",2020,1,20,"AAA","SOURCE_BACKED"))
    eid = upsert_event(c, {
        "event_type":"ON_FIELD_ODDITY",
        "league":"NFL",
        "event_date":"2022-01-01",
        "title":"Wild play",
        "neutral_summary":"A player scored on an unusual broken play.",
        "source_url":"https://example.com/mixed",
        "source_publisher":"Example",
        "evidence_tier":"AUTHORITATIVE",
        "verification_status":"VERIFIED",
        "subjects":[{"subject_type":"NFL_PLAYER","subject_id":"p1","role":"player"}],
    })
    q = compile_mixed_lore_stat(c, eid)
    assert q["question"] == "Who am I?"
    assert len(q["clues"]) == 3
    assert len({x.casefold() for x in q["clues"]}) == 3
    assert q["answer"]["label"] == "Human Player"
