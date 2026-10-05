import sqlite3
import types

from tools.director_v05 import cfb_story_candidate_harvest as cfb


def _conn():
    c=sqlite3.connect(":memory:")
    c.row_factory=sqlite3.Row
    c.execute("""
      CREATE TABLE schools(
        school_id TEXT PRIMARY KEY,
        school_name TEXT
      )
    """)
    c.executemany(
        "INSERT INTO schools(school_id,school_name) VALUES(?,?)",
        [("1","Alabama"),("2","Auburn"),("3","Georgia")],
    )
    c.commit()
    return c


def test_school_names_are_canonical_and_deduped():
    c=_conn()
    names=cfb._school_names(c,limit=10)
    assert names==["Alabama","Auburn","Georgia"]


def test_sensitive_cfb_family_is_never_reclassified_safe():
    assert "DISCIPLINE_LEGAL" in cfb.SENSITIVE_FAMILIES
    assert "PRESS_CONFERENCE" not in cfb.SENSITIVE_FAMILIES
    assert "OFF_FIELD_ODDITY" not in cfb.SENSITIVE_FAMILIES


def test_cfb_queries_cover_core_story_families():
    assert "PRESS_CONFERENCE" in cfb.CFB_QUERY_FAMILIES
    assert "OFF_FIELD_ODDITY" in cfb.CFB_QUERY_FAMILIES
    assert "CELEBRATION_FAN" in cfb.CFB_QUERY_FAMILIES
    assert "RULE_ODDITY" in cfb.CFB_QUERY_FAMILIES
    assert "DISCIPLINE_LEGAL" in cfb.CFB_QUERY_FAMILIES
    assert all(cfb.CFB_QUERY_FAMILIES[k] for k in cfb.CFB_QUERY_FAMILIES)


def test_cfb_source_domains_are_allowlisted():
    assert "ncaa.org" in cfb.CFB_DOMAINS
    assert "espn.com" in cfb.CFB_DOMAINS
    assert "cbssports.com" in cfb.CFB_DOMAINS
    assert len(set(cfb.CFB_DOMAINS))==len(cfb.CFB_DOMAINS)
