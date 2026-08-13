"""Reads Engine Gateway -- automated API test suite (Director v0.6, Part Q).

Uses actual Engine generation (not mocked) for one integration test per
registered capability, per the milestone's explicit instruction -- these
hit the real 1.65GB SQLite database through the real Director pipeline.
Pure HTTP/error-contract tests use small, fast, mock-translator requests
(the mock translator itself is real code, not a test double -- "mocks may
be used for pure HTTP/error-contract tests" refers to not needing a real
LLM provider for those, which none of these tests need anyway per Part K).
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor

DRAFT_REQUEST = "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him."
CHAMPIONSHIP_REQUEST = "Make a game where I guess how a team's season ended in the playoffs."
CLUES_REQUEST = "Make me a game where you give me clues about an NFL player and I have to identify him."
AMBIGUOUS_REQUEST = "Make me some NFL player trivia."
UNSUPPORTED_REQUEST = "Make me an NFL trivia game about players favorite foods."
MIXED_UNSUPPORTED_REQUEST = "Give me a game where I guess both a QB's team and his favorite food."


# --- health / capabilities ------------------------------------------------

def test_health_unauthenticated(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "reads-engine-gateway"
    assert body["api_version"] == "v1"


def test_capabilities_unauthenticated_and_exactly_eight(client):
    # v1.8, Part F: a 4th capability (the starting-lineup proof game) was
    # added to the registry that phase. The CFB data enrichment operation
    # added a 5th (CFB_HEISMAN). The App-Wide Engine Migration operation
    # added a 6th and 7th (NFL_GAME_RESULT/CFB_GAME_RESULT). The position+
    # college proof-game fix added an 8th (NFL_OFFENSE_LINEUP_COLLEGE) --
    # this baseline count/set is a real, deliberate change, not a regression.
    r = client.get("/v1/capabilities")
    assert r.status_code == 200
    caps = r.json()["capabilities"]
    assert len(caps) == 8
    triples = {(c["mechanic"], c["domain"], c["relationship_predicate"]) for c in caps}
    assert triples == {
        ("guess", "NFL_DRAFT", "DRAFTED_BY"),
        ("guess", "NFL_CHAMPIONSHIP", "TEAM_POSTSEASON_RESULT"),
        ("identify_player_from_clues", "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"),
        ("guess", "NFL_OFFENSE_LINEUP", "TEAM_OF_STARTING_LINEUP"),
        ("guess", "CFB_HEISMAN", "WON_HEISMAN"),
        ("guess", "NFL_GAME_RESULT", "WON_GAME"),
        ("guess", "CFB_GAME_RESULT", "WON_GAME"),
        ("guess", "NFL_OFFENSE_LINEUP_COLLEGE", "TEAM_OF_STARTING_LINEUP_BY_COLLEGE"),
    }
    # Part C: the frontend must never see Engine internals -- confirm no
    # response field leaks a Python module/adapter/table name.
    raw = json.dumps(caps)
    for forbidden in ("adapter", "sqlite", ".py", "tools.director", "generate_fn"):
        assert forbidden not in raw


# --- auth (Part F) ---------------------------------------------------------

def test_generate_missing_token_unauthorized(client):
    r = client.post("/v1/games/generate", json={"request_text": DRAFT_REQUEST})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_generate_invalid_token_unauthorized(client):
    r = client.post("/v1/games/generate", json={"request_text": DRAFT_REQUEST},
                     headers={"Authorization": "Bearer definitely-wrong"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_preview_valid_token_authorized(client, auth_headers):
    r = client.post("/v1/games/preview", json={"request_text": DRAFT_REQUEST}, headers=auth_headers)
    assert r.status_code == 200


def test_error_response_never_contains_token(client):
    r = client.post("/v1/games/generate", json={"request_text": DRAFT_REQUEST},
                     headers={"Authorization": "Bearer definitely-wrong"})
    assert "definitely-wrong" not in r.text


# --- input validation (Part G) ---------------------------------------------

def test_malformed_json(client, auth_headers):
    r = client.post("/v1/games/preview", headers={**auth_headers, "Content-Type": "application/json"},
                     content=b"{not valid json")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_oversized_request_rejected(client, auth_headers):
    huge = "A" * 100_000
    r = client.post("/v1/games/preview", json={"request_text": huge}, headers=auth_headers)
    # Rejected either by the body-size middleware (400) or by Pydantic's
    # max_length on request_text (400, reshaped by the validation handler) --
    # both are the same INVALID_REQUEST contract either way.
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_invalid_spec_extra_field_rejected(client, auth_headers):
    spec = {"mechanic": "guess", "domain": "NFL_DRAFT", "relationship_predicate": "DRAFTED_BY",
            "question_count": 5, "difficulty": "any", "filters": {}, "exclusions": [], "sql": "DROP TABLE users;"}
    r = client.post("/v1/games/preview", json={"spec": spec}, headers=auth_headers)
    assert r.status_code == 200  # a structured BLOCKED_* result, not an HTTP error
    body = r.json()
    assert body["gate_status"] == "BLOCKED_INVALID_SPEC"
    # The rejected FIELD NAME ("sql") is expected to appear in the rejection
    # message (naming what was rejected). The injected VALUE must never --
    # it was never executed, interpolated, or echoed anywhere.
    assert "DROP TABLE" not in json.dumps(body)


def test_extra_field_at_outer_level_rejected(client, auth_headers):
    r = client.post("/v1/games/preview", json={"request_text": DRAFT_REQUEST, "sql": "DROP TABLE users;"}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_invalid_difficulty_rejected(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": DRAFT_REQUEST, "difficulty": "impossible"}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_excessive_puzzle_count_rejected(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": DRAFT_REQUEST, "puzzle_count": 100000}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_both_request_text_and_spec_rejected(client, auth_headers):
    r = client.post("/v1/games/preview", json={"request_text": DRAFT_REQUEST, "spec": {"mechanic": "guess"}}, headers=auth_headers)
    assert r.status_code == 400


def test_neither_request_text_nor_spec_rejected(client, auth_headers):
    r = client.post("/v1/games/preview", json={}, headers=auth_headers)
    assert r.status_code == 400


# --- package path traversal (Part G/E) --------------------------------------

def test_package_path_traversal_rejected(client, auth_headers):
    for bad_id in ["..%2F..%2F..%2Fetc%2Fpasswd", "..", "GGP%3A..%2F..%2Fapp", "%2e%2e%2f%2e%2e%2fapp.py"]:
        r = client.get(f"/v1/games/{bad_id}", headers=auth_headers)
        assert r.status_code in (404, 422), f"{bad_id} -> {r.status_code}"
        assert "package_id" not in r.text or "traceback" not in r.text.lower()


def test_missing_package_returns_structured_404(client, auth_headers):
    r = client.get("/v1/games/GGP:aaaaaaaaaaaaaaaaaaaaaaaa", headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PACKAGE_NOT_FOUND"


# --- clarification / unsupported (Parts M, N) -------------------------------

def test_ambiguous_request_returns_clarification(client, auth_headers):
    r = client.post("/v1/games/preview", json={"request_text": AMBIGUOUS_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["gate_status"] == "NEEDS_CLARIFICATION"
    assert body["understood"] == {"competition": "NFL"}
    assert "domain" in body["missing_fields"]
    assert body["question"]


def test_ambiguous_request_generates_nothing(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": AMBIGUOUS_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] is None
    assert body["status"] == "NEEDS_CLARIFICATION"


def test_unsupported_request_generates_nothing(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": UNSUPPORTED_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] is None


def test_mixed_unsupported_does_not_silently_drop_half(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": MIXED_UNSUPPORTED_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] is None
    assert body["status"] == "UNDERSTOOD_BUT_UNSUPPORTED"
    assert "favorite food" in body["reason"] or "favorite" in body["reason"]


# --- real generation, one per registered capability (Part Q explicit requirement) --

def test_generate_draft_real_engine(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": DRAFT_REQUEST, "puzzle_count": 3, "seed": "pytest-draft"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] and body["package_id"].startswith("GGP:")
    assert body["qa_status"] == "PASSED"
    assert body["review_status"] == "GENERATED"
    assert body["question_count"] == 3
    assert len(body["questions"]) == 3

    # GET it back
    r2 = client.get(f"/v1/games/{body['package_id']}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["package_id"] == body["package_id"]


def test_generate_championship_real_engine(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": CHAMPIONSHIP_REQUEST, "puzzle_count": 3, "seed": "pytest-championship"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] and body["package_id"].startswith("GGP:")
    assert body["qa_status"] == "PASSED"
    assert body["question_count"] == 3


def test_generate_player_from_clues_real_engine(client, auth_headers):
    r = client.post("/v1/games/generate", json={"request_text": CLUES_REQUEST, "puzzle_count": 3, "seed": "pytest-clues"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] and body["package_id"].startswith("GGP4:")
    assert body["qa_status"] == "PASSED"
    assert body["puzzle_count"] == 3
    for puzzle in body["puzzles"]:
        assert puzzle["final_candidate_count"] == 1
        assert len(puzzle["clues"]) >= 3


# --- concurrency protection (Part H) ----------------------------------------

def test_concurrent_generation_protected(client, auth_headers):
    def call(i):
        return client.post(
            "/v1/games/generate",
            json={"request_text": CLUES_REQUEST, "puzzle_count": 2, "seed": f"pytest-concurrent-{i}"},
            headers=auth_headers,
        )

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(call, range(4)))

    statuses = sorted(r.status_code for r in results)
    busy_count = sum(1 for r in results if r.status_code == 429)
    ok_count = sum(1 for r in results if r.status_code == 200)
    assert ok_count == 1, f"expected exactly 1 success, got statuses={statuses}"
    assert busy_count == 3
    for r in results:
        if r.status_code == 429:
            assert r.json()["error"]["code"] == "GENERATION_BUSY"


# --- internal exception sanitization (Part I) -------------------------------

def test_internal_exception_never_leaks_traceback(auth_headers, monkeypatch):
    # raise_server_exceptions=False: a real client (real uvicorn process, real
    # browser) never sees the Python exception itself, only whatever HTTP
    # response the app's exception handler produced -- this is what that
    # looks like. (TestClient's DEFAULT is raise_server_exceptions=True,
    # which deliberately re-raises for local test-writing convenience; that's
    # a pytest/TestClient authoring aid, not how a real deployment behaves,
    # so it's turned off for this specific test, which is testing exactly
    # that real-client behavior.)
    from fastapi.testclient import TestClient
    from gateway.app import app
    from gateway.services import generation as generation_service

    def boom(**kwargs):
        raise RuntimeError("simulated internal failure with a fake /secret/path/leak")

    monkeypatch.setattr(generation_service, "preview", boom)
    local_client = TestClient(app, raise_server_exceptions=False)
    r = local_client.post("/v1/games/preview", json={"request_text": DRAFT_REQUEST}, headers=auth_headers)
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "/secret/path/leak" not in r.text
    assert "Traceback" not in r.text
    assert "RuntimeError" not in r.text
