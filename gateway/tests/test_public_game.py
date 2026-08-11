"""Tests for the public gameplay API (gateway/services/public_game.py,
gateway/app.py's /v1/public/* routes) -- v1.2 introduced draft_guess, v1.3
adds championship_guess through the same generalized mode registry.

Runs against the real, checksum-verified Reads_v4_Database.sqlite via the
same Director pipeline /v1/games/generate already uses -- not mocked. Every
route here is deliberately called WITHOUT auth_headers (the whole point:
these routes must work with no admin token, unlike every other route in
this Gateway)."""
import json
import time

from gateway import config
from gateway.errors import ERROR_CODES
from gateway.services import packages


def _get_game(client, **params):
    params.setdefault("mode", "draft_guess")
    return client.get("/v1/public/game", params=params)


def _get_champ_game(client, **params):
    params.setdefault("mode", "championship_guess")
    return client.get("/v1/public/game", params=params)


# --- public auth (no admin token needed) -------------------------------------

def test_public_modes_no_auth_needed(client):
    r = client.get("/v1/public/modes")
    assert r.status_code == 200
    modes_by_id = {m["mode"]: m for m in r.json()["modes"]}
    assert set(modes_by_id) == {"draft_guess", "championship_guess"}
    draft = modes_by_id["draft_guess"]
    assert draft["competition"] == "NFL"
    assert draft["title"] == "NFL Draft History: Guess the Team"
    assert draft["kind"] == "multiple_choice"
    assert draft["available"] is True
    # Part 20: only real, certified difficulties advertised -- "easy" was
    # surveyed this phase (0/232 real candidates) and must never appear.
    assert set(draft["difficulties"]) == {"medium", "hard", "any"}
    champ = modes_by_id["championship_guess"]
    assert champ["competition"] == "NFL"
    assert champ["kind"] == "multiple_choice"
    assert set(champ["difficulties"]) == {"medium", "hard", "any"}


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
    # championship_guess graduated to public in v1.3 (see below) --
    # player_from_clues is the real, registered-but-not-yet-public
    # capability left to exercise this path now.
    r = _get_game(client, mode="player_from_clues")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MODE_UNAVAILABLE"


def test_grid_and_six_degrees_are_not_public_modes(client):
    # Part 16/17: neither is migrated in v1.3 -- confirm they're not
    # accidentally reachable as a "mode" through this new surface.
    assert "grid" not in config.PUBLIC_MODE_ALLOWLIST
    assert "six_degrees" not in config.PUBLIC_MODE_ALLOWLIST
    assert config.PUBLIC_MODE_ALLOWLIST == frozenset({"draft_guess", "championship_guess"})


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


def test_public_game_rate_limit_is_shared_across_modes(client, monkeypatch):
    # Part 22: a deliberate, simple design choice -- one bucket per client
    # PER ROUTE, not per (client, mode). /v1/public/game is a single route
    # that happens to take a `mode` query param; both certified modes
    # ultimately call the same single-slot-concurrency-guarded
    # generation.generate() pipeline, so bounding combined draft+
    # championship traffic together is what actually protects that shared
    # resource. A per-mode bucket would let a client double its real
    # generation load by alternating modes -- exactly what this test
    # guards against.
    from gateway.app import public_game_limiter
    monkeypatch.setattr(public_game_limiter, "max_requests", 4)
    public_game_limiter.reset()
    statuses = []
    for i in range(6):
        mode = "draft_guess" if i % 2 == 0 else "championship_guess"
        statuses.append(_get_game(client, mode=mode, seed=f"shared-limit-{i}").status_code)
    assert statuses.count(429) >= 2, f"expected the shared bucket to rate-limit across modes, got {statuses}"
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


# --- v1.3: championship_guess, migrated through the same generalized registry --

def test_championship_game_no_auth_needed(client):
    r = _get_champ_game(client)
    assert r.status_code == 200


def test_championship_payload_never_contains_answer(client):
    r = _get_champ_game(client)
    raw = r.text
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh championship_guess response"
    body = r.json()
    assert set(body.keys()) == {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}
    assert set(body["payload"].keys()) == {"prompt", "options"}
    assert len(body["payload"]["options"]) == 4
    assert body["mode"] == "championship_guess"


def test_championship_correct_answer_accepted(client):
    game = _get_champ_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_championship_incorrect_answer_rejected(client):
    game = _get_champ_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False
    assert body["canonical_answer"] == real_answer


