import sqlite3

from tools.director_v05.lore_rotation import (
    event_family,
    question_lore_profile,
    rotation_score,
    select_rotated_questions,
)
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    return c


def _event(c, eid, event_type, league):
    c.execute(
        """INSERT INTO universal_event(
           event_id,event_type,league,event_date,title,neutral_summary,
           verification_status,sensitive,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))""",
        (eid,event_type,league,"2024-01-01",eid,eid,"VERIFIED",0),
    )


def _q(qid, eid, answer):
    return {
        "question_id":qid,
        "answer":{"id":answer,"label":answer,"type":"NFL_PLAYER"},
        "rarity_score":8.0,
        "difficulty_score":75.0,
        "provenance":{
            "chain":{
                "hops":[
                    {
                        "relation":"SUBJECT_OF_EVENT",
                        "object_type":"EVENT",
                        "object_id":eid,
                    }
                ]
            }
        },
    }


def test_event_type_maps_to_broad_family():
    assert event_family("ARREST") == "LEGAL_EVENT"
    assert event_family("COACH_FIRE") == "COACHING_MOVE"
    assert event_family("TRADE") == "TRADE"


def test_question_profile_reads_real_event_family_and_league():
    c = _conn()
    _event(c,"e1","TRADE","NFL")
    p = question_lore_profile(c,_q("q1","e1","p1"))
    assert p["families"] == ["TRADE"]
    assert p["leagues"] == ["NFL"]
    assert p["sensitive"] is False


def test_rotation_caps_sensitive_content():
    c = _conn()
    _event(c,"e1","ARREST","NFL")
    _event(c,"e2","CHARGE","NFL")
    _event(c,"e3","TRADE","NFL")
    candidates = [
        _q("q1","e1","p1"),
        _q("q2","e2","p2"),
        _q("q3","e3","p3"),
    ]
    out = select_rotated_questions(c,candidates,target=3,max_sensitive=1)
    assert out["sensitive_count"] == 1
    assert len(out["selected"]) == 2


def test_recent_family_gets_penalized():
    c = _conn()
    _event(c,"e1","TRADE","NFL")
    _event(c,"e2","TRANSFER","CFB")
    trade = _q("q1","e1","p1")
    transfer = _q("q2","e2","p2")
    base_trade = rotation_score(
        trade,question_lore_profile(c,trade),
        family_counts={},league_counts={},recent_families=(),family_targets={"TRADE":1}
    )
    recent_trade = rotation_score(
        trade,question_lore_profile(c,trade),
        family_counts={},league_counts={},recent_families=("TRADE",),family_targets={"TRADE":1}
    )
    assert recent_trade < base_trade


def test_rotation_spreads_families_and_leagues():
    c = _conn()
    specs = [
        ("e1","TRADE","NFL","p1"),
        ("e2","TRADE","NFL","p2"),
        ("e3","TRADE","NFL","p3"),
        ("e4","TRANSFER","CFB","p4"),
        ("e5","ON_FIELD_ODDITY","CFB","p5"),
        ("e6","RECORD_EVENT","NFL","p6"),
    ]
    candidates = []
    for i,(eid,typ,league,answer) in enumerate(specs):
        _event(c,eid,typ,league)
        candidates.append(_q("q"+str(i),eid,answer))

    out = select_rotated_questions(c,candidates,target=4,max_sensitive=0)
    assert len(out["selected"]) == 4
    assert len(out["family_counts"]) >= 3
    assert out["league_counts"].get("NFL",0) > 0
    assert out["league_counts"].get("CFB",0) > 0
    assert out["family_counts"].get("TRADE",0) <= out["max_per_family"]
