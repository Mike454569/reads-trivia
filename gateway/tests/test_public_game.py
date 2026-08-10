"""Tests for the v1.2 public gameplay pilot (gateway/services/public_game.py,
gateway/app.py's /v1/public/* routes).

Runs against the real, checksum-verified Reads_v4_Database.sqlite via the
same Director pipeline /v1/games/generate already uses -- not mocked. Every
route here is deliberately called WITHOUT auth_headers (the whole point:
these routes must work with no admin token, unlike every other route in
this Gateway)."""
import time

from gateway import config
from gateway.errors import ERROR_CODES
from gateway.services import packages


def _get_game(client, **params):
    params.setdefault("mode", "draft_guess")
    return client.get("/v1/public/game", params=params)


# --- public auth (no admin token needed) -------------------------------------

def test_public_modes_no_auth_needed(client):
    r = client.get("/v1/public/modes")
    assert r.status_code == 200
    assert {"mode": "draft_guess", "competition": "NFL", "title": "NFL Draft History: Guess the Team"} in r.json()["modes"]


def test_public_game_no_auth_needed(client):
    r = _get_game(client)
    assert r.status_code == 200


def test_public_answer_no_auth_needed(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "anything"})
    assert r.status_code == 200


def test_admin_routes_still_require_admin_auth(client):
    # Regression: adding public routes must not have loosened any existing
    # admin route's auth requirement.
    assert client.get("/v1/graph/search", params={"query": "Mahomes"}).status_code == 401
    assert client.get("/v1/grid/criteria").status_code == 401
    assert client.post("/v1/games/generate", json={"request_text": "x"}).status_code == 401


# --- answer leakage -----------------------------------------------------------

def test_game_payload_never_contains_answer(client):
    r = _get_game(client)
    raw = r.text
    body = r.json()
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh /v1/public/game response"
    assert set(body.keys()) == {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}
    assert set(body["payload"].keys()) == {"prompt", "options"}
    assert len(body["payload"]["options"]) == 4


def test_answer_response_reveals_canonical_answer_only_after_guessing(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "anything"})
    body = r.json()
    assert set(body.keys()) == {"correct", "canonical_answer", "notes"}
    assert body["canonical_answer"] in game["payload"]["options"]


# --- answer validation ---------------------------------------------------------

def test_correct_answer_accepted(client):
    game = _get_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_incorrect_answer_rejected(client):
    game = _get_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False
    assert body["canonical_answer"] == real_answer


def test_answer_case_and_whitespace_insensitive(client):
    game = _get_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "  " + real_answer.upper() + "  "})
    assert r.json()["correct"] is True


# --- game identity / tampering -------------------------------------------------

