"""Tests for the v0.7 Grid roster/eligibility port (gateway/services/grid.py,
gateway/app.py's /v1/grid/* routes).

Runs against the real, rebuilt, checksum-verified Reads_v4_Database.sqlite --
not mocked. Every example here (Mahomes/KC/QB, the Adrian Peterson name
collision, the 2006-2019 roster-coverage window) is a fact independently
confirmed against the live database before being written into an assertion,
following the same real-engine convention test_gateway.py and test_graph.py
already use.
"""
import time

from gateway.errors import ERROR_CODES

MAHOMES_ID = "PFR:MahoPa00"


def _err(r):
    return r.json()["error"]["code"]


# --- auth -------------------------------------------------------------------

def test_grid_criteria_missing_token_unauthorized(client):
    r = client.get("/v1/grid/criteria")
    assert r.status_code == 401
    assert _err(r) == "UNAUTHORIZED"


def test_grid_board_missing_token_unauthorized(client):
    r = client.post("/v1/grid/board", json={"row_ids": ["team_KC"] * 3, "col_ids": ["pos_qb"] * 3})
    assert r.status_code == 401


def test_grid_intersection_missing_token_unauthorized(client):
    r = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "pos_qb"})
    assert r.status_code == 401


def test_grid_validate_missing_token_unauthorized(client):
    r = client.post("/v1/grid/validate", json={"row_id": "team_KC", "col_id": "pos_qb", "player_name": "Patrick Mahomes"})
    assert r.status_code == 401


def test_grid_player_missing_token_unauthorized(client):
    r = client.get(f"/v1/grid/player/{MAHOMES_ID}")
    assert r.status_code == 401


# --- criteria listing / coverage metadata ------------------------------------

def test_grid_criteria_real_coverage_and_split(client, auth_headers):
    r = client.get("/v1/grid/criteria", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    # v0.8: real 2020-2026 nflverse roster import extended this from 2006-2019.
    assert body["roster_coverage"] == {"min_season": 2006, "max_season": 2026}
    assert body["draft_coverage"]["min_season"] == 1980
    assert body["draft_coverage"]["max_season"] == 2024
    assert len(body["supported"]["team"]) == 32
    stat_ids = {c["id"] for c in body["supported"]["stat"]}
    assert stat_ids == {"pos_qb", "pos_rb", "pos_wr", "pos_te", "pos_dl", "pos_lb",
                         "pos_db", "pos_ol", "multi_team", "one_team", "sb_champ",
                         "draft_r1", "draft_day2plus"}
    statuses = {c["id"]: c["status"] for c in body["supported"]["stat"]}
    assert statuses["draft_r1"] == "SUPPORTED_WITH_COVERAGE_LIMIT"
    assert statuses["pos_qb"] == "SUPPORTED"
    unsupported_ids = {c["id"] for c in body["unsupported"]}
    assert unsupported_ids == {"draft_undrafted", "hof",
                                "mvp", "sb_mvp", "roty", "probowl_5plus", "probowl_10plus", "allpro_3plus"}


def test_grid_draft_round_real_match(client, auth_headers):
    # v0.8: draft_facts table (real, 1980-2024, 0 nulls on draft_round) is
    # now wired up -- Mahomes was a real 2017 first-round pick.
    r = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "draft_r1"}, headers=auth_headers)
    assert r.status_code == 200
    assert any(p["node_id"] == MAHOMES_ID for p in r.json()["players"])


def test_grid_season_2024_now_supported(client, auth_headers):
    # v0.8 real coverage extension: season=2024 was UNDERSTOOD_BUT_UNSUPPORTED
    # in v0.7 (window ended 2019); now inside the real 2006-2026 window.
    r = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "pos_qb", "season": 2024}, headers=auth_headers)
    assert r.status_code == 200
    assert any(p["node_id"] == MAHOMES_ID for p in r.json()["players"])


# --- valid intersection (real data) -----------------------------------------

def test_grid_intersection_team_position_real_match(client, auth_headers):
    r = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "pos_qb"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any(p["node_id"] == MAHOMES_ID and p["display_name"] == "Patrick Mahomes" for p in body["players"])


