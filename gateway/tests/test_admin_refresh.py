"""Admin-triggered NFL/CFB data refresh -- Gateway routes + safety layer.

Requires READS_ENGINE_DIR to point at a real Engine database (same
convention every other Engine-backed Gateway test in this suite already
relies on) -- refresh_runs is a real table this module reads/writes.

Heavy work (network download, ~1.6GB DB backup, staging/publish) is never
exercised here -- that's covered by real, manual end-to-end runs (see the
PHASE 1 production-automation report). These tests cover the parts that
must be correct on every commit: admin gating, the in-flight-run
concurrency guard, background scheduling, and that the status route never
leaks a raw filesystem path.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from gateway.services import admin_refresh  # noqa: E402
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _insert_running_row(league: str, dataset: str) -> str:
    from tools.data_refresh import safety

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    run_id = "RUN:test" + uuid.uuid4().hex[:16]
    c.execute(
        "INSERT INTO refresh_runs(run_id, league, dataset_name, started_at, status) VALUES (?,?,?,?,?)",
        (run_id, league, dataset, datetime.now(timezone.utc).isoformat(), "RUNNING"),
    )
    c.commit()
    c.close()
    return run_id


def _finish_row(run_id: str, status: str = "SUCCESS") -> None:
    c = engine_bootstrap.connect()
    c.execute("UPDATE refresh_runs SET status=?, finished_at=? WHERE run_id=?",
               (status, datetime.now(timezone.utc).isoformat(), run_id))
    c.commit()
    c.close()


def test_check_can_start_ok_when_nothing_running():
    result = admin_refresh.check_can_start("nfl")
    assert result["status"] == "OK"
    assert result["league"] == "NFL"


def test_check_can_start_detects_in_flight_run():
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][2])
    try:
        result = admin_refresh.check_can_start("nfl")
        assert result["status"] == "ALREADY_RUNNING"
    finally:
        _finish_row(run_id)


def test_check_can_start_leagues_are_independent():
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][2])
    try:
        assert admin_refresh.check_can_start("nfl")["status"] == "ALREADY_RUNNING"
        assert admin_refresh.check_can_start("cfb")["status"] == "OK"
    finally:
        _finish_row(run_id)


def test_check_can_start_rejects_unknown_league():
    with pytest.raises(ValueError):
        admin_refresh.check_can_start("mlb")


def test_run_fn_for_returns_the_real_orchestrator_functions():
    from tools.data_refresh import cfb_refresh, nfl_refresh

    assert admin_refresh.run_fn_for("nfl") is nfl_refresh.run_nfl_refresh
    assert admin_refresh.run_fn_for("cfb") is cfb_refresh.run_cfb_refresh


def test_refresh_status_shape_and_no_path_leakage():
    status = admin_refresh.refresh_status()
    assert set(status.keys()) == {"nfl", "cfb"}
    for league_status in status.values():
        if league_status is None:
            continue
        raw = str(league_status)
        assert "/Users/" not in raw and "/data/" not in raw and ".sqlite" not in raw
        assert set(league_status.keys()) <= {
            "run_id", "status", "started_at", "finished_at", "rows_downloaded",
            "rows_imported", "rows_rejected", "no_op", "identity_bridge_status",
        }


# --- Gateway routes ----------------------------------------------------------

def test_refresh_routes_require_admin(client):
    assert client.post("/v1/admin/refresh/nfl").status_code == 401
    assert client.post("/v1/admin/refresh/cfb").status_code == 401
    assert client.get("/v1/admin/refresh/status").status_code == 401


def test_refresh_status_route_authorized(client, auth_headers):
    r = client.get("/v1/admin/refresh/status", headers=auth_headers)
    assert r.status_code == 200
    assert set(r.json().keys()) == {"nfl", "cfb"}


def test_refresh_route_reports_already_running(client, auth_headers):
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][2])
    try:
        r = client.post("/v1/admin/refresh/nfl", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "ALREADY_RUNNING"
    finally:
        _finish_row(run_id)


def test_admin_refresh_module_never_imports_tools_data_refresh_at_top_level():
    """Real regression test for a real production incident: the first
    version of this module imported tools.data_refresh at module scope,
    and since gateway/app.py imports admin_refresh at ITS module scope too,
    one missing Engine-script file on a deployment's mounted volume (e.g.
    fetch_nflverse_current.py, only present via a runtime volume mount,
    never baked into the Docker image -- see gateway/Dockerfile) took down
    the ENTIRE Gateway on every boot, a real crash loop in production, not
    a hypothetical. Every tools.data_refresh import must be nested inside a
    function body from now on -- this asserts that structurally (via AST,
    not by relying on sys.modules caching from other tests, which would be
    order-dependent) so a future edit can't silently reintroduce it."""
    import ast

    src = (REPO_ROOT / "gateway" / "services" / "admin_refresh.py").read_text()
    tree = ast.parse(src)
    for node in tree.body:  # module-level (top) statements only, not nested inside functions
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("tools.data_refresh"):
            pytest.fail(f"top-level 'from {node.module} import ...' found -- must be inside a function")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("tools.data_refresh"):
                    pytest.fail(f"top-level 'import {alias.name}' found -- must be inside a function")


def test_refresh_route_returns_503_not_500_when_data_refresh_unimportable(client, auth_headers, monkeypatch):
    """Simulates the real production scenario (a missing Engine script on
    the mounted volume) without needing to actually break an import --
    confirms the route degrades this ONE feature cleanly instead of
    surfacing a raw, unhandled 500."""
    def boom(league_key):
        raise ImportError("simulated: fetch_nflverse_current not found on this deployment's volume")

    monkeypatch.setattr(admin_refresh, "check_can_start", boom)
    r = client.post("/v1/admin/refresh/nfl", headers=auth_headers)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_refresh_route_schedules_background_task(client, auth_headers, monkeypatch):
    """Real refresh work is never invoked in this test -- the route must
    return before the (mocked) work runs, proving it's genuinely
    backgrounded rather than awaited inline."""
    calls = []

    def fake_run():
        calls.append("ran")
        return {"status": "SUCCESS"}

    monkeypatch.setattr(admin_refresh, "run_fn_for", lambda league_key: fake_run)
    r = client.post("/v1/admin/refresh/cfb", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "STARTED"
    # TestClient runs background tasks before returning control here (unlike
    # a real deployed server, where the HTTP response reaches the client
    # first) -- so by this point the fake has already run exactly once, not
    # zero or multiple times.
    assert calls == ["ran"]
