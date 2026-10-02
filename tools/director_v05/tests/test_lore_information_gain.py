import sqlite3

from tools.director_v05.lore_information_gain import calibrate_reveal_order


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
        "difficulty_band":"HARD",
        "answer":{"id":"p1","label":"Correct","type":"NFL_PLAYER"},
        "clues":[
            {"relation":"SUBJECT_OF_EVENT","text":"I made the bizarre play."},
            {"relation":"DRAFTED_BY","text":"I was drafted by AAA in 2020."},
            {"relation":"ROSTERED_BY","text":"I suited up for BBB in 2021."},
        ],
        "distractors":[
            {"entity_id":"p2","label":"Two"},
            {"entity_id":"p3","label":"Three"},
            {"entity_id":"p4","label":"Four"},
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


def _seed(c):
    # Only p2 shares the event, all three share draft team, two share roster team.
    c.execute("INSERT INTO universal_event_subject VALUES(?,?,?,?)",("e1","NFL_PLAYER","p2","player"))
    for pid in ("p2","p3","p4"):
        c.execute("INSERT INTO draft_facts VALUES(?,?,?,?)",(pid,"AAA",2020,"SOURCE_BACKED"))
    for pid in ("p2","p3"):
        c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?)",(pid,"BBB",2021,"SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?)",("p4","CCC",2021,"SOURCE_BACKED"))


def test_casual_surfaces_most_discriminating_clue_first():
    c = _conn()
    _seed(c)
    q = _question()
    out = calibrate_reveal_order(c, q, difficulty_band="CASUAL")
    assert out["clues"][0]["relation"] == "SUBJECT_OF_EVENT"
    assert out["clues"][0]["information_gain"] > out["clues"][-1]["information_gain"]
    assert [x["reveal_step"] for x in out["clues"]] == [1,2,3]


def test_sicko_preserves_ambiguity_first():
    c = _conn()
    _seed(c)
    q = _question()
    out = calibrate_reveal_order(c, q, difficulty_band="SICKO")
    assert out["clues"][0]["relation"] == "DRAFTED_BY"
    assert out["clues"][0]["survival_rate"] == 1.0
    assert out["clues"][-1]["relation"] == "SUBJECT_OF_EVENT"