def test_championship_question_is_a_real_postseason_fact(client):
    # Spot-check the actual generated prompt shape, not just that SOMETHING
    # came back -- confirms the real adapter (not a stub) is wired in.
    game = _get_champ_game(client, seed="test-champ-real-fact").json()
    assert game["payload"]["prompt"].startswith("How did the ")
    assert "NFL season" in game["payload"]["prompt"]
    real_outcomes = {
        "Won the Super Bowl", "Lost the Super Bowl", "Lost in the Conference Championship",
        "Lost in the Divisional Round", "Lost in the Wild Card Round",
    }
    assert set(game["payload"]["options"]) <= real_outcomes


# --- v1.3: public mode registry ------------------------------------------------

def test_both_certified_modes_registered(client):
    modes = {m["mode"] for m in client.get("/v1/public/modes").json()["modes"]}
    assert modes == {"draft_guess", "championship_guess"}


def test_player_from_clues_remains_internal_only(client):
    r = _get_game(client, mode="player_from_clues")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MODE_UNAVAILABLE"
    assert "player_from_clues" not in {m["mode"] for m in client.get("/v1/public/modes").json()["modes"]}


# --- v1.3: certified-difficulty enforcement (Part 20/21) -----------------------

def test_draft_uncertified_easy_difficulty_rejected_immediately(client):
    r = _get_game(client, difficulty="easy")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_championship_uncertified_easy_difficulty_rejected_immediately(client):
    r = _get_champ_game(client, difficulty="easy")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_draft_certified_difficulties_actually_work(client):
    for diff in ("medium", "hard", "any"):
        r = _get_game(client, difficulty=diff, seed=f"test-draft-diff-{diff}")
        assert r.status_code == 200, f"difficulty={diff!r} should be certified and real"


def test_championship_certified_difficulties_actually_work(client):
    for diff in ("medium", "hard", "any"):
        r = _get_champ_game(client, difficulty=diff, seed=f"test-champ-diff-{diff}")
        assert r.status_code == 200, f"difficulty={diff!r} should be certified and real"


# --- v1.3: game ID / cross-mode tamper resistance (Part 7) ---------------------

def test_cross_mode_game_id_stays_scoped_to_its_own_mode(client):
    draft_game = _get_game(client, seed="test-tamper-draft").json()
    champ_game = _get_champ_game(client, seed="test-tamper-champ").json()
    assert draft_game["game_id"] != champ_game["game_id"]

    draft_stored = packages.load_package(draft_game["game_id"])
    champ_stored = packages.load_package(champ_game["game_id"])
    draft_answer = draft_stored["questions"][0]["answer"]
    champ_answer = champ_stored["questions"][0]["answer"]
    assert draft_answer != champ_answer  # a real team name vs. a real postseason outcome label

    # Submitting the DRAFT game's id with the CHAMPIONSHIP answer must be
    # judged against the draft game's own real answer, never the other
    # package's -- there is no "mode" field in the request for a client to
    # lie about (see public_game.py's validate_public_answer docstring).
    r = client.post("/v1/public/game/answer", json={"game_id": draft_game["game_id"], "answer": champ_answer})
    assert r.json()["correct"] is False
    assert r.json()["canonical_answer"] == draft_answer


# --- v1.3: contract versioning (Part 31) ----------------------------------------

def test_contract_version_present_and_stable(client):
    draft_game = _get_game(client).json()
    champ_game = _get_champ_game(client).json()
    assert draft_game["metadata"]["contract_version"] == 1
    assert champ_game["metadata"]["contract_version"] == 1


# --- v1.4: production rollout controls (Part 10/11) -----------------------

def test_master_switch_on_by_default(client):
    # Every other test in this file already implicitly proves this (they'd
    # all fail otherwise), but an explicit assertion documents the default.
    assert config.PUBLIC_GAME_ENABLED is True


def test_master_switch_off_blocks_game_fetch_safely(client, monkeypatch):
    from gateway.services import public_game
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", False)
    r = _get_game(client)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_master_switch_off_blocks_answer_validation_safely(client, monkeypatch):
    from gateway.services import public_game
    game = _get_game(client).json()  # fetch BEFORE disabling
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", False)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_master_switch_off_reflected_in_modes_list(client, monkeypatch):
    from gateway.services import public_game
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", False)
    modes = client.get("/v1/public/modes").json()["modes"]
    assert all(m["available"] is False for m in modes)
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", True)
    modes = client.get("/v1/public/modes").json()["modes"]
    assert all(m["available"] is True for m in modes)


