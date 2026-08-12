"""v1.8, Part B/C/G/H/L -- tests for the Game Creator's Gateway routes
(/v1/creator/*). Admin-only, real-engine tests -- no mocking of the
translator/generation/QA path, matching the discipline every other
real-generation test in this suite already follows.
"""
DRAFT_REQUEST = "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him."
LINEUP_REQUEST = "Guess the NFL team from the colleges attended by the players on its offense, displayed by position."
UNSUPPORTED_REQUEST = "Make me an NFL trivia game about players favorite foods."
GIBBERISH_REQUEST = "asdkjaslkdj random nonsense not football at all"


# --- auth (Part L: admin-only, no exception) --------------------------------

def test_creator_feasibility_requires_admin(client):
    r = client.post("/v1/creator/feasibility", json={"request_text": DRAFT_REQUEST})
    assert r.status_code == 401


def test_creator_generate_requires_admin(client):
    r = client.post("/v1/creator/generate", json={"request_text": DRAFT_REQUEST})
    assert r.status_code == 401


def test_creator_queue_requires_admin(client):
    r = client.get("/v1/creator/queue")
    assert r.status_code == 401


def test_creator_review_requires_admin(client):
    r = client.post("/v1/creator/review", json={"package_id": "GGP:" + "a" * 24, "review_status": "APPROVED"})
    assert r.status_code == 401


def test_creator_capabilities_requires_admin(client):
    r = client.get("/v1/creator/capabilities")
    assert r.status_code == 401


# --- Part L: no code/spec injection surface ---------------------------------

def test_creator_feasibility_rejects_a_spec_field(client, auth_headers):
    # CreatorFeasibilityRequest has NO `spec` field at all (extra="forbid") --
    # a client cannot hand-craft a structured spec to try to reach an
    # unregistered/internal capability triple directly.
    r = client.post(
        "/v1/creator/feasibility",
        json={"request_text": DRAFT_REQUEST, "spec": {"mechanic": "guess"}},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_creator_feasibility_rejects_empty_text(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": ""}, headers=auth_headers)
    assert r.status_code == 400


def test_creator_feasibility_rejects_oversized_text(client, auth_headers):
    from gateway import config
    r = client.post(
        "/v1/creator/feasibility",
        json={"request_text": "x" * (config.MAX_REQUEST_TEXT_CHARS + 1)},
        headers=auth_headers,
    )
    assert r.status_code == 400


# --- feasibility (Part C) ----------------------------------------------------

def test_creator_feasibility_supported(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": DRAFT_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["support_status"] == "SUPPORTED"


def test_creator_feasibility_supported_with_limitations_for_proof_game(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": LINEUP_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert len(body["known_limitations"]) == 3


def test_creator_feasibility_understood_but_unsupported(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": UNSUPPORTED_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    # "favorite foods" alone (no "both" coordination signal) is plain NO_MATCH,
    # not UNDERSTOOD_UNSUPPORTED_MECHANIC -- see mock.py's own module docstring.
    assert r.json()["support_status"] == "UNKNOWN"


def test_creator_feasibility_unknown_for_gibberish(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": GIBBERISH_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["support_status"] == "UNKNOWN"


# --- generate + review queue (Part G/H) --------------------------------------

def test_creator_generate_then_appears_in_queue_as_generated(client, auth_headers):
    r = client.post(
        "/v1/creator/generate",
        json={"request_text": DRAFT_REQUEST, "puzzle_count": 2, "seed": "pytest-creator-gen-1"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] and body["qa_status"] == "PASSED"
    assert body["review_status"] == "GENERATED"

    r2 = client.get("/v1/creator/queue", params={"review_status": "GENERATED"}, headers=auth_headers)
    assert r2.status_code == 200
    ids = {p["package_id"] for p in r2.json()["packages"]}
    assert body["package_id"] in ids


def test_creator_approve_then_reflected_in_queue_and_package(client, auth_headers):
    gen = client.post(
        "/v1/creator/generate",
        json={"request_text": DRAFT_REQUEST, "puzzle_count": 2, "seed": "pytest-creator-approve-1"},
        headers=auth_headers,
    ).json()
    pid = gen["package_id"]

    r = client.post("/v1/creator/review", json={"package_id": pid, "review_status": "APPROVED"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["review_status"] == "APPROVED"
    assert r.json()["reviewed_at"]

    r2 = client.get(f"/v1/games/{pid}", headers=auth_headers)
    assert r2.json()["review_status"] == "APPROVED"

    r3 = client.get("/v1/creator/queue", params={"review_status": "APPROVED"}, headers=auth_headers)
    ids = {p["package_id"] for p in r3.json()["packages"]}
    assert pid in ids


def test_creator_reject_then_reflected(client, auth_headers):
    gen = client.post(
        "/v1/creator/generate",
        json={"request_text": DRAFT_REQUEST, "puzzle_count": 2, "seed": "pytest-creator-reject-1"},
        headers=auth_headers,
    ).json()
    pid = gen["package_id"]
    r = client.post("/v1/creator/review", json={"package_id": pid, "review_status": "REJECTED"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["review_status"] == "REJECTED"


def test_creator_review_unknown_package_404(client, auth_headers):
    fake_id = "GGP:" + "0" * 24
    r = client.post("/v1/creator/review", json={"package_id": fake_id, "review_status": "APPROVED"}, headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PACKAGE_NOT_FOUND"


def test_creator_review_rejects_generated_as_a_target_status(client, auth_headers):
    # GENERATED is set only by generation itself -- not a human-settable
    # target of the review action (models.py's Literal excludes it).
    r = client.post(
        "/v1/creator/review",
        json={"package_id": "GGP:" + "0" * 24, "review_status": "GENERATED"},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_creator_queue_invalid_review_status_filter_rejected(client, auth_headers):
    r = client.get("/v1/creator/queue", params={"review_status": "NOT_A_REAL_STATUS"}, headers=auth_headers)
    assert r.status_code == 400


# --- capability reference (Part C) -------------------------------------------

def test_creator_capabilities_lists_seven_with_real_statuses(client, auth_headers):
    r = client.get("/v1/creator/capabilities", headers=auth_headers)
    assert r.status_code == 200
    caps = r.json()["capabilities"]
    assert len(caps) == 7
    lineup = next(c for c in caps if c["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP")
    assert lineup["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    heisman = next(c for c in caps if c["relationship_predicate"] == "WON_HEISMAN")
    assert heisman["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    game_results = [c for c in caps if c["relationship_predicate"] == "WON_GAME"]
    assert len(game_results) == 2
    assert {c["domain"] for c in game_results} == {"NFL_GAME_RESULT", "CFB_GAME_RESULT"}
    assert all(c["support_status"] == "SUPPORTED_WITH_LIMITATIONS" for c in game_results)
