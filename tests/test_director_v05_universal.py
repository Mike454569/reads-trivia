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


def test_chain_rejects_missing_provenance():
    import pytest
    from tools.director_v05.chain_engine import Hop,build_chain
    with pytest.raises(ValueError):
        build_chain("NFL_PLAYER","p1",[Hop("A","p1","x"),Hop("B","p1","y")])

def test_chain_quality_rejects_ambiguous_signature():
    from tools.director_v05.chain_engine import Hop,build_chain
    from tools.director_v05.chain_quality import eligible_chains,explain_rejection
    hs=lambda p:[Hop("DRAFTED_BY",p,"PIT",2020,"NFLVERSE_DATA","SOURCE_BACKED"),Hop("ALL_PRO",p,"FIRST_TEAM",2023,"WIKIPEDIA_STRUCTURED","WIKIPEDIA_STRUCTURED_SECONDARY")]
    a=build_chain("NFL_PLAYER","p1",hs("p1")); b=build_chain("NFL_PLAYER","p2",hs("p2"))
    assert eligible_chains([a,b])==[]
    assert explain_rejection(a,[a,b])=="AMBIGUOUS_CHAIN"

def test_chain_compiler_preserves_answer_provenance():
    from tools.director_v05.chain_engine import Hop,build_chain
    from tools.director_v05.chain_compiler import compile_chain
    c=build_chain("NFL_PLAYER","p1",[Hop("DRAFTED_BY","p1","PIT",2020,"NFLVERSE_DATA","SOURCE_BACKED"),Hop("ALL_PRO","p1","FIRST_TEAM",2023,"WIKIPEDIA_STRUCTURED","WIKIPEDIA_STRUCTURED_SECONDARY")])
    q=compile_chain(c,"WHO_AM_I")
    assert q["answer"]["id"]=="p1"
    assert q["answer_provenance_required"] is True
    assert len(q["clues"])==2


def test_progressive_clues_delay_giveaway_hof():
    from tools.director_v05.chain_engine import Hop,build_chain
    from tools.director_v05.clue_intelligence import order_progressive_clues
    chain=build_chain("NFL_PLAYER","p1",[
      Hop("HOF","p1","HOF",2028,"WIKIPEDIA_STRUCTURED","WIKIPEDIA_STRUCTURED_SECONDARY"),
      Hop("DRAFTED_BY","p1","PIT",2020,"NFLVERSE_DATA","SOURCE_BACKED"),
      Hop("GAME_APPEARANCE","p1","g1",2024,"NFLVERSE_DATA","SOURCE_BACKED"),
    ])
    clues=order_progressive_clues(chain,current_season=2026,max_clues=3)
    assert clues[-1]["relation"]=="HOF"

def test_sicko_planner_is_real_behavior_not_label_only():
    from tools.director_v05.chain_engine import Hop,build_chain
    from tools.director_v05.difficulty_planner import plan
    chain=build_chain("NFL_PLAYER","p1",[
      Hop("DRAFTED_BY","p1","PIT",2020,"NFLVERSE_DATA","SOURCE_BACKED"),
      Hop("ALL_PRO","p1","FIRST_TEAM",2024,"WIKIPEDIA_STRUCTURED","WIKIPEDIA_STRUCTURED_SECONDARY"),
      Hop("GAME_APPEARANCE","p1","g1",2025,"NFLVERSE_DATA","SOURCE_BACKED"),
    ])
    stats={
      ("DRAFTED_BY","PIT",2020):{"population":1000,"matching":120},
      ("ALL_PRO","FIRST_TEAM",2024):{"population":1000,"matching":20},
      ("GAME_APPEARANCE","g1",2025):{"population":1000,"matching":2},
    }
    p=plan(chain,"SICKO",stats=stats,current_season=2026)
    assert p["difficulty_band"]=="SICKO"
    assert p["clues"][0]["giveaway_risk"]<=0.40

def test_chain_compiler_embeds_clue_plan():
    from tools.director_v05.chain_engine import Hop,build_chain
    from tools.director_v05.chain_compiler import compile_chain
    chain=build_chain("NFL_PLAYER","p1",[
      Hop("DRAFTED_BY","p1","PIT",2020,"NFLVERSE_DATA","SOURCE_BACKED"),
      Hop("ALL_PRO","p1","FIRST_TEAM",2024,"WIKIPEDIA_STRUCTURED","WIKIPEDIA_STRUCTURED_SECONDARY"),
    ])
    q=compile_chain(chain,"THREE_CLUES",difficulty_band="HARD",current_season=2026)
    assert q["compiler_version"]=="1.1.0"
    assert q["clue_plan"]["difficulty_band"]=="HARD"


def _verified_player_chain():
    from tools.director_v05.chain_engine import Hop, build_chain
    return build_chain("NFL_PLAYER","p1",[
        Hop("DRAFTED_BY","p1","PIT",2020,"NFLVERSE_DATA","SOURCE_BACKED"),
        Hop("ALL_PRO","p1","FIRST_TEAM",2023,"WIKIPEDIA_STRUCTURED","WIKIPEDIA_STRUCTURED_SECONDARY"),
    ])


