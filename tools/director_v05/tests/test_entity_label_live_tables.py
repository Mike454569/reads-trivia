import sqlite3

from tools.director_v05.entity_labels import resolve_required_label


def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    c.execute("""CREATE TABLE team_aliases(
        team_code TEXT, full_name TEXT, season_end INTEGER
    )""")
    c.execute("""CREATE TABLE schools(
        school_id TEXT PRIMARY KEY, school_name TEXT
    )""")
    c.execute("""CREATE TABLE school_aliases(
        school_id TEXT, alias_name TEXT
    )""")
    c.execute("""CREATE TABLE canonical_cfb_players(
        cfb_player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    return c


def test_resolves_nfl_team_from_team_aliases():
    c=_conn()
    c.execute("INSERT INTO team_aliases VALUES(?,?,?)",("GB","Green Bay Packers",None))
    assert resolve_required_label(c,"NFL_TEAM","GB")=="Green Bay Packers"


def test_resolves_school_from_live_schools_table():
    c=_conn()
    c.execute("INSERT INTO schools VALUES(?,?)",("ALA","Alabama"))
    assert resolve_required_label(c,"SCHOOL","ALA")=="Alabama"


def test_resolves_cfb_player_from_live_canonical_table():
    c=_conn()
    c.execute("INSERT INTO canonical_cfb_players VALUES(?,?)",("ESPN_CFB:123","Player One"))
    assert resolve_required_label(c,"CFB_PLAYER","ESPN_CFB:123")=="Player One"
