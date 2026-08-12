"""Tests for the public Six Degrees adapter (v1.7, Part C) --
gateway/services/public_six_degrees.py, gateway/app.py's
/v1/public/six_degrees/* routes.

Runs against the real, checksum-verified Reads_v4_Database.sqlite (via
graph_explorer.py) -- not mocked, same "real engine, no mocking" convention
test_public_game.py and test_graph.py already use. Every route here is
called WITHOUT auth_headers -- these are public routes, same trust boundary
as /v1/public/game."""
import json

from gateway import config


def _get_game(client, **params):
    return client.get("/v1/public/six_degrees/game", params=params)


# --- public auth (no admin token needed) -------------------------------------

def test_six_degrees_game_no_auth_needed(client):
    r = _get_game(client)
    assert r.status_code == 200


def test_six_degrees_answer_no_auth_needed(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": game["game_id"], "step_index": 0, "choice_index": 0})
    assert r.status_code == 200


def test_six_degrees_reveal_no_auth_needed(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/six_degrees/reveal", json={"game_id": game["game_id"]})
    assert r.status_code == 200


# --- real content, no leakage -------------------------------------------------

def test_six_degrees_game_real_puzzle(client):
    r = _get_game(client, seed="test-seed-1")
    assert r.status_code == 200
    body = r.json()
    assert body["start"]["name"]
    assert body["end"]["name"]
    assert body["par"] >= 1
    assert body["step_index"] == 0
    assert body["completed"] is False
    assert body["current"]["name"]
    assert len(body["options"]) >= 2
    # Options are just names -- never a raw graph node id.
    assert all(isinstance(o, str) for o in body["options"])


def test_six_degrees_initial_fetch_never_reveals_the_answer(client):
    r = _get_game(client, seed="test-seed-leak-check")
    raw = json.dumps(r.json())
    assert "solution_path" not in raw
    assert "correct_id" not in raw
    assert "last_correct" not in raw  # only appears after an actual answer


def test_six_degrees_same_seed_same_puzzle(client):
    a = _get_game(client, seed="deterministic-check").json()
    b = _get_game(client, seed="deterministic-check").json()
    assert a["start"]["name"] == b["start"]["name"]
    assert a["end"]["name"] == b["end"]["name"]
    assert a["current"]["name"] == b["current"]["name"]
    assert set(a["options"]) == set(b["options"])


def test_six_degrees_content_is_nfl_only(client):
    # Coach Connections v2 rebuild: the routes this file otherwise exercises
    # (public_six_degrees.py) stay mounted for rollback safety, but are no
    # longer the mode /v1/public/modes advertises -- that's now
    # "coach_connections" (gateway/services/public_coach_connections.py),
    # still NFL-only (PUBLIC_NODE_TYPES = {nfl_player, team, coach}), still a
    # graph-connections mechanic. This isn't asserting a specific
    # team/coach/player name (that would be a brittle/content-coupled test)
    # -- just that the mode's own self-reported metadata matches reality.
    modes = {m["mode"]: m for m in client.get("/v1/public/modes").json()["modes"]}
    assert modes["coach_connections"]["competition"] == "NFL"
    assert modes["coach_connections"]["kind"] == "graph_connections"
    assert "six_degrees_guess" not in modes


# --- answer flow ---------------------------------------------------------------

def test_six_degrees_correct_answer_advances(client):
    game = _get_game(client, seed="advance-check").json()
    correct_name = None
    # Find the correct option by trying each and reading the server's own
    # verdict -- never assumed/guessed client-side (there is no way for a
    # legitimate client to know it in advance, which is the point).
    for i, _ in enumerate(game["options"]):
        r = client.post("/v1/public/six_degrees/answer",
                         json={"game_id": game["game_id"], "step_index": 0, "choice_index": i}).json()
        if r["last_correct"]:
            correct_name = r["last_correct_name"]
            break
    assert correct_name is not None, "no option was ever marked correct -- puzzle construction bug"


def test_six_degrees_wrong_answer_ends_attempt(client):
    game = _get_game(client, seed="wrong-answer-check").json()
    # Submit every option in turn; whichever one the server says is wrong
    # should immediately report completed=True (attempt over), never allow
    # a second guess at the same step.
    for i, _ in enumerate(game["options"]):
        r = client.post("/v1/public/six_degrees/answer",
                         json={"game_id": game["game_id"], "step_index": 0, "choice_index": i}).json()
        if not r["last_correct"]:
            assert r["completed"] is True
            return
    # If every single option was marked correct, options were built wrong.
    assert False, "every option was marked correct -- distractor construction bug"


def test_six_degrees_full_completion_reaches_completed_true(client):
    game = _get_game(client, seed="full-completion-check").json()
    step_index = 0
    current = game
    guard = 0
    while not current.get("completed") and guard < 10:
        guard += 1
        correct_i = None
        for i, _ in enumerate(current["options"]):
            probe = client.post("/v1/public/six_degrees/answer",
                                 json={"game_id": game["game_id"], "step_index": step_index, "choice_index": i}).json()
            if probe["last_correct"]:
                correct_i = i
                current = probe
                break
        assert correct_i is not None, f"no correct option found at step {step_index}"
        step_index += 1
    assert current["completed"] is True


def test_six_degrees_answer_step_index_out_of_range_rejected(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": game["game_id"], "step_index": 99, "choice_index": 0})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_six_degrees_answer_choice_index_out_of_range_rejected(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": game["game_id"], "step_index": 0, "choice_index": 99})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_six_degrees_unknown_game_id_rejected(client):
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": "GGP:" + "a" * 24, "step_index": 0, "choice_index": 0})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


def test_six_degrees_malformed_game_id_rejected_same_as_unknown(client):
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": "../../etc/passwd", "step_index": 0, "choice_index": 0})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


def test_six_degrees_draft_game_id_rejected_by_six_degrees_answer(client):
    # Cross-mode tampering guard: a real Draft game_id must not validate
    # against the Six Degrees answer route (different `mode` stamped on the
    # stored package).
    draft_game = client.get("/v1/public/game", params={"mode": "draft_guess"}).json()
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": draft_game["game_id"], "step_index": 0, "choice_index": 0})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


# --- reveal (give up) -----------------------------------------------------------

def test_six_degrees_reveal_shows_real_solution_names(client):
    game = _get_game(client, seed="reveal-check").json()
    r = client.post("/v1/public/six_degrees/reveal", json={"game_id": game["game_id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["solution_names"][0] == game["start"]["name"]
    assert body["solution_names"][-1] == game["end"]["name"]
    assert len(body["solution_names"]) == body["par"] + 1


def test_six_degrees_reveal_unknown_game_id_rejected(client):
    r = client.post("/v1/public/six_degrees/reveal", json={"game_id": "GGP:" + "b" * 24})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


# --- master switch (v1.7, Part C2) ----------------------------------------------

def test_six_degrees_master_switch_on_by_default(client):
    assert config.PUBLIC_SIX_DEGREES_ENABLED is True


def test_six_degrees_master_switch_off_blocks_game_fetch(client, monkeypatch):
    from gateway.services import public_six_degrees
    monkeypatch.setattr(public_six_degrees.config, "PUBLIC_SIX_DEGREES_ENABLED", False)
    r = _get_game(client)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_six_degrees_master_switch_off_blocks_answer(client, monkeypatch):
    from gateway.services import public_six_degrees
    game = _get_game(client).json()  # fetch BEFORE disabling
    monkeypatch.setattr(public_six_degrees.config, "PUBLIC_SIX_DEGREES_ENABLED", False)
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": game["game_id"], "step_index": 0, "choice_index": 0})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_six_degrees_master_switch_off_blocks_reveal(client, monkeypatch):
    from gateway.services import public_six_degrees
    game = _get_game(client).json()
    monkeypatch.setattr(public_six_degrees.config, "PUBLIC_SIX_DEGREES_ENABLED", False)
    r = client.post("/v1/public/six_degrees/reveal", json={"game_id": game["game_id"]})
    assert r.status_code == 503


# --- rate limiting ---------------------------------------------------------------

def test_six_degrees_game_rate_limit_enforced(client, monkeypatch):
    from gateway.app import public_six_degrees_game_limiter
    monkeypatch.setattr(public_six_degrees_game_limiter, "max_requests", 2)
    public_six_degrees_game_limiter.reset()
    responses = [_get_game(client, seed=f"ratelimit-{i}") for i in range(4)]
    statuses = [r.status_code for r in responses]
    assert statuses.count(429) >= 1
    public_six_degrees_game_limiter.reset()
    monkeypatch.setattr(public_six_degrees_game_limiter, "max_requests", config.PUBLIC_SIX_DEGREES_GAME_RATE_LIMIT_MAX)


# --- security regression ---------------------------------------------------------

def test_six_degrees_errors_never_contain_admin_secret(client, auth_headers):
    import os
    admin_token = os.environ.get("READS_ENGINE_ADMIN_TOKEN", "")
    r = client.post("/v1/public/six_degrees/answer",
                     json={"game_id": "GGP:" + "c" * 24, "step_index": 0, "choice_index": 0})
    raw = json.dumps(r.json())
    assert admin_token not in raw
    assert "Authorization" not in raw
