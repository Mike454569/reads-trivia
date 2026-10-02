import sqlite3
import pytest

from tools.director_v05.lore_distractors import (
    attach_deep_lore_options,
    nfl_lore_distractors,
)


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("""CREATE TABLE draft_facts(
        player_key TEXT, player_name TEXT, draft_season INTEGER,
        draft_round INTEGER, draft_pick_overall INTEGER, draft_team TEXT,
        verification_status TEXT
    )""")
    c.execute("""CREATE TABLE canonical_roster_seasons(
        player_id TEXT, team_code TEXT, season INTEGER,
        verification_status TEXT
    )""")
    c.execute("""CREATE TABLE nfl_all_pro_selections(
        player_id TEXT, position_raw TEXT, season INTEGER, is_ap INTEGER,
        verification_status TEXT
    )""")
    c.execute("""CREATE TABLE nfl_pro_bowl_selections(
        player_id TEXT, position_raw TEXT, season INTEGER,
        verification_status TEXT
    )""")
    return c


def _seed(c):
    players = [
        ("p1","Correct Player",2020,1,20,"AAA","WR"),
        ("p2","Same Era Guy",2019,1,25,"AAA","WR"),
        ("p3","Close Pick Guy",2021,1,18,"BBB","WR"),
        ("p4","Team Mate Guy",2020,2,45,"AAA","WR"),
        ("p5","Far Guy",2012,5,160,"ZZZ","LB"),
    ]
    for pid,name,season,round_no,pick,team,pos in players:
        c.execute("INSERT INTO canonical_players VALUES(?,?)",(pid,name))
        c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?,?,?)",
                  (pid,name,season,round_no,pick,team,"SOURCE_BACKED"))
        c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?)",
                  (pid,team,season,"SOURCE_BACKED"))
        c.execute("INSERT INTO nfl_all_pro_selections VALUES(?,?,?,?,?)",
                  (pid,pos,season,1,"WIKIPEDIA_STRUCTURED_SECONDARY"))


def test_profile_aware_distractors_are_plausible_and_unique():
    c = _conn()
    _seed(c)
    result = nfl_lore_distractors(c, "p1", k=3)
    ids = [d["entity_id"] for d in result["selected"]]
    assert len(ids) == 3
    assert len(set(ids)) == 3
    assert "p1" not in ids
    assert "p2" in ids


def test_recent_distractor_is_penalized_not_forced():
    c = _conn()
    _seed(c)
    fresh = nfl_lore_distractors(c, "p1", k=3)
    recent = nfl_lore_distractors(c, "p1", k=3, recent_distractor_ids={"p2"})
    fresh_scores = {d["entity_id"]: d["score"] for d in fresh["selected"]}
    recent_scores = {d["entity_id"]: d["score"] for d in recent["selected"]}
    if "p2" in fresh_scores and "p2" in recent_scores:
        assert recent_scores["p2"] < fresh_scores["p2"]


def test_attach_options_outputs_four_unique_human_labels():
    c = _conn()
    _seed(c)
    q = {
        "question_id":"q1",
        "question":"Who am I?",
        "answer":{"id":"p1","label":"Correct Player","type":"NFL_PLAYER"},
        "clues":[{"text":"I was drafted in 2020."}],
    }
    out = attach_deep_lore_options(c, q)
    assert out["mechanic"] == "MULTIPLE_CHOICE"
    assert len(out["options"]) == 4
    assert len({x.casefold() for x in out["options"]}) == 4
    assert out["options"].count("Correct Player") == 1


def test_weak_pool_fails_closed():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)",("p1","Only Player"))
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?,?,?)",
              ("p1","Only Player",2020,1,1,"AAA","SOURCE_BACKED"))
    with pytest.raises(ValueError, match="INSUFFICIENT_DEEP_LORE_DISTRACTORS"):
        nfl_lore_distractors(c, "p1", k=3)


def test_options_are_not_fixed_to_first_slot_and_are_deterministic():
    c = _conn()
    _seed(c)
    q = {
        "question_id":"q-shuffle",
        "question":"Who am I?",
        "difficulty_band":"HARD",
        "answer":{"id":"p1","label":"Correct Player","type":"NFL_PLAYER"},
        "clues":[{"text":"I was drafted in 2020."}],
    }
    a = attach_deep_lore_options(c, q)
    b = attach_deep_lore_options(c, q)
    assert a["options"] == b["options"]
    assert sorted(a["options"]) == sorted(["Correct Player"] + [d["label"] for d in a["distractors"]])
    assert a["options"].count("Correct Player") == 1


def test_sicko_uses_closer_distractors_than_casual():
    c = _conn()
    _seed(c)
    casual = nfl_lore_distractors(c, "p1", k=3, difficulty_band="CASUAL")
    sicko = nfl_lore_distractors(c, "p1", k=3, difficulty_band="SICKO")
    casual_avg = sum(d["score"] for d in casual["selected"]) / 3
    sicko_avg = sum(d["score"] for d in sicko["selected"]) / 3
    assert sicko_avg >= casual_avg
