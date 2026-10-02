import sqlite3
import pytest

from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.lore_chains import (
    compile_lore_chain_question,
    discover_lore_chains,
)
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""CREATE TABLE draft_facts(
        player_key TEXT, draft_team TEXT, draft_season INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    c.execute("""CREATE TABLE canonical_roster_seasons(
        player_id TEXT, team_code TEXT, season INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    c.execute("""CREATE TABLE nfl_all_pro_selections(
        player_id TEXT, honor_level TEXT, season INTEGER, is_ap INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    return c


def _event(c, eid_suffix, player_id="p1", team_id="AAA"):
    return upsert_event(c, {
        "event_type": "ON_FIELD_ODDITY",
        "league": "NFL",
        "event_date": "2022-01-01",
        "title": "Verified oddity " + eid_suffix,
        "neutral_summary": "Verified unusual football event.",
        "source_url": "https://example.com/" + eid_suffix,
        "source_publisher": "Example",
        "evidence_tier": "AUTHORITATIVE",
        "verification_status": "VERIFIED",
        "subjects": [
            {"subject_type":"NFL_PLAYER","subject_id":player_id,"role":"player"},
            {"subject_type":"NFL_TEAM","subject_id":team_id,"role":"team"},
        ],
    })


def test_discovers_mixed_source_deep_chain():
    c = _conn()
    _event(c, "oddity")
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p1","AAA",2020,"draft-src","SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?,?)",
              ("p1","BBB",2021,"roster-src","SOURCE_BACKED"))
    c.execute("INSERT INTO nfl_all_pro_selections VALUES(?,?,?,?,?,?)",
              ("p1","FIRST_TEAM",2023,1,"ap-src","WIKIPEDIA_STRUCTURED_SECONDARY"))

    chains = discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=5)
    assert chains
    assert all(ch.gameplay_eligible for ch in chains)
    assert any(ch.source_diversity >= 2 and ch.depth >= 3 for ch in chains)


def test_chains_do_not_loop_back_to_anchor():
    c = _conn()
    _event(c, "loop")
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p1","AAA",2020,"draft-src","SOURCE_BACKED"))

    chains = discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=6)
    for chain in chains:
        visited = {(chain.anchor_type, chain.anchor_id)}
        for hop in chain.hops:
            node = (hop.object_type, hop.object_id)
            assert node not in visited
            visited.add(node)


def test_single_source_paths_do_not_qualify():
    c = _conn()
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p1","AAA",2020,"draft-src","SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?,?)",
              ("p1","BBB",2021,"roster-src","SOURCE_BACKED"))
    c.execute("INSERT INTO nfl_all_pro_selections VALUES(?,?,?,?,?,?)",
              ("p1","FIRST_TEAM",2023,1,"ap-src","WIKIPEDIA_STRUCTURED_SECONDARY"))

    # These are all structured facts; no verified lore event joins the path.
    chains = discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=5)
    assert chains == []


def test_compiled_deep_chain_has_provenance_and_no_answer_leak():
    c = _conn()
    _event(c, "compile")
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p1","AAA",2020,"draft-src","SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?,?)",
              ("p1","BBB",2021,"roster-src","SOURCE_BACKED"))
    c.execute("INSERT INTO nfl_all_pro_selections VALUES(?,?,?,?,?,?)",
              ("p1","FIRST_TEAM",2023,1,"ap-src","WIKIPEDIA_STRUCTURED_SECONDARY"))

    chains = discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=5)
    assert chains
    q = compile_lore_chain_question(chains[0])
    assert q["question_family"] == "DEEP_LORE_CHAIN"
    assert q["provenance"]["provenance_complete"] is True
    combined = " ".join(clue["text"] for clue in q["clues"]).casefold()
    assert q["answer"]["label"].casefold() not in combined
