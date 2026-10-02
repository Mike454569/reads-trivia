import sqlite3

from tools.director_v05.cfb_pbp_detectors import classify_cfb_game, classify_cfb_play
from tools.director_v05.cfb_pbp_story_mining import mine_cfb_pbp
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""
        CREATE TABLE cfb_plays(
            game_id TEXT NOT NULL,
            play_id TEXT NOT NULL,
            season INTEGER,
            offense_school_id INTEGER,
            defense_school_id INTEGER,
            down INTEGER,
            yards_gained INTEGER,
            play_type TEXT,
            play_text TEXT,
            scoring INTEGER,
            ppa REAL,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL,
            PRIMARY KEY(game_id, play_id)
        )
    """)
    return c


def test_cfb_play_detector_uses_real_cfb_fields():
    play = {
        "play_id":"p1",
        "down":4,
        "yards_gained":75,
        "play_type":"Interception Return",
        "play_text":"Interception returned for touchdown",
        "scoring":1,
    }
    kinds = {x[0].split(":")[0] for x in classify_cfb_play(play)}
    assert "CFB_EXPLOSIVE_SCORE" in kinds
    assert "CFB_FOURTH_DOWN" in kinds
    assert "CFB_TURNOVER_SCORE" in kinds


def test_cfb_game_detector_finds_turnover_and_explosive_chaos():
    plays = []
    for i in range(6):
        plays.append({
            "play_type":"Interception Return",
            "play_text":"Interception",
            "scoring":1 if i < 2 else 0,
            "yards_gained":45 if i < 4 else 0,
            "down":4 if i < 3 else 1,
        })
    kinds = {x[0] for x in classify_cfb_game(plays)}
    assert "CFB_TURNOVER_AVALANCHE" in kinds
    assert "CFB_DEFENSIVE_SCORE_FRENZY" in kinds
    assert "CFB_EXPLOSIVE_SCORE_CLUSTER" in kinds
    assert "CFB_FOURTH_DOWN_MADNESS" in kinds


def test_miner_ingests_verified_cfb_lore_and_dedupes():
    c = _conn()
    rows = [
        ("g1","p1",2024,1,2,4,72,"Interception Return","Interception returned for touchdown",1,8.0),
        ("g1","p2",2024,2,1,1,5,"Rush","Routine rush",0,0.1),
        ("g1","p3",2024,1,2,1,0,"Safety","Quarterback tackled for safety",1,2.0),
    ]
    for row in rows:
        c.execute(
            "INSERT INTO cfb_plays VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (*row, "SOURCE_BACKED", "CFBD_API_LIVE"),
        )

    first = mine_cfb_pbp(c)
    stored_after_first = c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0]
    second = mine_cfb_pbp(c)
    stored_after_second = c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0]

    assert first["events"] >= 3
    assert second["events"] == first["events"]
    assert stored_after_second == stored_after_first

    leagues = {r[0] for r in c.execute("SELECT DISTINCT league FROM universal_event")}
    assert leagues == {"CFB"}
    schools = {
        (r["subject_type"], r["subject_id"])
        for r in c.execute("SELECT subject_type,subject_id FROM universal_event_subject")
    }
    assert ("SCHOOL","1") in schools
    assert ("SCHOOL","2") in schools


def test_miner_ignores_unverified_or_wrong_source_rows():
    c = _conn()
    c.execute(
        "INSERT INTO cfb_plays VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("g1","p1",2024,1,2,1,80,"Kickoff Return","Kickoff returned for touchdown",1,9.0,
         "UNVERIFIED","OTHER_SOURCE"),
    )
    result = mine_cfb_pbp(c)
    assert result["events"] == 0
    assert c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0] == 0