def test_grid_board_real_valid_9_of_9(client, auth_headers):
    r = client.post("/v1/grid/board", json={
        "row_ids": ["team_KC", "team_NE", "team_GB"],
        "col_ids": ["pos_qb", "pos_wr", "sb_champ"],
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid_count"] == 9
    assert all(cell["valid"] and cell["count"] > 0 for cell in body["cells"])


# --- invalid / rejected intersection -----------------------------------------

def test_grid_validate_rejects_player_satisfying_only_one_side(client, auth_headers):
    # Mahomes is real QB (satisfies pos_qb) but never played for NE (does not satisfy team_NE).
    r = client.post("/v1/grid/validate", json={
        "row_id": "team_NE", "col_id": "pos_qb", "player_name": "Patrick Mahomes",
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert body["satisfies_row"] is False
    assert body["satisfies_col"] is True
    assert body["reason"] == "DOES_NOT_SATISFY_BOTH_CONDITIONS"


def test_grid_validate_accepts_player_satisfying_both_sides(client, auth_headers):
    r = client.post("/v1/grid/validate", json={
        "row_id": "team_KC", "col_id": "pos_qb", "player_name": "Patrick Mahomes",
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["node_id"] == MAHOMES_ID
    assert body["points"] >= 10


# --- identity: real name collision must not produce a false positive --------

def test_grid_validate_real_name_collision_is_ambiguous_not_guessed(client, auth_headers):
    # Confirmed directly against graph_nodes: exactly 2 distinct nfl_player
    # rows are named "Adrian Peterson" (PFR:PeteAd00, PFR:PeteAd01) -- a real
    # HOF Vikings RB and a different, unrelated player. Resolving either one
    # "by name alone" would risk crediting/rejecting the wrong person.
    r = client.post("/v1/grid/validate", json={
        "row_id": "team_MIN", "col_id": "pos_rb", "player_name": "Adrian Peterson",
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert body["reason"] == "AMBIGUOUS"
    assert len(body["candidates"]) == 2
    assert {c["node_id"] for c in body["candidates"]} == {"PFR:PeteAd00", "PFR:PeteAd01"}


def test_grid_validate_unknown_player_not_found(client, auth_headers):
    r = client.post("/v1/grid/validate", json={
        "row_id": "team_KC", "col_id": "pos_qb", "player_name": "Zzz Not A Real Player Zzz",
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert body["reason"] == "NOT_FOUND"


# --- season bounds ------------------------------------------------------------

def test_grid_season_bound_excludes_player_from_other_season(client, auth_headers):
    # Mahomes' first KC/QB season is 2017 (real DRAFTED_BY/PLAYED_FOR season_start).
    # A season=2010 query must NOT include him even though the season-agnostic
    # (career) query does.
    r_2010 = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "pos_qb", "season": 2010}, headers=auth_headers)
    assert r_2010.status_code == 200
    assert not any(p["node_id"] == MAHOMES_ID for p in r_2010.json()["players"])

    r_2018 = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "pos_qb", "season": 2018}, headers=auth_headers)
    assert r_2018.status_code == 200
    assert any(p["node_id"] == MAHOMES_ID for p in r_2018.json()["players"])


def test_grid_season_bound_validate_rejects_early_season(client, auth_headers):
    r = client.post("/v1/grid/validate", json={
        "row_id": "team_KC", "col_id": "pos_qb", "player_name": "Patrick Mahomes", "season": 2010,
    }, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert body["satisfies_row"] is False


# --- historical coverage: outside the real window must not be guessed -------

def test_grid_out_of_coverage_season_is_unsupported_not_a_silent_empty(client, auth_headers):
    for season in (1999, 2027):  # v0.8 real window is 2006-2026; both still genuinely out of range
        r = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "pos_qb", "season": season}, headers=auth_headers)
        assert r.status_code == 200  # UNDERSTOOD_BUT_UNSUPPORTED is a structured 200, not a 4xx/5xx
        assert r.json()["error"]["code"] == "UNDERSTOOD_BUT_UNSUPPORTED"


def test_grid_unsupported_criterion_is_unavailable_not_guessed(client, auth_headers):
    r = client.get("/v1/grid/intersection", params={"row_id": "team_KC", "col_id": "hof"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["error"]["code"] == "UNDERSTOOD_BUT_UNSUPPORTED"
    assert "Hall of Fame" in r.json()["error"]["message"]


# --- alias handling (franchise relocation) -----------------------------------

def test_grid_franchise_alias_oakland_counts_as_las_vegas(client, auth_headers):
    # OAK's real PLAYED_FOR rows (2006-2019) must be reachable under the
    # CURRENT franchise code team_LV, matching data/grid.js's own convention
    # of tagging relocated players under the current code.
    r = client.get("/v1/grid/intersection", params={"row_id": "team_LV", "col_id": "pos_qb"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["count"] > 0


# --- validation ---------------------------------------------------------------

def test_grid_board_wrong_row_count_rejected(client, auth_headers):
    r = client.post("/v1/grid/board", json={"row_ids": ["team_KC", "team_NE"], "col_ids": ["pos_qb"] * 3}, headers=auth_headers)
    assert r.status_code == 400
    assert _err(r) == "INVALID_REQUEST"


def test_grid_validate_unknown_criterion_id_rejected(client, auth_headers):
    r = client.post("/v1/grid/validate", json={
        "row_id": "team_KC", "col_id": "not_a_real_criterion", "player_name": "Patrick Mahomes",
    }, headers=auth_headers)
    assert r.status_code == 400
    assert _err(r) == "INVALID_REQUEST"


def test_grid_validate_empty_player_name_rejected(client, auth_headers):
    r = client.post("/v1/grid/validate", json={"row_id": "team_KC", "col_id": "pos_qb", "player_name": "  "}, headers=auth_headers)
    assert r.status_code == 400


def test_grid_board_extra_field_rejected(client, auth_headers):
    r = client.post("/v1/grid/board", json={"row_ids": ["team_KC"] * 3, "col_ids": ["pos_qb"] * 3, "sql": "DROP TABLE x"}, headers=auth_headers)
    assert r.status_code == 400


# --- player metadata / not found ---------------------------------------------

def test_grid_player_real_metadata(client, auth_headers):
    r = client.get(f"/v1/grid/player/{MAHOMES_ID}", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] == "Patrick Mahomes"
    assert "KC" in body["teams"]
    assert "pos_qb" in body["position_groups"]
    assert body["drafted"] == {"team": "KC", "year": 2017}
    # v0.8: real jersey_number data (WORE_NUMBER edges) -- Mahomes wore #15.
    assert {"number": 15, "season": 2024} in body["jersey_numbers"]


def test_grid_player_unknown_node_id_is_404_not_found(client, auth_headers):
    r = client.get("/v1/grid/player/PFR:NoSuchPlayer99", headers=auth_headers)
    assert r.status_code == 404
    assert _err(r) == "NOT_FOUND"


# --- performance: indexed lookups, not full-table scans ----------------------

def test_grid_validate_is_fast_not_a_full_graph_scan(client, auth_headers):
    t0 = time.perf_counter()
    r = client.post("/v1/grid/validate", json={
        "row_id": "team_KC", "col_id": "pos_qb", "player_name": "Patrick Mahomes",
    }, headers=auth_headers)
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200
    # Generous ceiling for a TestClient round trip against 1.4M real edges --
    # a real full unindexed scan of graph_edges would be visibly slower than
    # this on every call, not just occasionally.
    assert elapsed < 2.0, f"single validate call took {elapsed:.2f}s -- investigate for an unindexed scan"


def test_grid_board_multi_team_criterion_completes_quickly(client, auth_headers):
    # multi_team/one_team pull all 28,617 real PLAYED_FOR rows once per call
    # (see grid.py's _players_matching) -- the one intentionally larger
    # query in this module. Still bounded well under a second in practice.
    t0 = time.perf_counter()
    r = client.post("/v1/grid/board", json={
        "row_ids": ["team_KC", "team_NE", "team_GB"],
        "col_ids": ["multi_team", "one_team", "pos_qb"],
    }, headers=auth_headers)
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200
    assert elapsed < 3.0, f"board build with multi_team/one_team took {elapsed:.2f}s"


# --- rate limiting -------------------------------------------------------------

def test_rate_limit_enforced_on_grid_board(client, auth_headers, monkeypatch):
    from gateway import config
    from gateway.app import grid_board_limiter
    monkeypatch.setattr(grid_board_limiter, "max_requests", 3)
    grid_board_limiter.reset()

    responses = [
        client.post("/v1/grid/board", json={
            "row_ids": ["team_KC", "team_NE", "team_GB"],
            "col_ids": ["pos_qb", "pos_wr", "sb_champ"],
        }, headers=auth_headers)
        for _ in range(5)
    ]
    statuses = [r.status_code for r in responses]
    assert statuses.count(429) >= 2, f"expected at least 2 rate-limited responses, got {statuses}"

    grid_board_limiter.reset()
    monkeypatch.setattr(grid_board_limiter, "max_requests", config.GRID_BOARD_RATE_LIMIT_MAX)


def test_capabilities_includes_grid_capabilities(client):
    r = client.get("/v1/capabilities")
    assert r.status_code == 200
    body = r.json()
    assert "grid_capabilities" in body
    ids = {c["id"] for c in body["grid_capabilities"]}
    assert ids == {"grid_criteria", "grid_board", "grid_intersection", "grid_validate", "grid_player"}
    for c in body["grid_capabilities"]:
        assert c["requires_admin"] is True


def test_not_found_error_code_is_registered():
    assert "NOT_FOUND" in ERROR_CODES
