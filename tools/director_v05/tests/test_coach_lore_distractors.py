import sqlite3
import pytest

from tools.director_v05.lore_distractors import (
    attach_deep_lore_options,
    coach_lore_distractors,
)


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE coach_team_seasons(
        coach_id TEXT, coach_name TEXT, team_code TEXT, season INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    return c


def _seed(c):
    rows = [
        ("c1","Correct Coach","AAA",2022),
        ("c1","Correct Coach","AAA",2023),
        ("c2","Same Team Coach","AAA",2020),
        ("c3","Same Era Coach","BBB",2023),
        ("c4","Another Era Coach","CCC",2021),
        ("c5","Far Coach","ZZZ",2010),
    ]
    for row in rows:
        c.execute("INSERT INTO coach_team_seasons VALUES(?,?,?,?,?,?)",
                  (*row,"coach-src","SOURCE_BACKED"))


def test_coach_distractors_use_team_and_era():
    c = _conn()
    _seed(c)
    result = coach_lore_distractors(c, "c1", k=3, difficulty_band="SICKO")
    ids = [d["entity_id"] for d in result["selected"]]
    assert len(ids) == 3
    assert "c1" not in ids
    assert "c2" in ids or "c3" in ids


def test_coach_question_gets_four_human_options():
    c = _conn()
    _seed(c)
    q = {
        "question_id":"coach-q",
        "question":"Who am I?",
        "difficulty_band":"HARD",
        "answer":{"id":"c1","label":"Correct Coach","type":"COACH"},
        "clues":[{"text":"I coached AAA in 2023."}],
    }
    out = attach_deep_lore_options(c, q)
    assert len(out["options"]) == 4
    assert out["options"].count("Correct Coach") == 1
    assert len({x.casefold() for x in out["options"]}) == 4


def test_coach_thin_pool_fails_closed():
    c = _conn()
    c.execute("INSERT INTO coach_team_seasons VALUES(?,?,?,?,?,?)",
              ("c1","Only Coach","AAA",2023,"coach-src","SOURCE_BACKED"))
    with pytest.raises(ValueError, match="INSUFFICIENT_DEEP_LORE_DISTRACTORS"):
        coach_lore_distractors(c, "c1", k=3)
