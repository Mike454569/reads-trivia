import sqlite3
import pytest

from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.lore_chains import (
    _structured_edges,
    compile_lore_chain_question,
    discover_lore_chains,
)
from tools.director_v05.universal_schema import install


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT, display_name TEXT
    )""")
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p1", "Test Player"))
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
        "neutral_summary": "Test Player returned a bizarre broken-play touchdown after the ball changed hands twice.",
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
    q = compile_lore_chain_question(c, chains[0])
    assert q["question_family"] == "DEEP_LORE_CHAIN"
    assert q["question"] == "Who am I?"
    assert q["answer"]["label"] == "Test Player"
    assert q["provenance"]["provenance_complete"] is True
    combined = " ".join(clue["text"] for clue in q["clues"]).casefold()
    assert q["answer"]["label"].casefold() not in combined


def test_deep_lore_copy_uses_real_event_detail_not_engine_jargon():
    c = _conn()
    _event(c, "human-copy")
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p1","AAA",2020,"draft-src","SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?,?)",
              ("p1","BBB",2021,"roster-src","SOURCE_BACKED"))
    c.execute("INSERT INTO nfl_all_pro_selections VALUES(?,?,?,?,?,?)",
              ("p1","FIRST_TEAM",2023,1,"ap-src","WIKIPEDIA_STRUCTURED_SECONDARY"))

    q = compile_lore_chain_question(c, discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=5)[0])
    copy = " ".join([q["question"]] + [clue["text"] for clue in q["clues"]]).casefold()
    assert "verified chain" not in copy
    assert "subject of event" not in copy
    assert "structured fact" not in copy
    assert "strangest verified moment" not in copy
    assert "ball changed hands twice" in copy



def test_cfb_school_edges_use_real_game_log_source_ids():
    c = _conn()
    c.execute("""CREATE TABLE cfb_player_game_stats_real(
        cfb_player_id TEXT, school_id TEXT, season INTEGER,
        passing_yards INTEGER, rushing_yards INTEGER, rec_yards INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    c.execute("INSERT INTO cfb_player_game_stats_real VALUES(?,?,?,?,?,?,?,?)",
              ("cp1","ALA",2022,100,50,25,"cfb-src-a","SOURCE_BACKED_DERIVED"))
    c.execute("INSERT INTO cfb_player_game_stats_real VALUES(?,?,?,?,?,?,?,?)",
              ("cp1","TEX",2023,200,30,40,"cfb-src-b","SOURCE_BACKED_DERIVED"))

    edges = _structured_edges(c, "CFB_PLAYER", "cp1")
    assert [(e.relation,e.object_id) for e in edges] == [
        ("STARTED_AT","ALA"),
        ("TRANSFERRED_TO","TEX"),
    ]
    assert all(e.source_id and e.source_id.startswith("cfb-src") for e in edges)
    assert all(e.verification_status == "SOURCE_BACKED_DERIVED" for e in edges)


def test_derived_fact_without_evidence_is_not_a_chain_edge():
    c = _conn()
    c.execute(
        """INSERT INTO universal_derived_fact(
           derived_id,metric,subject_type,subject_id,value_num,value_text,
           formula_version,input_fact_ids_json,eligible_for_gameplay)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        ("d1","STEAL_SCORE","NFL_PLAYER","p1",9.0,None,"v1","[]",1),
    )
    assert not [e for e in _structured_edges(c, "NFL_PLAYER", "p1") if e.object_type == "DERIVED_FACT"]

    c.execute(
        """INSERT INTO universal_fact_evidence(
           fact_id,source_url,publisher,published_date,evidence_tier)
           VALUES(?,?,?,?,?)""",
        ("d1","https://example.com/evidence","Example",None,"AUTHORITATIVE"),
    )
    edges = [e for e in _structured_edges(c, "NFL_PLAYER", "p1") if e.object_type == "DERIVED_FACT"]
    assert len(edges) == 1
    assert edges[0].source_id == "https://example.com/evidence"



def test_reverse_team_traversal_is_season_local_and_source_backed():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p2", "Nearby Player"))
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p3", "Far Player"))
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p2","AAA",2021,"draft-near","SOURCE_BACKED"))
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p3","AAA",2010,"draft-far","SOURCE_BACKED"))

    edges = _structured_edges(c, "NFL_TEAM", "AAA", season_hint=2022)
    drafted = [e for e in edges if e.relation == "DRAFTED_PLAYER"]
    assert any(e.object_id == "p2" for e in drafted)
    assert all(e.object_id != "p3" for e in drafted)
    assert all(e.source_id for e in drafted)


def test_reverse_school_traversal_uses_verified_game_logs():
    c = _conn()
    c.execute("""CREATE TABLE cfb_player_game_stats_real(
        cfb_player_id TEXT, school_id TEXT, season INTEGER,
        passing_yards INTEGER, rushing_yards INTEGER, rec_yards INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    c.execute("INSERT INTO cfb_player_game_stats_real VALUES(?,?,?,?,?,?,?,?)",
              ("cp2","ALA",2023,100,20,30,"cfb-near","SOURCE_BACKED_DERIVED"))
    c.execute("INSERT INTO cfb_player_game_stats_real VALUES(?,?,?,?,?,?,?,?)",
              ("cp3","ALA",2015,100,20,30,"cfb-far","SOURCE_BACKED_DERIVED"))

    edges = _structured_edges(c, "SCHOOL", "ALA", season_hint=2022)
    players = [e for e in edges if e.relation == "SCHOOL_PLAYER"]
    assert any(e.object_id == "cp2" for e in players)
    assert all(e.object_id != "cp3" for e in players)
    assert all(e.verification_status == "SOURCE_BACKED_DERIVED" for e in players)


def test_cross_player_chain_can_traverse_event_team_to_another_player():
    c = _conn()
    c.execute("INSERT INTO canonical_players VALUES(?,?)", ("p2", "Second Player"))
    _event(c, "cross-player", player_id="p1", team_id="AAA")
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("p2","AAA",2021,"draft-p2","SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?,?)",
              ("p2","BBB",2022,"roster-p2","SOURCE_BACKED"))

    chains = discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=6)
    assert any(
        any(h.relation == "DRAFTED_PLAYER" and h.object_id == "p2" for h in chain.hops)
        for chain in chains
    )
    assert all(chain.provenance_complete for chain in chains)



def test_team_to_coach_reverse_edge_is_season_local():
    c = _conn()
    c.execute("""CREATE TABLE coach_team_seasons(
        coach_id TEXT, team_code TEXT, season INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    c.execute("INSERT INTO coach_team_seasons VALUES(?,?,?,?,?)",
              ("c1","AAA",2022,"coach-near","SOURCE_BACKED"))
    c.execute("INSERT INTO coach_team_seasons VALUES(?,?,?,?,?)",
              ("c2","AAA",2010,"coach-far","SOURCE_BACKED"))

    edges = _structured_edges(c, "NFL_TEAM", "AAA", season_hint=2022)
    coaches = [e for e in edges if e.relation == "TEAM_COACH"]
    assert any(e.object_id == "c1" for e in coaches)
    assert all(e.object_id != "c2" for e in coaches)
    assert all(e.source_id for e in coaches)


def test_deep_chain_can_cross_from_player_event_team_to_coach():
    c = _conn()
    c.execute("""CREATE TABLE coach_team_seasons(
        coach_id TEXT, team_code TEXT, season INTEGER,
        source_id TEXT, verification_status TEXT
    )""")
    _event(c, "coach-cross", player_id="p1", team_id="AAA")
    c.execute("INSERT INTO coach_team_seasons VALUES(?,?,?,?,?)",
              ("c1","AAA",2022,"coach-src","SOURCE_BACKED"))

    chains = discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=6)
    assert any(
        any(h.relation == "TEAM_COACH" and h.object_id == "c1" for h in chain.hops)
        for chain in chains
    )
    for chain in chains:
        visited = {(chain.anchor_type, chain.anchor_id)}
        for hop in chain.hops:
            node = (hop.object_type, hop.object_id)
            assert node not in visited
            visited.add(node)



def test_unresolved_answer_label_fails_closed():
    c = _conn()
    _event(c, "unresolved-answer", player_id="missing-player", team_id="AAA")
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("missing-player","AAA",2020,"draft-src","SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?,?)",
              ("missing-player","BBB",2021,"roster-src","SOURCE_BACKED"))
    chains = discover_lore_chains(c, "NFL_PLAYER", "missing-player", max_depth=5)
    if chains:
        with pytest.raises(ValueError, match="UNRESOLVED_ENTITY_LABEL"):
            compile_lore_chain_question(c, chains[0])


def test_cross_player_clue_requires_human_secondary_label():
    c = _conn()
    _event(c, "unresolved-secondary", player_id="p1", team_id="AAA")
    c.execute("INSERT INTO draft_facts VALUES(?,?,?,?,?)",
              ("unknown-p2","AAA",2021,"draft-p2","SOURCE_BACKED"))
    c.execute("INSERT INTO canonical_roster_seasons VALUES(?,?,?,?,?)",
              ("unknown-p2","BBB",2022,"roster-p2","SOURCE_BACKED"))

    chains = discover_lore_chains(c, "NFL_PLAYER", "p1", max_depth=6)
    cross = [
        ch for ch in chains
        if any(h.object_id == "unknown-p2" for h in ch.hops)
    ]
    for chain in cross:
        with pytest.raises(ValueError, match="UNRESOLVED_ENTITY_LABEL"):
            compile_lore_chain_question(c, chain)