def test_story_chain_fuses_verified_event_and_career_evidence():
    from tools.director_v05.story_chain import compile_story_chain
    event={
      "event_id":"evt_1","event_type":"MEDIA_EVENT","league":"NFL","event_date":"2024-10-01",
      "title":"A bizarre verified football moment","neutral_summary":"A documented odd event occurred.",
      "source_url":"https://example.com/story","source_publisher":"Example","source_date":"2024-10-02",
      "evidence_tier":"REPUTABLE_MEDIA","verification_status":"VERIFIED",
      "subjects":[{"subject_type":"player","subject_id":"p1"}],
    }
    material=compile_story_chain(event,_verified_player_chain(),"THREE_CLUES")
    assert material["material_type"]=="STORY_CHAIN"
    assert material["answer"]["id"]=="p1"
    assert material["answer_provenance_required"] is True
    assert len(material["clues"])==3
    assert material["reveal"]["title"]==event["title"]
    assert "title" not in material["clues"][-1]


def test_story_chain_rejects_unverified_event():
    import pytest
    from tools.director_v05.story_chain import compile_story_chain
    event={
      "event_id":"evt_2","event_type":"MEDIA_EVENT","league":"NFL",
      "source_url":"https://example.com/story","source_publisher":"Example",
      "evidence_tier":"REPUTABLE_MEDIA","verification_status":"PENDING",
      "subjects":[{"subject_type":"player","subject_id":"p1"}],
    }
    with pytest.raises(ValueError,match="VERIFIED"):
        compile_story_chain(event,_verified_player_chain(),"WHO_AM_I")


def test_story_chain_requires_event_subject_to_match_answer():
    import pytest
    from tools.director_v05.story_chain import compile_story_chain
    event={
      "event_id":"evt_3","event_type":"MEDIA_EVENT","league":"NFL",
      "source_url":"https://example.com/story","source_publisher":"Example",
      "evidence_tier":"REPUTABLE_MEDIA","verification_status":"VERIFIED",
      "subjects":[{"subject_type":"player","subject_id":"different-player"}],
    }
    with pytest.raises(ValueError,match="subject does not match"):
        compile_story_chain(event,_verified_player_chain(),"WHO_AM_I")


def test_sensitive_story_chain_preserves_legal_stage_without_inferring_guilt():
    from tools.director_v05.story_chain import compile_story_chain
    event={
      "event_id":"evt_4","event_type":"CHARGE","league":"NFL","event_date":"2024-01-01",
      "title":"Documented legal event","neutral_summary":"A charge was filed; no disposition is implied.",
      "source_url":"https://example.com/court","source_publisher":"Example Court",
      "evidence_tier":"AUTHORITATIVE","verification_status":"VERIFIED",
      "legal_stage":"CHARGED","sensitive":True,
      "subjects":[{"subject_type":"player","subject_id":"p1"}],
    }
    material=compile_story_chain(event,_verified_player_chain(),"THREE_CLUES")
    assert material["story"]["legal_stage"]=="CHARGED"
    assert material["requires_precise_legal_language"] is True
    assert material["no_guilt_inference"] is True
    assert material["clues"][-1]["legal_stage"]=="CHARGED"


def test_story_engine_auto_discovers_playable_material_and_suppresses_repeats():
    import sqlite3
    from tools.director_v05.event_ingest import upsert_event
    from tools.director_v05.story_engine import compile_story_candidates

    conn=sqlite3.connect(":memory:")
    conn.row_factory=sqlite3.Row
    eid=upsert_event(conn,{
      "event_type":"MEDIA_EVENT","league":"NFL","event_date":"2024-10-01",
      "title":"Verified odd football moment","neutral_summary":"A documented odd event occurred.",
      "source_url":"https://example.com/story","source_publisher":"Example",
      "source_date":"2024-10-02","evidence_tier":"REPUTABLE_MEDIA",
      "verification_status":"VERIFIED","tags":["funny","oddity"],
      "subjects":[{"subject_type":"player","subject_id":"p1"}]
    })

    def provider(_conn, subject_id):
        return [_verified_player_chain()] if subject_id=="p1" else []

    rows=compile_story_candidates(conn,"FUNNY_MOMENTS","THREE_CLUES",chain_provider=provider,league="NFL",limit=5)
    assert len(rows)==1
    assert rows[0]["story"]["event_id"]==eid
    assert rows[0]["answer"]["id"]=="p1"

    rows2=compile_story_candidates(
        conn,"FUNNY_MOMENTS","THREE_CLUES",chain_provider=provider,
        league="NFL",limit=5,recent_event_ids=[eid]
    )
    assert rows2==[]


def test_story_engine_skips_subjects_without_verified_deep_chain():
    import sqlite3
    from tools.director_v05.event_ingest import upsert_event
    from tools.director_v05.story_engine import compile_story_candidates

    conn=sqlite3.connect(":memory:")
    conn.row_factory=sqlite3.Row
    upsert_event(conn,{
      "event_type":"MEDIA_EVENT","league":"NFL","event_date":"2024-10-01",
      "title":"Verified odd football moment","neutral_summary":"A documented odd event occurred.",
      "source_url":"https://example.com/story","source_publisher":"Example",
      "evidence_tier":"REPUTABLE_MEDIA","verification_status":"VERIFIED",
      "tags":["funny"],"subjects":[{"subject_type":"player","subject_id":"p2"}]
    })
    assert compile_story_candidates(
        conn,"FUNNY_MOMENTS","WHO_AM_I",chain_provider=lambda *_: [],limit=5
    )==[]
