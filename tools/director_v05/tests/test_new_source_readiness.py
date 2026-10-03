import sqlite3

from tools.data_refresh.cfb_recruiting_refresh import _canonical_player_id, _resolve_school
from tools.director_v05.fact_source_status import source_status_for_family


def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    c.execute("CREATE TABLE schools(school_id TEXT PRIMARY KEY, school_name TEXT)")
    c.execute("CREATE TABLE school_aliases(school_id TEXT, alias_name TEXT)")
    c.execute("CREATE TABLE canonical_cfb_players(cfb_player_id TEXT PRIMARY KEY)")
    return c


def test_recruiting_school_resolution_never_guesses():
    c=_conn()
    c.execute("INSERT INTO schools VALUES(?,?)",("ALA","Alabama"))
    c.execute("INSERT INTO school_aliases VALUES(?,?)",("ALA","Bama"))
    assert _resolve_school(c,"Alabama")=="ALA"
    assert _resolve_school(c,"Bama")=="ALA"
    assert _resolve_school(c,"Imaginary State") is None


def test_recruiting_player_link_requires_existing_canonical_identity():
    c=_conn()
    c.execute("INSERT INTO canonical_cfb_players VALUES(?)",("ESPN_CFB:123",))
    assert _canonical_player_id(c,"123")=="ESPN_CFB:123"
    assert _canonical_player_id(c,"999") is None


def test_source_readiness_updates_for_new_fact_families():
    assert source_status_for_family("RECRUITING")["status"]=="AUTO_SOURCE_READY"
    assert source_status_for_family("RULE_ODDITY")["status"]=="AUTO_SOURCE_READY"
    assert source_status_for_family("PRESS_CONFERENCE")["status"]=="PARTIAL_SOURCE"
    assert source_status_for_family("OFF_FIELD_ODDITY")["status"]=="PARTIAL_SOURCE"