def test_unknown_game_id_rejected(client):
    r = client.post("/v1/public/game/answer", json={"game_id": "GGP:0000000000000000000000", "answer": "x"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


def test_malformed_game_id_rejected_same_as_unknown(client):
    # Never distinguish "malformed" from "genuinely missing" to the client
    # (same reasoning packages.load_package's own docstring already gives).
    r = client.post("/v1/public/game/answer", json={"game_id": "not-a-real-id-at-all", "answer": "x"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


def test_answer_request_extra_field_rejected(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x", "score": 100})
    assert r.status_code == 400


# --- mode allow-list -----------------------------------------------------------

def test_unknown_mode_is_invalid_mode(client):
    r = _get_game(client, mode="not_a_real_mode")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_MODE"


def test_known_internal_but_not_public_mode_is_mode_unavailable(client):
    r = _get_game(client, mode="championship_guess")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MODE_UNAVAILABLE"
    r2 = _get_game(client, mode="player_from_clues")
    assert r2.json()["error"]["code"] == "MODE_UNAVAILABLE"


def test_grid_and_six_degrees_are_not_public_modes(client):
    # Part 34/35: neither is migrated in v1.2 -- confirm they're not
    # accidentally reachable as a "mode" through this new surface.
    assert "grid" not in config.PUBLIC_MODE_ALLOWLIST
    assert "six_degrees" not in config.PUBLIC_MODE_ALLOWLIST
    assert config.PUBLIC_MODE_ALLOWLIST == frozenset({"draft_guess"})


# --- determinism ----------------------------------------------------------------

def test_same_seed_same_mode_returns_same_game(client):
    g1 = _get_game(client, seed="pytest-fixed-seed-1").json()
    g2 = _get_game(client, seed="pytest-fixed-seed-1").json()
    assert g1["game_id"] == g2["game_id"]
    assert g1["payload"]["prompt"] == g2["payload"]["prompt"]


def test_different_seeds_can_return_different_games(client):
    g1 = _get_game(client, seed="pytest-seed-aaa").json()
    g2 = _get_game(client, seed="pytest-seed-bbb").json()
    assert g1["game_id"] != g2["game_id"]


# --- validation -------------------------------------------------------------

def test_invalid_difficulty_rejected(client):
    r = _get_game(client, difficulty="nonsense")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_missing_mode_param_rejected(client):
    r = client.get("/v1/public/game")
    assert r.status_code == 400


# --- rate limiting ---------------------------------------------------------

def test_rate_limit_enforced_on_public_game(client, monkeypatch):
    from gateway.app import public_game_limiter
    monkeypatch.setattr(public_game_limiter, "max_requests", 3)
    public_game_limiter.reset()
    statuses = [_get_game(client, seed=f"ratelimit-{i}").status_code for i in range(5)]
    assert statuses.count(429) >= 2, f"expected at least 2 rate-limited responses, got {statuses}"
    public_game_limiter.reset()
    monkeypatch.setattr(public_game_limiter, "max_requests", config.PUBLIC_GAME_RATE_LIMIT_MAX)


def test_rate_limit_enforced_on_public_answer(client):
    from gateway.app import public_answer_limiter
    game = _get_game(client).json()
    orig = public_answer_limiter.max_requests
    public_answer_limiter.max_requests = 3
    public_answer_limiter.reset()
    try:
        statuses = [client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x"}).status_code for _ in range(5)]
        assert statuses.count(429) >= 2, f"expected at least 2 rate-limited responses, got {statuses}"
    finally:
        public_answer_limiter.reset()
        public_answer_limiter.max_requests = orig


# --- CORS ---------------------------------------------------------------------

def test_production_reads_origin_is_allowed_by_default(client):
    r = client.options("/v1/public/game", headers={
        "Origin": "https://reads.football",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") == "https://reads.football"


def test_untrusted_origin_not_reflected(client):
    r = client.options("/v1/public/game", headers={
        "Origin": "https://evil-scraper.example.com",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") != "https://evil-scraper.example.com"


# --- error contract never leaks internals --------------------------------------

def test_public_errors_never_contain_admin_secret(client, auth_headers):
    r = client.post("/v1/public/game/answer", json={"game_id": "GGP:0000000000000000000000", "answer": "x"})
    raw = r.text
    assert auth_headers["Authorization"].split(" ")[1] not in raw
    assert "sqlite" not in raw.lower()
    assert "/Users/" not in raw


def test_new_error_codes_registered():
    assert {"INVALID_MODE", "MODE_UNAVAILABLE", "NO_ELIGIBLE_GAME", "INVALID_GAME_ID", "GAME_EXPIRED"} <= ERROR_CODES


# --- capabilities discovery unaffected -----------------------------------------

def test_capabilities_route_unaffected_by_public_routes(client):
    r = client.get("/v1/capabilities")
    assert r.status_code == 200
    assert len(r.json()["capabilities"]) == 3  # unchanged from test_gateway.py's own baseline assertion


# --- performance (Part 23, cheap sanity check) ---------------------------------

def test_public_answer_is_fast_no_generation(client):
    game = _get_game(client).json()
    t0 = time.perf_counter()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x"})
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200
    assert elapsed < 1.0, f"answer validation took {elapsed:.2f}s -- should be a cheap package lookup, not generation"
