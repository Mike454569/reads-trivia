import sqlite3

from tools.director_v05.cfb_recruiting_lore import mine_cfb_recruiting_lore
from tools.director_v05.official_rule_lore import populate_official_rule_lore
from tools.director_v05.reviewed_media_lore import ingest_reviewed_stories
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""CREATE TABLE cfb_recruits(
        recruit_id TEXT PRIMARY KEY,
        athlete_id TEXT,
        cfb_player_id TEXT,
        class_year INTEGER,
        recruit_type TEXT,
        ranking INTEGER,
        recruit_name TEXT,
        high_school TEXT,
        committed_school_id TEXT,
        committed_school_name TEXT,
        position TEXT,
        height REAL,
        weight INTEGER,
        stars INTEGER,
        rating REAL,
        city TEXT,
        state_province TEXT,
        country TEXT,
        source_id TEXT,
        verification_status TEXT
    )""")
    return c


def test_recruiting_lore_uses_school_and_optional_player_subjects():
    c = _conn()
    c.execute(
        "INSERT INTO cfb_recruits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("r1","123","ESPN_CFB:123",2026,"HighSchool",12,"Player One",
         "Central HS","ALA","Alabama","QB",74.0,205,5,0.9876,
         "Tuscaloosa","AL","USA","CFBD_API_LIVE","SOURCE_BACKED"),
    )
    out = mine_cfb_recruiting_lore(c)
    assert out["events"] == 1
    subs = {
        (r["subject_type"], r["subject_id"], r["role"])
        for r in c.execute("SELECT subject_type,subject_id,role FROM universal_event_subject")
    }
    assert ("SCHOOL","ALA","commitment") in subs
    assert ("CFB_PLAYER","ESPN_CFB:123","recruit") in subs


def test_recruiting_lore_requires_resolved_school():
    c = _conn()
    c.execute(
        "INSERT INTO cfb_recruits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("r1","123",None,2026,"HighSchool",12,"Player One",
         "Central HS",None,"Unknown U","QB",74.0,205,5,0.9876,
         "Tuscaloosa","AL","USA","CFBD_API_LIVE","SOURCE_BACKED"),
    )
    out = mine_cfb_recruiting_lore(c)
    assert out["events"] == 0


def test_official_rule_population_is_idempotent_and_primary():
    c = _conn()
    first = populate_official_rule_lore(c)
    count1 = c.execute("SELECT COUNT(*) FROM universal_event WHERE event_type='RULE_ODDITY'").fetchone()[0]
    second = populate_official_rule_lore(c)
    count2 = c.execute("SELECT COUNT(*) FROM universal_event WHERE event_type='RULE_ODDITY'").fetchone()[0]
    assert first["events"] >= 5
    assert second["events"] == first["events"]
    assert count2 == count1
    tiers = {r[0] for r in c.execute(
        """SELECT DISTINCT evidence_tier FROM universal_event_evidence e
           JOIN universal_event u ON u.event_id=e.event_id
           WHERE u.event_type='RULE_ODDITY'"""
    )}
    assert tiers == {"PRIMARY"}


def test_reviewed_media_lane_rejects_social_only_and_accepts_reputable_media():
    c = _conn()
    bad = {
        "event_type":"PRESS_CONFERENCE",
        "league":"NFL",
        "event_date":"2026-01-01",
        "title":"Bad source",
        "neutral_summary":"Coach discussed the game.",
        "source_url":"https://x.com/example/status/1",
        "source_publisher":"X",
        "evidence_tier":"REPUTABLE_MEDIA",
        "subjects":[{"subject_type":"COACH","subject_id":"c1","role":"speaker"}],
    }
    good = {
        "event_type":"OFF_FIELD_ODDITY",
        "league":"NFL",
        "event_date":"2026-01-02",
        "title":"Reviewed story",
        "neutral_summary":"A documented off-field football story.",
        "source_url":"https://www.espn.com/example",
        "source_publisher":"ESPN",
        "evidence_tier":"REPUTABLE_MEDIA",
        "subjects":[{"subject_type":"NFL_PLAYER","subject_id":"p1","role":"subject"}],
    }
    out = ingest_reviewed_stories(c,[bad,good])
    assert out["inserted"] == 1
    assert len(out["rejected"]) == 1
