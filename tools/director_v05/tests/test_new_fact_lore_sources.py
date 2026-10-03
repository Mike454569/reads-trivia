import sqlite3

from tools.director_v05.cfb_weather_lore import mine_cfb_weather_lore
from tools.director_v05.nfl_contract_lore import mine_nfl_contract_lore
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("""CREATE TABLE cfb_games_canonical(
        game_id TEXT PRIMARY KEY, season INTEGER, home_school_id TEXT, away_school_id TEXT,
        game_indoors INTEGER, temperature REAL, wind_speed REAL, snowfall REAL,
        precipitation REAL, weather_condition TEXT, weather_source_id TEXT,
        weather_verification_status TEXT
    )""")
    c.execute("""CREATE TABLE nfl_player_contracts(
        contract_id INTEGER PRIMARY KEY, player_key TEXT, team_code TEXT, position TEXT,
        year_signed INTEGER, contract_years INTEGER, value REAL, apy REAL, guaranteed REAL,
        source_id TEXT, verification_status TEXT
    )""")
    return c


def test_weather_miner_creates_verified_extreme_weather_lore():
    c = _conn()
    c.execute("INSERT INTO cfb_games_canonical VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
              ("g1",2024,"ALA","UGA",0,28,30,1.5,0.4,"Snow and wind",
               "CFBD_API_LIVE","SOURCE_BACKED"))
    first = mine_cfb_weather_lore(c)
    count1 = c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0]
    second = mine_cfb_weather_lore(c)
    count2 = c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0]
    assert first["events"] >= 3
    assert second["events"] == first["events"]
    assert count2 == count1
    assert c.execute(
        "SELECT COUNT(*) FROM universal_event WHERE event_type='WEATHER_CHAOS' AND verification_status='VERIFIED'"
    ).fetchone()[0] >= 1


def test_weather_miner_requires_weather_provenance():
    c = _conn()
    c.execute("INSERT INTO cfb_games_canonical VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
              ("g1",2024,"ALA","UGA",0,20,40,3,1,"Blizzard",None,None))
    out = mine_cfb_weather_lore(c)
    assert out["events"] == 0


def test_contract_miner_creates_human_labeled_verified_contract_event():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)",("p1","Player One"))
    c.execute("INSERT INTO nfl_player_contracts VALUES(?,?,?,?,?,?,?,?,?,?,?)",
              (1,"p1","GB","WR",2024,4,80000000,20000000,45000000,
               "NFLVERSE_DATA","SOURCE_BACKED"))
    out = mine_nfl_contract_lore(c)
    assert out["events"] == 1
    row = c.execute("SELECT event_type,neutral_summary FROM universal_event").fetchone()
    assert row["event_type"] == "CONTRACT"
    assert "Player One" in row["neutral_summary"]
    assert "$80,000,000" in row["neutral_summary"]


def test_contract_miner_skips_unresolved_player_label():
    c = _conn()
    c.execute("INSERT INTO nfl_player_contracts VALUES(?,?,?,?,?,?,?,?,?,?,?)",
              (1,"missing","GB","WR",2024,4,80000000,20000000,45000000,
               "NFLVERSE_DATA","SOURCE_BACKED"))
    out = mine_nfl_contract_lore(c)
    assert out["events"] == 0
    assert out["skipped_unresolved_labels"] == 1
