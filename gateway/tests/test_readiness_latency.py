"""Readiness-latency incident fix -- targeted regression coverage.

Real production root cause: PRAGMA quick_check against the 1.65GB Engine
database measured ~166s on Fly's volume. Running that on every polled
/v1/ready request (even with the existing cache/lock, which only helps
REPEATED calls, not the cold/expired one) meant a cold or cache-expired
poll could independently take minutes -- Fly's health checker has a much
shorter budget than that, so this intermittently reported
`context deadline exceeded` and could pull the only machine out of
rotation. Fix: PRAGMA quick_check is no longer part of the polled
readiness path at all -- see tools/quiz_export/engine.py's
check_engine_readiness() / check_engine_readiness_deep() docstrings.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.quiz_export import engine  # noqa: E402

FAST_PATH_BUDGET_SECONDS = 2.0  # generous -- real measured cost is single-digit milliseconds


def _reset_readiness_cache():
    engine._READINESS_CACHE["result"] = None
    engine._READINESS_CACHE["checked_at"] = 0.0


def test_hot_path_never_runs_quick_check():
    """The actual fix, proven directly: intercept every SQL statement the
    fast path executes and assert none of them is PRAGMA quick_check."""
    _reset_readiness_cache()
    executed = []
    real_connect = engine.sqlite3.connect

    class _Recording:
        def __init__(self, conn):
            self._conn = conn

        def execute(self, sql, *a, **kw):
            executed.append(sql)
            return self._conn.execute(sql, *a, **kw)

        def close(self):
            return self._conn.close()

    def fake_connect(*a, **kw):
        return _Recording(real_connect(*a, **kw))

    engine.sqlite3.connect = fake_connect
    try:
        result = engine.check_engine_readiness()
    finally:
        engine.sqlite3.connect = real_connect

    assert result["ready"] is True
    assert not any("quick_check" in sql.lower() for sql in executed), executed


def test_deep_check_does_run_quick_check():
    """The other half of the same proof: the deep variant (startup/admin
    diagnostic only) still genuinely performs full integrity verification --
    this split removed quick_check from the hot path, it did not delete the
    capability."""
    executed = []
    real_connect = engine.sqlite3.connect

    class _Recording:
        def __init__(self, conn):
            self._conn = conn

        def execute(self, sql, *a, **kw):
            executed.append(sql)
            return self._conn.execute(sql, *a, **kw)

        def close(self):
            return self._conn.close()

    def fake_connect(*a, **kw):
        return _Recording(real_connect(*a, **kw))

    engine.sqlite3.connect = fake_connect
    try:
        result = engine.check_engine_readiness_deep()
    finally:
        engine.sqlite3.connect = real_connect

    assert result["ready"] is True
    assert result["deep_integrity_checked"] is True
    assert any("quick_check" in sql.lower() for sql in executed), executed


def test_cold_and_repeated_calls_are_fast(client):
    _reset_readiness_cache()
    t0 = time.perf_counter()
    r1 = client.get("/v1/ready")
    cold_latency = time.perf_counter() - t0
    assert r1.status_code == 200
    assert cold_latency < FAST_PATH_BUDGET_SECONDS, f"cold /v1/ready took {cold_latency:.3f}s"

    t0 = time.perf_counter()
    r2 = client.get("/v1/ready")
    warm_latency = time.perf_counter() - t0
    assert r2.status_code == 200
    assert warm_latency < FAST_PATH_BUDGET_SECONDS

    # Simulate the TTL expiring (the real "cache went stale, poll arrives
    # again" case Fly's 30s interval hits constantly) -- still fast.
    engine._READINESS_CACHE["checked_at"] = 0.0
    t0 = time.perf_counter()
    r3 = client.get("/v1/ready")
    expired_latency = time.perf_counter() - t0
    assert r3.status_code == 200
    assert expired_latency < FAST_PATH_BUDGET_SECONDS, f"cache-expired /v1/ready took {expired_latency:.3f}s"


def test_missing_db_reports_not_ready_fast_and_without_path_leakage(client, monkeypatch):
    _reset_readiness_cache()
    fake_dir = Path("/tmp/definitely-not-a-real-reads-engine-dir-xyz")
    monkeypatch.setattr(engine, "ENGINE_DIR", fake_dir)

    t0 = time.perf_counter()
    r = client.get("/v1/ready")
    latency = time.perf_counter() - t0

    assert r.status_code == 503
    assert latency < FAST_PATH_BUDGET_SECONDS
    body = r.json()
    assert body["status"] == "not_ready"
    assert body["engine_database"]["ready"] is False
    assert body["engine_database"]["reason_code"] == "DIR_MISSING"
    # Never the real filesystem path in this PUBLIC, unauthenticated body.
    raw = r.text
    assert str(fake_dir) not in raw
    assert "/Users/" not in raw
    assert "reason" not in body["engine_database"]  # only reason_code, never the detailed/path-bearing string

    _reset_readiness_cache()


def test_admin_deep_diagnostic_requires_admin(client):
    r = client.get("/v1/admin/diagnostics/db-integrity")
    assert r.status_code == 401


def test_admin_deep_diagnostic_default_returns_cached_result_without_running_a_check(client, auth_headers):
    """Reliability pass (Pass 2.6): this route's DEFAULT (no `force`)
    response is now a passive read of the background task's cached
    _deep_integrity_status -- TestClient(app) never triggers the lifespan
    background task (no `with` context manager here), so this is exactly
    the real "fresh boot, background check hasn't run yet" state: an
    honest `ready: None`/`checked_at: None`, not a fabricated pass. See
    test_admin_deep_diagnostic_force_runs_full_check for the still-real
    live-check path."""
    r = client.get("/v1/admin/diagnostics/db-integrity", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["forced"] is False
    assert body["ready"] is None
    assert body["checked_at"] is None


def test_admin_deep_diagnostic_force_runs_full_check(client, auth_headers):
    r = client.get("/v1/admin/diagnostics/db-integrity", params={"force": "true"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["forced"] is True
    assert body["ready"] is True
    assert "database_version" in body

    # The forced live check also updates the shared cache the default
    # (non-forced) path reads -- a subsequent unforced call now sees it.
    r2 = client.get("/v1/admin/diagnostics/db-integrity", headers=auth_headers)
    body2 = r2.json()
    assert body2["forced"] is False
    assert body2["ready"] is True
    assert body2["checked_at"] == body["checked_at"]
