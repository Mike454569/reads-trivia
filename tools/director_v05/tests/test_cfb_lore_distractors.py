import sqlite3
import pytest

from tools.director_v05.lore_distractors import (
    attach_deep_lore_options,
    cfb_lore_distractors,
)


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE cfb_players_canonical(
        cfb_player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("""CREATE TABLE cfb_transfer_summary(
        cfb_player_id TEXT, first_school_id TEXT, last_school_id TEXT,
        first_season INTEGER, last_season INTEGER, transfer_count INTEGER
    )""")
    c.execute("""CREATE TABLE cfb_player_game_stats_real(
        cfb_player_id TEXT, player_name TEXT, school_id TEXT, season INTEGER,
        passing_yards INTEGER, rushing_yards INTEGER, receiving_yards INTEGER,
        verification_status TEXT
    )""")
    return c


def _seed(c):
    rows = [
        ("p1","Correct College Guy","ALA","TEX",2022,2024,1,420),
        ("p2","Same School Guy","UGA","TEX",2021,2024,1,390),
        ("p3","Same Era Guy","LSU","LSU",2022,2024,0,410),
        ("p4","Transfer Twin","ALA","TEX",2021,2023,1,360),
        ("p5","Far Away Guy","OSU","OSU",2015,2016,0,120),
    ]
    for pid,name,first,last,first_s,last_s,tc,peak in rows:
        c.execute("INSERT INTO cfb_players_canonical VALUES(?,?)",(pid,name))
        c.execute("INSERT INTO cfb_transfer_summary VALUES(?,?,?,?,?,?)",
                  (pid,first,last,first_s,last_s,tc))
        c.execute("INSERT INTO cfb_player_game_stats_real VALUES(?,?,?,?,?,?,?,?)",
                  (pid,name,last,last_s,peak,0,0,"SOURCE_BACKED_DERIVED"))


def test_cfb_lore_distractors_use_school_and_era_context():
    c = _conn()
    _seed(c)
    result = cfb_lore_distractors(c, "p1", k=3, difficulty_band="SICKO")
    ids = [d["entity_id"] for d in result["selected"]]
    assert len(ids) == 3
    assert "p1" not in ids
    assert "p2" in ids or "p4" in ids
    assert len(set(ids)) == 3


def test_cfb_options_are_four_unique_human_labels():
    c = _conn()
    _seed(c)
    q = {
        "question_id":"cfb-q1",
        "question":"Who am I?",
        "difficulty_band":"HARD",
        "answer":{"id":"p1","label":"Correct College Guy","type":"CFB_PLAYER"},
        "clues":[{"text":"I later transferred to Texas."}],
    }
    out = attach_deep_lore_options(c, q)
    assert len(out["options"]) == 4
    assert len({x.casefold() for x in out["options"]}) == 4
    assert out["options"].count("Correct College Guy") == 1


def test_cfb_recent_distractor_is_penalized():
    c = _conn()
    _seed(c)
    fresh = cfb_lore_distractors(c, "p1", k=3, difficulty_band="SICKO")
    recent = cfb_lore_distractors(
        c, "p1", k=3, difficulty_band="SICKO", recent_distractor_ids={"p2"}
    )
    a = {d["entity_id"]: d["score"] for d in fresh["selected"]}
    b = {d["entity_id"]: d["score"] for d in recent["selected"]}
    if "p2" in a and "p2" in b:
        assert b["p2"] < a["p2"]


def test_cfb_thin_pool_fails_closed():
    c = _conn()
    c.execute("INSERT INTO cfb_players_canonical VALUES(?,?)",("p1","Only College Guy"))
    c.execute("INSERT INTO cfb_transfer_summary VALUES(?,?,?,?,?,?)",
              ("p1","ALA","ALA",2023,2024,0))
    c.execute("INSERT INTO cfb_player_game_stats_real VALUES(?,?,?,?,?,?,?,?)",
              ("p1","Only College Guy","ALA",2024,100,0,0,"SOURCE_BACKED_DERIVED"))
    with pytest.raises(ValueError, match="INSUFFICIENT_DEEP_LORE_DISTRACTORS"):
        cfb_lore_distractors(c, "p1", k=3)
