"""Tests for the v0.7 graph/Six Degrees port (gateway/services/graph.py,
gateway/app.py's /v1/graph/search, /v1/graph/path, /v1/six-degrees routes).

Runs against the real, rebuilt, checksum-verified Reads_v4_Database.sqlite
(via graph_explorer.py) -- not mocked -- so these assertions are checked
against real search results/paths/puzzles, following the same
"real engine, no mocking" convention test_gateway.py already uses for
test_generate_draft_real_engine and friends.
"""
from gateway import config
from gateway.errors import ERROR_CODES


def test_graph_search_missing_token_unauthorized(client):
    r = client.get("/v1/graph/search", params={"query": "Mahomes"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_graph_path_missing_token_unauthorized(client):
    r = client.get("/v1/graph/path", params={
        "start_type": "nfl_player", "start_id": "PFR:MahoPa00",
        "end_type": "team", "end_id": "KC",
    })
    assert r.status_code == 401


def test_six_degrees_missing_token_unauthorized(client):
    r = client.get("/v1/six-degrees")
    assert r.status_code == 401


def test_graph_search_real_result(client, auth_headers):
    r = client.get("/v1/graph/search", params={"query": "Mahomes", "limit": 5}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "Mahomes"
    assert body["count"] >= 1
    assert any(row["display_name"] == "Patrick Mahomes" for row in body["results"])
    assert all({"node_type", "node_id", "display_name"} <= row.keys() for row in body["results"])


def test_graph_search_empty_query_rejected(client, auth_headers):
    r = client.get("/v1/graph/search", params={"query": ""}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_graph_search_limit_out_of_range_rejected(client, auth_headers):
    r = client.get("/v1/graph/search", params={"query": "Mahomes", "limit": 51}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_graph_search_no_match_returns_empty_not_error(client, auth_headers):
    r = client.get("/v1/graph/search", params={"query": "zzzznomatchzzzz"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["count"] == 0
    assert r.json()["results"] == []


def test_graph_path_real_connection_found(client, auth_headers):
    # Real node IDs pulled from a real search response (test_graph_search_real_result
    # above confirms these resolve), not guessed -- matches
    # Reads_Football_Data_Engine_v4.0/smoke_test_graph.py's own approach.
    r = client.get("/v1/graph/path", params={
        "start_type": "nfl_player", "start_id": "PFR:MahoPa00",
        "end_type": "team", "end_id": "KC",
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert body["degrees"] == len(body["path"])
    assert body["path"][0]["from_id"] == "PFR:MahoPa00"
    assert body["path"][-1]["to_id"] == "KC"


def test_graph_path_repeatable_across_calls(client, auth_headers):
    params = {"start_type": "nfl_player", "start_id": "PFR:MahoPa00", "end_type": "team", "end_id": "KC"}
    r1 = client.get("/v1/graph/path", params=params, headers=auth_headers)
    r2 = client.get("/v1/graph/path", params=params, headers=auth_headers)
    assert r1.json()["path"] == r2.json()["path"]


def test_graph_path_nonexistent_nodes_returns_not_found_not_error(client, auth_headers):
    r = client.get("/v1/graph/path", params={
        "start_type": "nonexistent_type", "start_id": "nope",
        "end_type": "nonexistent_type", "end_id": "nope2",
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is False
    assert body["path"] is None
    assert body["degrees"] is None


def test_graph_path_missing_required_param_rejected(client, auth_headers):
    r = client.get("/v1/graph/path", params={"start_type": "nfl_player", "start_id": "PFR:MahoPa00"}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_graph_path_max_depth_out_of_range_rejected(client, auth_headers):
    r = client.get("/v1/graph/path", params={
        "start_type": "nfl_player", "start_id": "PFR:MahoPa00",
        "end_type": "team", "end_id": "KC", "max_depth": 9,
    }, headers=auth_headers)
    assert r.status_code == 400


def test_six_degrees_default_seed_real_puzzle(client, auth_headers):
    r = client.get("/v1/six-degrees", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "six_degrees"
    assert "start" in body and "end" in body
    assert isinstance(body["solution_path"], list) and len(body["solution_path"]) >= 1


def test_six_degrees_deterministic_for_same_seed(client, auth_headers):
    r1 = client.get("/v1/six-degrees", params={"seed": "42"}, headers=auth_headers)
    r2 = client.get("/v1/six-degrees", params={"seed": "42"}, headers=auth_headers)
    assert r1.json() == r2.json()


def test_six_degrees_different_seeds_can_differ(client, auth_headers):
    r1 = client.get("/v1/six-degrees", params={"seed": "42"}, headers=auth_headers)
    r2 = client.get("/v1/six-degrees", params={"seed": "daily"}, headers=auth_headers)
    assert r1.json() != r2.json()


def test_six_degrees_invalid_len_bounds_rejected(client, auth_headers):
    r = client.get("/v1/six-degrees", params={"min_len": 5, "max_len": 2}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_capabilities_includes_graph_capabilities(client):
    r = client.get("/v1/capabilities")
    assert r.status_code == 200
    body = r.json()
    assert "graph_capabilities" in body
    ids = {c["id"] for c in body["graph_capabilities"]}
    assert ids == {"graph_search", "graph_path", "six_degrees"}
    for c in body["graph_capabilities"]:
        assert c["requires_admin"] is True


def test_rate_limit_enforced_on_graph_path(client, auth_headers, monkeypatch):
    from gateway.app import graph_path_limiter
    monkeypatch.setattr(graph_path_limiter, "max_requests", 3)
    graph_path_limiter.reset()

    responses = [
        client.get("/v1/graph/path", params={
            "start_type": "nfl_player", "start_id": "PFR:MahoPa00",
            "end_type": "team", "end_id": "KC",
        }, headers=auth_headers)
        for _ in range(5)
    ]
    statuses = [r.status_code for r in responses]
    assert statuses.count(429) >= 2, f"expected at least 2 rate-limited responses, got {statuses}"
    limited = [r for r in responses if r.status_code == 429][0]
    assert limited.json()["error"]["code"] == "RATE_LIMITED"

    graph_path_limiter.reset()
    monkeypatch.setattr(graph_path_limiter, "max_requests", config.GRAPH_PATH_RATE_LIMIT_MAX)


def test_graph_error_codes_are_registered():
    # Sanity check that graph.py never raises a GatewayError code that
    # isn't in the shared registry (GatewayError itself would already
    # reject that at raise time, but this makes the contract explicit).
    assert {"SERVICE_UNAVAILABLE", "INVALID_REQUEST", "INTERNAL_ERROR", "GENERATION_FAILED"} <= ERROR_CODES
