"""v1.8, Part F -- real-engine tests for the Starting Lineup capability, the
milestone's primary acceptance test. Hits the real Engine database through
the real Director pipeline (Part Q's "one integration test per registered
capability", extended here with the extra scrutiny this capability needs
given its "truthful supported variant" framing -- see
tools/quiz_export/adapters/lineup.py's module docstring).

COLLEGE_PHRASED_REQUEST is the LITERAL proof-game request text from the
v1.8 spec ("guess the team from the colleges of the players on its offense,
by position"). The capability this routes to does NOT use colleges (see the
adapter's docstring for why) -- these tests assert that honesty directly:
no generated field ever claims a college was used.
"""
import json

COLLEGE_PHRASED_REQUEST = (
    "Guess the NFL team from the colleges attended by the players on its offense, displayed by position."
)
LINEUP_REQUEST = "Make a game where I guess the NFL team from its starting offensive lineup, by position."


def test_capability_registered_with_position_lineup_template(client):
    r = client.get("/v1/capabilities")
    assert r.status_code == 200
    caps = r.json()["capabilities"]
    lineup_caps = [c for c in caps if c["domain"] == "NFL_OFFENSE_LINEUP"]
    assert len(lineup_caps) == 1
    cap = lineup_caps[0]
    assert cap["mechanic"] == "guess"
    assert cap["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP"
    assert cap["visual_template"] == "POSITION_LINEUP"


def test_college_phrased_request_routes_here_and_generates_real_data(client, auth_headers):
    r = client.post(
        "/v1/games/generate",
        json={"request_text": COLLEGE_PHRASED_REQUEST, "puzzle_count": 5, "seed": "pytest-lineup-college-phrase"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] and body["package_id"].startswith("GGP:")
    assert body["qa_status"] == "PASSED"
    assert body["question_count"] == 5
    assert body["parsed_spec"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP"

    # Honesty check: the GENERATED CONTENT (not the echoed-back request text,
    # which naturally still says "colleges" verbatim) never claims colleges
    # were used -- see module docstring.
    assert "college" not in body["game_instructions"].lower()
    assert "college" not in body["game_title"].lower()
    for q in body["questions"]:
        assert "college" not in q["question"].lower()
        assert "college" not in q["notes"].lower()
        assert "college" not in json.dumps(q["visual_payload"]).lower()

    for q in body["questions"]:
        assert q["visual_template"] == "POSITION_LINEUP"
        payload = q["visual_payload"]
        assert payload["season"] is not None
        positions = payload["positions"]
        assert [p["position"] for p in positions] == ["QB", "RB", "WR", "WR", "TE", "OL", "OL", "OL", "OL", "OL"]
        # Every player is a real, non-empty name with a positive real starts count.
        for p in positions:
            assert isinstance(p["name"], str) and p["name"].strip()
            assert isinstance(p["starts"], int) and p["starts"] > 0
        # The correct answer is a real, non-empty team name among 4 unique options.
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert q["options"][q["correctIndex"]] == q["answer"]
        # The answer team name itself is never one of the 10 player names shown
        # (a sanity check that we're not accidentally leaking the answer INTO the board).
        assert q["answer"] not in [p["name"] for p in positions]


def test_plain_lineup_phrasing_also_routes_correctly(client, auth_headers):
    r = client.post(
        "/v1/games/generate",
        json={"request_text": LINEUP_REQUEST, "puzzle_count": 1, "seed": "pytest-lineup-plain-phrase"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["qa_status"] == "PASSED"
    assert body["parsed_spec"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP"


def test_real_seasons_and_no_duplicate_questions_across_a_large_batch(client, auth_headers):
    r = client.post(
        "/v1/games/generate",
        json={"request_text": LINEUP_REQUEST, "puzzle_count": 100, "seed": "pytest-lineup-batch"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["qa_status"] == "PASSED"
    questions = body["questions"]
    assert len(questions) > 50  # real, non-trivial yield -- audited coverage is 412/415 real team-seasons
    seasons = {q["visual_payload"]["season"] for q in questions}
    assert seasons <= set(range(2006, 2019))
    question_texts = [q["question"] for q in questions]
    assert len(question_texts) == len(set(question_texts))  # no duplicate prompts
    ids = [q["id"] for q in questions]
    assert min(ids) >= 640000  # this capability's reserved ID block


def test_preview_recognizes_college_phrased_request_without_generating(client, auth_headers):
    r = client.post("/v1/games/preview", json={"request_text": COLLEGE_PHRASED_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["gate_status"] == "READY"
    assert body["capability"]["domain"] == "NFL_OFFENSE_LINEUP"
