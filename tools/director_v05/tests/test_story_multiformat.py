import sqlite3

from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.story_multiformat import (
    generate_story_formats_for_event,
    generate_story_matching_round,
)
from tools.director_v05.story_to_trivia_factory import _ensure_schema
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    _ensure_schema(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    return c


def _event(c, eid, pid, title, date=None):
    return upsert_event(c, {
        "event_id":eid,
        "event_type":"OFF_FIELD_ODDITY",
        "league":"NFL",
        "event_date":date,
        "title":title,
        "neutral_summary":title + " was documented by a primary football source.",
        "source_url":"https://www.nfl.com/" + eid,
        "source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY",
        "verification_status":"VERIFIED",
        "subjects":[{"subject_type":"NFL_PLAYER","subject_id":pid,"role":"subject"}],
        "tags":["story_factory","off_field"],
        "sensitive":False,
    })


def test_undated_story_never_unlocks_chronology():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1","Player One"))
    _event(c,"e-story","p1","Player One strange offseason story",None)

    out = generate_story_formats_for_event(
        c,
        candidate_id="cand1",
        event_id="e-story",
        subject_type="NFL_PLAYER",
        subject_id="p1",
    )

    reasons = {(r["format"],r["reason"]) for r in out["rejected"]}
    assert ("BEFORE_AFTER","STORY_EVENT_DATE_NOT_REVIEWED") in reasons
    assert ("TIMELINE","STORY_EVENT_DATE_NOT_REVIEWED") in reasons
    stored = {
        r["mechanic"]
        for r in c.execute("SELECT mechanic FROM story_generated_questions")
    }
    assert "SORTING_TIMELINE" not in stored


def test_reviewed_date_unlocks_before_after_and_timeline():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1","Player One"))
    _event(c,"e1","p1","First unusual story","2018-01-01")
    _event(c,"e2","p1","Second unusual story","2020-01-01")
    _event(c,"e3","p1","Third unusual story","2022-01-01")
    _event(c,"e4","p1","Fourth unusual story","2024-01-01")

    out = generate_story_formats_for_event(
        c,
        candidate_id="cand1",
        event_id="e4",
        subject_type="NFL_PLAYER",
        subject_id="p1",
    )
    families = {q["question_family"] for q in out["generated"]}
    assert "LORE_BEFORE_AFTER" in families
    assert "LORE_TIMELINE" in families


def test_matching_round_requires_distinct_promoted_story_subjects():
    c = _conn()
    for i in range(1,4):
        pid = "p" + str(i)
        c.execute("INSERT INTO canonical_players VALUES(?,?)", (pid,"Player "+str(i)))
        eid = "e" + str(i)
        _event(c,eid,pid,"Story for Player "+str(i),"202" + str(i) + "-01-01")
        c.execute(
            """INSERT INTO football_story_enrichment(
               candidate_id,decision,promoted_event_id,subject_type,subject_id,
               generated_question_count,processed_at,evidence_terms_json)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                "c"+str(i),"AUTO_PROMOTED",eid,"NFL_PLAYER",pid,1,
                "2026-10-03T00:00:0"+str(i)+"Z","[]",
            ),
        )
    c.commit()

    out = generate_story_matching_round(c,limit=3)
    assert out["generated"] is not None
    assert out["generated"]["mechanic"] == "MATCHING"
    assert len(out["generated"]["prompts"]) == 3
    assert len(out["generated"]["answers"]) == 3
