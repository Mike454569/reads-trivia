from tools.director_v05.capability_compiler import compile_capabilities, eligible_event_where

def test_missing_family_blocks_concept():
    cov={"families":{"culture_story":{"status":"MISSING"},"off_field":{"status":"PRESENT"}}}
    assert compile_capabilities(cov)["FUNNY_MOMENTS"]["status"]=="UNSUPPORTED"

def test_partial_family_limits_concept():
    cov={"families":{"draft":{"status":"PRESENT"},"derived":{"status":"PARTIAL"}}}
    assert compile_capabilities(cov)["DRAFT_BUSTS"]["status"]=="SUPPORTED_WITH_LIMITATIONS"

def test_sensitive_events_require_verified_evidence():
    where,args=eligible_event_where("LEGAL_HISTORY")
    assert "verification_status='VERIFIED'" in where
    assert "evidence_tier IN" in where
    assert "legal" in args


def test_event_ingest_and_query_roundtrip():
    import sqlite3
    from tools.director_v05.event_ingest import upsert_event
    from tools.director_v05.query_engine import query_events
    conn=sqlite3.connect(":memory:")
    eid=upsert_event(conn,{
      "event_type":"MEDIA_EVENT","league":"NFL","event_date":"2020-01-01",
      "title":"Odd football moment","neutral_summary":"A verified odd event occurred.",
      "source_url":"https://example.com/story","source_publisher":"Example",
      "evidence_tier":"REPUTABLE_MEDIA","verification_status":"VERIFIED",
      "tags":["funny","oddity"],"subjects":[{"subject_type":"player","subject_id":"p1"}]
    })
    rows=query_events(conn,"FUNNY_MOMENTS",league="NFL")
    assert rows and rows[0]["event_id"]==eid

def test_sensitive_secondary_source_is_rejected():
    import sqlite3, pytest
    from tools.director_v05.event_ingest import upsert_event
    conn=sqlite3.connect(":memory:")
    with pytest.raises(ValueError):
      upsert_event(conn,{
        "event_type":"LEGAL_EVENT","league":"NFL","event_date":"2020-01-01",
        "title":"Legal event","neutral_summary":"Neutral legal summary.",
        "source_url":"https://example.com/post","source_publisher":"Example",
        "evidence_tier":"SECONDARY","verification_status":"VERIFIED",
        "jurisdiction":"Example County","legal_stage":"CHARGED","tags":["legal"]
      })

def test_unverified_event_never_reaches_creator():
    import sqlite3
    from tools.director_v05.event_ingest import upsert_event
    from tools.director_v05.query_engine import query_events
    conn=sqlite3.connect(":memory:")
    upsert_event(conn,{
      "event_type":"MEDIA_EVENT","league":"NFL","event_date":"2020-01-01",
      "title":"Pending oddity","neutral_summary":"Pending verification.",
      "source_url":"https://example.com/story","source_publisher":"Example",
      "evidence_tier":"REPUTABLE_MEDIA","verification_status":"PENDING",
      "tags":["funny"]
    })
    assert query_events(conn,"FUNNY_MOMENTS")==[]


def test_derived_fact_requires_provenance():
    import sqlite3, pytest
    from tools.director_v05.derivations import store
    conn=sqlite3.connect(":memory:")
    with pytest.raises(ValueError):
        store(conn,"bust_score","player","p1",88,[])

def test_draft_bust_recipe_composes_with_higher_lower():
    from tools.director_v05.recipe_compiler import compile_recipe
    r=compile_recipe("DRAFT_BUSTS","HIGHER_LOWER",league="NFL")
    assert r["source"]=="derived"
    assert r["metric"]=="bust_score"
    assert r["answer_provenance_required"] is True

def test_story_recipe_requires_verified_evidence():
    from tools.director_v05.recipe_compiler import compile_recipe
    r=compile_recipe("ABSURD_STORIES","THREE_CLUES",league="NFL")
    assert r["source"]=="events"
    assert r["requires_verified_evidence"] is True


def test_legacy_bridge_stable_fact_ids():
    import sqlite3
    from tools.director_v05.legacy_bridge import iter_facts
    conn=sqlite3.connect(":memory:"); conn.row_factory=sqlite3.Row
    conn.execute("CREATE TABLE games(game_id TEXT,season INT,week INT,game_type TEXT,game_date TEXT,away_team TEXT,away_score INT,home_team TEXT,home_score INT,source_id TEXT)")
    conn.execute("INSERT INTO games VALUES('g1',2025,1,'REG','2025-09-01','A',10,'B',20,'NFLVERSE_DATA')")
    a=list(iter_facts(conn,"nfl_games")); b=list(iter_facts(conn,"nfl_games"))
    assert a[0]["fact_id"]==b[0]["fact_id"]
    assert a[0]["kind"]=="GAME_RESULT"

def test_relationship_traversal_is_allowlisted():
    import sqlite3, pytest
    from tools.director_v05.relationships import traverse
    conn=sqlite3.connect(":memory:")
    with pytest.raises(ValueError):
        traverse(conn,"DROP_TABLES","x")


def test_multihop_rejects_shallow_chain():
    import pytest
    from tools.director_v05.multihop import mechanic_payload
    with pytest.raises(ValueError):
        mechanic_payload({"subject_type":"player","subject_id":"p1","depth":1,"clues":[{"type":"draft","text":"x","weight":1}],"depth_score":1,"input_fact_ids":["f1"]},"WHO_AM_I")

def test_ambiguity_gate_rejects_collision():
    from tools.director_v05.ambiguity import uniqueness_check
    clues=[{"type":"draft","text":"Drafted in round 1."},{"type":"honor","text":"Earned 1 AP All-Pro selection(s)."}]
    target={"subject_id":"p1","clues":clues}
    other={"subject_id":"p2","clues":clues}
    result=uniqueness_check(target,[target,other])
    assert result["unique"] is False
    assert result["collisions"]==["p2"]

def test_uniqueness_gate_accepts_distinct_chain():
    from tools.director_v05.ambiguity import uniqueness_check,certify_payload
    target={"subject_id":"p1","clues":[{"type":"draft","text":"A"},{"type":"honor","text":"B"}]}
    other={"subject_id":"p2","clues":[{"type":"draft","text":"C"},{"type":"honor","text":"D"}]}
    u=uniqueness_check(target,[target,other])
    payload={"input_fact_ids":["f1","f2"],"requires_unique_answer":True}
    assert certify_payload(payload,u)["certified"] is True
