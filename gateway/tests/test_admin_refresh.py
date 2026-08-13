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


def _insert_running_row(league: str, dataset: str, *, started_at: str | None = None) -> str:
    from tools.data_refresh import safety

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    run_id = "RUN:test" + uuid.uuid4().hex[:16]
    c.execute(
        "INSERT INTO refresh_runs(run_id, league, dataset_name, started_at, status) VALUES (?,?,?,?,?)",
        (run_id, league, dataset, started_at or datetime.now(timezone.utc).isoformat(), "RUNNING"),
    )
    c.commit()
    c.close()
    return run_id


def _run_row(run_id: str) -> dict:
    c = engine_bootstrap.connect()
    row = c.execute("SELECT * FROM refresh_runs WHERE run_id=?", (run_id,)).fetchone()
    c.close()
    return dict(row)


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
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][3])
    try:
        result = admin_refresh.check_can_start("nfl")
        assert result["status"] == "ALREADY_RUNNING"
    finally:
        _finish_row(run_id)


def test_check_can_start_is_a_global_guard_not_per_dataset():
    """Real capacity constraint, not a theoretical one: the Gateway machine
    is a single shared-CPU, 1GB-memory box, and every refresh's backup step
    copies the full ~1.6GB Engine DB -- so an in-flight NFL roster refresh
    must ALSO block starting a CFB games refresh, not just another NFL
    roster refresh. Deliberately the opposite of a per-dataset guard."""
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][3])
    try:
        assert admin_refresh.check_can_start("nfl")["status"] == "ALREADY_RUNNING"
        assert admin_refresh.check_can_start("cfb")["status"] == "ALREADY_RUNNING"
        assert admin_refresh.check_can_start("nfl_games")["status"] == "ALREADY_RUNNING"
        assert admin_refresh.check_can_start("cfb_games")["status"] == "ALREADY_RUNNING"
    finally:
        _finish_row(run_id)


def test_check_can_start_rejects_unknown_league():
    with pytest.raises(ValueError):
        admin_refresh.check_can_start("mlb")


def test_stale_running_row_is_reclaimed_and_no_longer_blocks():
    """Real regression test for a real production incident: a refresh's
    BackgroundTask runs inside the Gateway's own process, and `fly deploy`
    kills and replaces that process mid-flight as an ordinary part of a
    rolling update -- nothing ever calls finish_run() for a run killed that
    way. Confirmed happening live: a real NFL roster refresh triggered at
    01:12:38 UTC was still reporting RUNNING 10+ minutes later, right after
    a deploy. Without reclaim, that one row would silently block every
    future refresh, forever, via the global guard -- this proves it self-
    heals instead."""
    from datetime import datetime, timedelta, timezone

    old_start = (datetime.now(timezone.utc) - timedelta(minutes=admin_refresh.STALE_RUNNING_THRESHOLD_MINUTES + 5)).isoformat()
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][3], started_at=old_start)
    try:
        result = admin_refresh.check_can_start("nfl")
        assert result["status"] == "OK", "a stale RUNNING row must not block new refreshes"
        reclaimed = _run_row(run_id)
        assert reclaimed["status"] == "FAILED_STALE"
        assert reclaimed["finished_at"] is not None
    finally:
        _finish_row(run_id)  # no-op if already reclaimed, harmless either way


def test_recent_running_row_is_not_reclaimed():
    """The other half of the same guarantee -- a run that's genuinely still
    in progress (started well within the threshold) must still block, or
    the staleness fix would defeat the whole point of the concurrency
    guard."""
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][3])  # started_at=now
    try:
        result = admin_refresh.check_can_start("cfb")
        assert result["status"] == "ALREADY_RUNNING"
        assert _run_row(run_id)["status"] == "RUNNING"
    finally:
        _finish_row(run_id)


def test_run_fn_for_returns_the_real_orchestrator_functions():
    from tools.data_refresh import cfb_refresh, nfl_refresh

    assert admin_refresh.run_fn_for("nfl") is nfl_refresh.run_nfl_refresh
    assert admin_refresh.run_fn_for("cfb") is cfb_refresh.run_cfb_refresh


def test_refresh_status_shape_and_no_path_leakage():
    status = admin_refresh.refresh_status()
    assert set(status.keys()) == {"nfl", "cfb"}
    # Historical Engine Enrichment operation: nfl_draft_refresh.py and
    # nfl_player_stats_refresh.py added.
    assert set(status["nfl"].keys()) == {"rosters", "games", "draft", "player_stats", "player_game_stats", "team_game_stats"}
    assert set(status["cfb"].keys()) == {"rosters", "games"}
    for league_block in status.values():
        for run_status in league_block.values():
            if run_status is None:
                continue
            raw = str(run_status)
            assert "/Users/" not in raw and "/data/" not in raw and ".sqlite" not in raw
            assert set(run_status.keys()) <= {
                "run_id", "status", "started_at", "finished_at", "rows_downloaded",
                "rows_imported", "rows_rejected", "no_op", "identity_bridge_status",
            }


