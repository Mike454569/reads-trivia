import csv
import sqlite3

from tools.data_refresh import cfb_player_season_stats_refresh as refresh
from tools.director_v05.cfb_pbp_story_mining import mine_cfb_pbp
from tools.director_v05.universal_schema import install


def test_extract_play_subjects_uses_existing_canonical_identity(tmp_path):
    path = tmp_path / "stats.csv"
    fields = [
        "game_id","play_id","touchdown_player_id","touchdown_player",
        "rush_player_id","rush_player",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow({
            "game_id":"g1","play_id":"p1",
            "touchdown_player_id":"123","touchdown_player":"Player One",
            "rush_player_id":"123","rush_player":"Player One",
        })
        w.writerow({
            "game_id":"g1","play_id":"p2",
            "touchdown_player_id":"999","touchdown_player":"Unknown",
            "rush_player_id":"","rush_player":"",
        })

    rows = refresh._extract_play_subjects(
        path, 2024, {"ESPN_CFB:123"}
    )
    assert {r[2] for r in rows} == {"ESPN_CFB:123"}
    assert {r[4] for r in rows} == {"TOUCHDOWN","RUSHER"}
    assert all(r[6] == "SPORTSDATAVERSE_CFB" for r in rows)


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""CREATE TABLE cfb_plays(
        game_id TEXT, play_id TEXT, season INTEGER,
        offense_school_id INTEGER, defense_school_id INTEGER,
        down INTEGER, yards_gained INTEGER, play_type TEXT, play_text TEXT,
        scoring INTEGER, ppa REAL, verification_status TEXT, source_id TEXT,
        PRIMARY KEY(game_id,play_id)
    )""")
    c.execute("""CREATE TABLE cfb_play_player_subjects(
        game_id TEXT, play_id TEXT, cfb_player_id TEXT, player_name TEXT,
        role TEXT, season INTEGER, source_id TEXT, verification_status TEXT,
        PRIMARY KEY(game_id,play_id,cfb_player_id,role)
    )""")
    return c


def test_cfb_pbp_lore_attaches_verified_player_subject():
    c = _conn()
    c.execute(
        "INSERT INTO cfb_plays VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("g1","p1",2024,1,2,1,75,"Rush TD","75-yard rushing touchdown",
         1,5.0,"SOURCE_BACKED","CFBD_API_LIVE"),
    )
    c.execute(
        "INSERT INTO cfb_play_player_subjects VALUES(?,?,?,?,?,?,?,?)",
        ("g1","p1","ESPN_CFB:123","Player One","TOUCHDOWN",2024,
         "SPORTSDATAVERSE_CFB","SOURCE_BACKED"),
    )

    out = mine_cfb_pbp(c)
    assert out["events"] >= 1
    rows = c.execute(
        """SELECT subject_type,subject_id,role
           FROM universal_event_subject
           WHERE subject_type='CFB_PLAYER'"""
    ).fetchall()
    assert any(
        r["subject_id"] == "ESPN_CFB:123" and r["role"] == "touchdown"
        for r in rows
    )


def test_cfb_pbp_lore_ignores_unverified_player_bridge():
    c = _conn()
    c.execute(
        "INSERT INTO cfb_plays VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("g1","p1",2024,1,2,1,75,"Rush TD","75-yard rushing touchdown",
         1,5.0,"SOURCE_BACKED","CFBD_API_LIVE"),
    )
    c.execute(
        "INSERT INTO cfb_play_player_subjects VALUES(?,?,?,?,?,?,?,?)",
        ("g1","p1","ESPN_CFB:123","Player One","TOUCHDOWN",2024,
         "OTHER","UNVERIFIED"),
    )

    mine_cfb_pbp(c)
    count = c.execute(
        "SELECT COUNT(*) FROM universal_event_subject WHERE subject_type='CFB_PLAYER'"
    ).fetchone()[0]
    assert count == 0
