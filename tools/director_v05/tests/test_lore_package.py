import sqlite3

from gateway.services import packages
from tools.director_v02.package_contract import validate_package_contract
from tools.director_v05 import lore_package


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE universal_event_subject(
        event_id TEXT, subject_type TEXT, subject_id TEXT, role TEXT
    )""")
    c.execute("INSERT INTO universal_event_subject VALUES(?,?,?,?)",("e1","NFL_PLAYER","p1","player"))
    return c


def _bank():
    return {
        "candidate_count": 5,
        "selected_count": 1,
        "unique_answers": 1,
        "unique_events": 1,
        "selected": [{
            "question_id":"qdeep-1",
            "question":"Who am I?",
            "difficulty_band":"HARD",
            "answer":{"id":"p1","label":"Player One","type":"NFL_PLAYER"},
            "options":["Player Two","Player One","Player Three","Player Four"],
            "clues":[
                {"text":"I was drafted by Green Bay in 2020.","reveal_step":1},
                {"text":"I made the Pro Bowl in 2022.","reveal_step":2},
                {"text":"In 2023, I scored on a bizarre broken play.","reveal_step":3},
            ],
            "chain_id":"chain1",
            "question_family":"DEEP_LORE_CHAIN",
            "rarity_score":8.0,
            "difficulty_score":78.0,
            "provenance":{"provenance_complete":True,"chain":{"hops":[]}},
            "distractors":[
                {"entity_id":"p2","label":"Player Two"},
                {"entity_id":"p3","label":"Player Three"},
                {"entity_id":"p4","label":"Player Four"},
            ],
        }],
    }


def test_deep_lore_package_uses_standard_guess_contract(monkeypatch):
    c = _conn()
    monkeypatch.setattr(lore_package.engine_bootstrap, "connect", lambda: c)
    monkeypatch.setattr(lore_package, "build_lore_question_bank", lambda *a, **k: _bank())

    package = lore_package.build_package(seed="abc", target_count=1, difficulty="medium")
    assert package["package_id"].startswith("GGP39:")
    assert package["qa_status"] == "PASSED"
    assert package["parsed_spec"]["relationship_predicate"] == "IDENTIFY_FROM_DEEP_LORE"

    q = package["questions"][0]
    assert q["question"] == "Who am I?"
    assert q["answer"] == "Player One"
    assert q["options"][q["correctIndex"]] == "Player One"
    assert q["difficulty"] == "medium"
    assert q["visual_template"] == "DEEP_LORE_THREE_CLUES"

    assert validate_package_contract(package) == []


def test_deep_lore_package_fails_closed_on_empty_bank(monkeypatch):
    c = _conn()
    monkeypatch.setattr(lore_package.engine_bootstrap, "connect", lambda: c)
    empty = {
        "candidate_count":0,"selected_count":0,"unique_answers":0,
        "unique_events":0,"selected":[]
    }
    monkeypatch.setattr(lore_package, "build_lore_question_bank", lambda *a, **k: empty)

    package = lore_package.build_package(seed="abc", target_count=1, difficulty="hard")
    assert package["qa_status"] == "FAILED"
    assert package["question_count"] == 0
    violations = validate_package_contract(package)
    assert any("empty" in v or "nothing to play" in v for v in violations)


def test_ggp39_package_id_is_storage_safe(tmp_path, monkeypatch):
    c = _conn()
    monkeypatch.setattr(lore_package.engine_bootstrap, "connect", lambda: c)
    monkeypatch.setattr(lore_package, "build_lore_question_bank", lambda *a, **k: _bank())
    monkeypatch.setattr(packages.config, "PACKAGES_DIR", tmp_path)

    package = lore_package.build_package(seed="store-me", target_count=1, difficulty="easy")
    stored = packages.save_package(package)
    assert stored["package_id"].startswith("GGP39:")
    assert packages.load_package(stored["package_id"])["package_id"] == stored["package_id"]



def test_deep_lore_delivery_blends_ready_story_question(monkeypatch):
    c = _conn()
    monkeypatch.setattr(lore_package.engine_bootstrap, "connect", lambda: c)

    story = {
        "question_id":"qstory-1",
        "question":"Who am I?",
        "difficulty_band":"HARD",
        "answer":{"id":"p-story","label":"Story Player","type":"NFL_PLAYER"},
        "options":["Story Player","Wrong A","Wrong B","Wrong C"],
        "clues":[
            {"text":"I spoke to reporters after a strange game.","reveal_step":1},
            {"text":"The story came from an NFL media appearance.","reveal_step":2},
            {"text":"The event became a memorable football moment.","reveal_step":3},
        ],
        "question_family":"LORE_IDENTITY",
        "provenance":{"provenance_complete":True,"chain":{"hops":[]}},
    }
    normal = _bank()
    normal["selected"][0]["answer"]["id"] = "p-normal"
    monkeypatch.setattr(
        lore_package,
        "load_ready_story_questions",
        lambda *a, **k: [story],
    )
    monkeypatch.setattr(
        lore_package,
        "build_lore_question_bank",
        lambda *a, **k: normal,
    )

    package = lore_package.build_package(
        seed="story-blend",
        target_count=2,
        difficulty="medium",
    )
    ids = [q["id"] for q in package["questions"]]
    assert "qstory-1" in ids
    assert "qdeep-1" in ids
    assert package["_diagnostics"]["story_questions_used"] == 1