def test_public_modes_env_var_narrows_but_cannot_expand(monkeypatch):
    monkeypatch.setenv("READS_PUBLIC_MODES", "draft_guess")
    assert config.public_modes_allowed() == frozenset({"draft_guess"})
    # Requesting a mode that isn't code-certified does NOT sneak it in.
    monkeypatch.setenv("READS_PUBLIC_MODES", "draft_guess,totally_made_up_mode")
    assert config.public_modes_allowed() == frozenset({"draft_guess"})
    monkeypatch.delenv("READS_PUBLIC_MODES", raising=False)
    assert config.public_modes_allowed() == config.PUBLIC_MODE_ALLOWLIST


def test_public_modes_env_var_temporarily_disables_one_mode(client, monkeypatch):
    monkeypatch.setenv("READS_PUBLIC_MODES", "draft_guess")
    r = _get_champ_game(client)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MODE_UNAVAILABLE"
    r2 = _get_game(client)
    assert r2.status_code == 200
    modes = client.get("/v1/public/modes").json()["modes"]
    by_id = {m["mode"]: m for m in modes}
    assert by_id["draft_guess"]["available"] is True
    assert by_id["championship_guess"]["available"] is False
    monkeypatch.delenv("READS_PUBLIC_MODES", raising=False)


# --- v1.4: readiness (Part 4/5/6) -------------------------------------------

def test_ready_route_exposes_no_filesystem_path(client):
    r = client.get("/v1/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert "db_path" not in body["engine_database"]
    assert "reason" not in body["engine_database"]
    assert body["mode_registry"]["loaded"] is True
    raw = r.text
    assert "/Users/" not in raw
    assert "nfl-trivia" not in raw


def test_health_route_is_minimal_and_safe(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"status", "service", "api_version"}


# --- v1.4: gameplay telemetry (Part 17/18) ----------------------------------

def test_answer_telemetry_correctly_identifies_mode(client, tmp_path, monkeypatch):
    # Real bug caught by actually inspecting a generated package's stored
    # `parsed_spec` (not assumed): it has no `domain` key at all (the
    # validator normalizes that away) -- an earlier version of the mode
    # lookup this test checks used `domain` and always logged `mode: None`
    # for every answer-submission telemetry event. Verified directly
    # against the real operational log file, not just that the endpoint
    # still returns 200 (which it did even with the bug, since the buggy
    # lookup never affected the client-facing response).
    from gateway import config as gw_config
    from gateway.services import public_game
    log_dir = tmp_path / "telemetry"
    monkeypatch.setattr(gw_config, "GATEWAY_AUDIT_LOG_DIR", log_dir)
    monkeypatch.setattr(gw_config, "OPERATIONAL_LOG_PATH", log_dir / "gateway_operational_log.jsonl")

    draft_game = _get_game(client, seed="telemetry-mode-draft").json()
    client.post("/v1/public/game/answer", json={"game_id": draft_game["game_id"], "answer": "x"})
    champ_game = _get_champ_game(client, seed="telemetry-mode-champ").json()
    client.post("/v1/public/game/answer", json={"game_id": champ_game["game_id"], "answer": "x"})

    lines = [json.loads(l) for l in gw_config.OPERATIONAL_LOG_PATH.read_text().splitlines() if l.strip()]
    answer_events = [l for l in lines if l.get("event") == "public_answer_submitted"]
    assert len(answer_events) == 2
    assert answer_events[0]["mode"] == "draft_guess"
    assert answer_events[1]["mode"] == "championship_guess"
    # Never the raw free-text answer (Part 17).
    assert all("answer" not in e for e in answer_events)


def test_game_served_telemetry_recorded(client, tmp_path, monkeypatch):
    from gateway import config as gw_config
    log_dir = tmp_path / "telemetry"
    monkeypatch.setattr(gw_config, "GATEWAY_AUDIT_LOG_DIR", log_dir)
    monkeypatch.setattr(gw_config, "OPERATIONAL_LOG_PATH", log_dir / "gateway_operational_log.jsonl")
    _get_game(client, seed="telemetry-served-check")
    lines = [json.loads(l) for l in gw_config.OPERATIONAL_LOG_PATH.read_text().splitlines() if l.strip()]
    served = [l for l in lines if l.get("event") == "public_game_served"]
    assert len(served) == 1
    assert served[0]["mode"] == "draft_guess"
    assert served[0]["generation_attempts"] >= 1
    assert served[0]["latency_ms"] > 0
