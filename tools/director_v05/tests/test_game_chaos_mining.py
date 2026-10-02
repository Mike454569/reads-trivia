import sqlite3

from tools.director_v05.game_chaos_mining import classify_game, mine_nfl_game_chaos


def test_classify_game_detects_multiple_chaos_patterns():
    plays = [
        {"yards_gained": 75, "touchdown": 1, "interception": 1, "fumble_lost": 0, "down": 2, "wpa": 0.31},
        {"yards_gained": 55, "touchdown": 1, "interception": 0, "fumble_lost": 1, "down": 3, "wpa": -0.29},
        {"yards_gained": 45, "touchdown": 1, "interception": 0, "fumble_lost": 0, "down": 1, "wpa": 0.27},
        {"yards_gained": 44, "touchdown": 1, "interception": 0, "fumble_lost": 0, "down": 4, "wpa": 0.02},
        {"yards_gained": 20, "touchdown": 0, "interception": 1, "fumble_lost": 0, "down": 4, "wpa": 0.01},
        {"yards_gained": 19, "touchdown": 0, "interception": 1, "fumble_lost": 0, "down": 4, "wpa": 0.01},
        {"yards_gained": 1, "touchdown": 0, "interception": 1, "fumble_lost": 1, "down": 2, "wpa": 0.01},
    ]
    rules = {row[0] for row in classify_game(plays)}
    assert "TURNOVER_AVALANCHE" in rules
    assert "DEFENSIVE_SCORE_FRENZY" in rules
    assert "EXPLOSIVE_TD_CLUSTER" in rules
    assert "FOURTH_DOWN_MADNESS" in rules
    assert "WIN_PROBABILITY_WHIPLASH" in rules


def test_miner_is_repeatable_without_duplicate_events():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE nfl_plays(
            game_id TEXT, play_id TEXT, season INTEGER, yards_gained INTEGER,
            touchdown INTEGER, posteam TEXT, defteam TEXT, down INTEGER,
            interception INTEGER, fumble_lost INTEGER,
            own_kickoff_recovery INTEGER, wpa REAL
        )"""
    )
    rows = [
        ("g1", "1", 2025, 5, 0, "AAA", "BBB", 1, 1, 0, 0, 0.01),
        ("g1", "2", 2025, 5, 0, "BBB", "AAA", 1, 1, 0, 0, 0.01),
        ("g1", "3", 2025, 5, 0, "AAA", "BBB", 1, 1, 0, 0, 0.01),
        ("g1", "4", 2025, 5, 0, "BBB", "AAA", 1, 1, 0, 0, 0.01),
        ("g1", "5", 2025, 5, 0, "AAA", "BBB", 1, 1, 0, 0, 0.01),
        ("g1", "6", 2025, 5, 0, "BBB", "AAA", 1, 1, 0, 0, 0.01),
    ]
    conn.executemany("INSERT INTO nfl_plays VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", rows)

    first = mine_nfl_game_chaos(conn)
    second = mine_nfl_game_chaos(conn)

    assert first["events"] == 1
    assert second["events"] == 1
    stored = conn.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0]
    assert stored == 1