def test_all_four_datasets_are_recognized():
    for key in ("nfl", "cfb", "nfl_games", "cfb_games"):
        result = admin_refresh.check_can_start(key)
        assert result["status"] == "OK"


def test_run_fn_for_covers_games_datasets_too():
    from tools.data_refresh import cfb_games_refresh, nfl_games_refresh

    assert admin_refresh.run_fn_for("nfl_games") is nfl_games_refresh.run_nfl_games_refresh
    assert admin_refresh.run_fn_for("cfb_games") is cfb_games_refresh.run_cfb_games_refresh


# --- Gateway routes ----------------------------------------------------------

def test_refresh_routes_require_admin(client):
    assert client.post("/v1/admin/refresh/nfl").status_code == 401
    assert client.post("/v1/admin/refresh/cfb").status_code == 401
    assert client.post("/v1/admin/refresh/nfl_games").status_code == 401
    assert client.post("/v1/admin/refresh/cfb_games").status_code == 401
    assert client.get("/v1/admin/refresh/status").status_code == 401


def test_refresh_route_rejects_unknown_dataset_key(client, auth_headers):
    r = client.post("/v1/admin/refresh/mlb", headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_refresh_status_route_authorized(client, auth_headers):
    r = client.get("/v1/admin/refresh/status", headers=auth_headers)
    assert r.status_code == 200
    assert set(r.json().keys()) == {"nfl", "cfb"}


def test_refresh_route_reports_already_running(client, auth_headers):
    run_id = _insert_running_row("NFL", admin_refresh._runners()["nfl"][3])
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
    def boom(dataset_key):
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

    monkeypatch.setattr(admin_refresh, "run_fn_for", lambda dataset_key: fake_run)
    r = client.post("/v1/admin/refresh/cfb", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "STARTED"
    # TestClient runs background tasks before returning control here (unlike
    # a real deployed server, where the HTTP response reaches the client
    # first) -- so by this point the fake has already run exactly once, not
    # zero or multiple times.
    assert calls == ["ran"]


# --- backup retention (real production incident: unbounded backups filled --
# the entire 5GB Fly volume solid, taking the Gateway down with
# "OSError: No space left on device") ------------------------------------

def test_prune_old_backups_deletes_everything_but_the_newest(tmp_path, monkeypatch):
    from tools.data_refresh import safety

    fake_db = tmp_path / "reads_football_v4.0.sqlite"
    fake_db.write_bytes(b"not a real db, just a path anchor")
    monkeypatch.setattr(safety, "_db_path", lambda: fake_db)

    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    import os
    import time
    paths = []
    for i in range(4):
        p = backups_dir / f"reads_v2.1_2026081{i}T000000Z.sqlite"
        p.write_bytes(b"x" * 100)
        os.utime(p, (time.time() + i, time.time() + i))  # distinct, increasing mtimes
        paths.append(p)
    # A stray leftover journal from an interrupted run -- must be cleaned
    # up alongside its backup, never left orphaned.
    journal = backups_dir / (paths[0].name + "-journal")
    journal.write_bytes(b"j")

    safety._prune_old_backups(keep=1)

    remaining = sorted(backups_dir.iterdir())
    assert remaining == [paths[-1]]  # only the most-recently-modified backup survives


def test_prune_old_backups_keep_zero_deletes_all(tmp_path, monkeypatch):
    from tools.data_refresh import safety

    fake_db = tmp_path / "reads_football_v4.0.sqlite"
    fake_db.write_bytes(b"anchor")
    monkeypatch.setattr(safety, "_db_path", lambda: fake_db)

    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    (backups_dir / "reads_v2.1_20260812T000000Z.sqlite").write_bytes(b"x")

    # keep=0 is what create_verified_backup() actually calls with -- the
    # real production schedule runs all four datasets sequentially the
    # same day, so a backup only needs to survive its OWN run, never a
    # later one's.
    safety._prune_old_backups(keep=0)

    assert list(backups_dir.iterdir()) == []


def test_prune_old_backups_missing_dir_is_a_no_op(tmp_path, monkeypatch):
    from tools.data_refresh import safety

    fake_db = tmp_path / "reads_football_v4.0.sqlite"
    fake_db.write_bytes(b"anchor")
    monkeypatch.setattr(safety, "_db_path", lambda: fake_db)
    # backups/ deliberately never created -- must not raise.
    safety._prune_old_backups(keep=1)
