import sqlite3

from tools.director_v05.lore_answer_uniqueness import (
    clue_fit_report,
    filter_ambiguous_distractors,
)


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE universal_event_subject(
        event_id TEXT, subject_type TEXT, subject_id TEXT, role TEXT
    )""")
    c.execute("""CREATE TABLE draft_facts(
        player_key TEXT, draft_team TEXT, draft_season INTEGER,
        verification_status TEXT
    )""")
    c.execute("""CREATE TABLE canonical_roster_seasons(
        player_id TEXT, team_code TEXT, season INTEGER,
        verification_status TEXT
    )""")
    return c


def _question():
    return {
        "answer":{"id":"p1","label":"Correct","type":"NFL_PLAYER"},
        "clues":[
            {"relation":"SUBJECT_OF_EVENT","text":"I made the play."},
            {"relation":"DRAFTED_BY","text":"I was drafted by AAA in 2020."},
            {"relation":"ROSTERED_BY","text":"I suited up for BBB in 2021."},
        ],
        "provenance":{
            "chain":{
                "hops":[
                    {"relation":"SUBJECT_OF_EVENT","object_type":"EVENT","object_id":"e1","season":2022},
                    {"relation":"DRAFTED_BY","object_type":"NFL_TEAM","object_id":"AAA","season":2020},
                    {"relation":"ROSTERED_BY","object_type":"NFL_TEAM","object_id":"BBB","season":2021},
                ]
            }
        }
    }


def test_candidate_matching_every_clue_is_rejected():
    c = _conn()
    c.execute("INSERT INTO universal_event_subject VALUES(?,?,?,?)",("e1","NFL_PLAYER","p2","player"))
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?)",("p2","AAA",2020,"SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?)",("p2","BBB",2021,"SOURCE_BACKED"))

    report = clue_fit_report(c, _question(), "p2")
    assert report["all_checked_clues_match"] is True

    kept, rejected = filter_ambiguous_distractors(
        c, _question(), [{"entity_id":"p2","label":"Also Correct","score":99}], k=3
    )
    assert kept == []
    assert rejected[0]["reason"] == "DISTRACTOR_FITS_ALL_CLUES"


def test_candidate_matching_only_some_clues_remains_valid_distractor():
    c = _conn()
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?)",("p3","AAA",2020,"SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?)",("p3","CCC",2021,"SOURCE_BACKED"))

    report = clue_fit_report(c, _question(), "p3")
    assert report["matched_clues"] == 1
    assert report["all_checked_clues_match"] is False

    kept, rejected = filter_ambiguous_distractors(
        c, _question(), [{"entity_id":"p3","label":"Plausible Wrong","score":80}], k=3
    )
    assert len(kept) == 1
    assert rejected == []
