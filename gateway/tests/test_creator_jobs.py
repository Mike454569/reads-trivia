"""Phase 2 -- async Creator job system tests, unit-level (creator_jobs.py)
and Gateway-route-level (admin auth, request-shape validation).

Heavy work (a real Tier-2 100-round sweep) is NOT run inline in these tests
-- that's covered by the real, manual all-21-capability sweep this Phase's
completion report references. These tests cover what must be correct on
every commit: per-item isolation, cancellation, retry bounds, expiration,
and that the Gateway routes are genuinely admin-gated.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _cleanup_job(c, job_id: str) -> None:
    c.execute("DELETE FROM creator_job_items WHERE job_id=?", (job_id,))
    c.execute("DELETE FROM creator_jobs WHERE job_id=?", (job_id,))
    c.commit()


# --- unit: creator_jobs.py ---------------------------------------------------

def test_create_job_creates_one_item_per_capability():
    from tools.director_v02 import creator_jobs

    c = engine_bootstrap.connect()
    try:
        job_id = creator_jobs.create_job(
            c, job_type="TIER2_CERTIFICATION_SWEEP",
            capability_ids=["NFL_DRAFT__DRAFTED_BY", "CFB_HEISMAN__WON_HEISMAN"], created_by="test",
        )
        status = creator_jobs.get_job_status(c, job_id)
        assert status["status"] == "PENDING"
        assert len(status["items"]) == 2
        assert all(i["status"] == "PENDING" for i in status["items"])
    finally:
        _cleanup_job(c, job_id)
        c.close()


def test_per_item_isolation_one_failure_does_not_discard_successes(monkeypatch):
    """The real, explicit requirement: a failing item must never discard
    another item's success within the same job."""
    from tools.director_v02 import creator_jobs

    def fake_runner(c, capability_id: str):
        if capability_id == "WILL_FAIL":
            raise RuntimeError("simulated real failure")
        return True, None

    monkeypatch.setitem(creator_jobs._ITEM_RUNNERS, "TIER2_CERTIFICATION_SWEEP", fake_runner)

    c = engine_bootstrap.connect()
    try:
        job_id = creator_jobs.create_job(
            c, job_type="TIER2_CERTIFICATION_SWEEP",
            capability_ids=["WILL_SUCCEED_1", "WILL_FAIL", "WILL_SUCCEED_2"], created_by="test",
        )
        result = creator_jobs.run_job(job_id)
        assert result["status"] == "PARTIALLY_COMPLETED"
        assert result["completed"] == 2
        assert result["failed"] == 1

        status = creator_jobs.get_job_status(c, job_id)
        succeeded_ids = {i["capability_id"] for i in status["completed_concepts"]}
        failed_ids = {i["capability_id"] for i in status["failed_concepts"]}
        assert succeeded_ids == {"WILL_SUCCEED_1", "WILL_SUCCEED_2"}
        assert failed_ids == {"WILL_FAIL"}
        assert "simulated real failure" in status["failed_concepts"][0]["failure_reason"]
    finally:
        _cleanup_job(c, job_id)
        c.close()


def test_cancellation_stops_before_remaining_items_run(monkeypatch):
    """Items run in item_id order, not capability_id/insertion order (see
    run_job()'s "ORDER BY item_id" -- item_id is a random uuid), so this
    requests cancellation after whichever item runs first and asserts the
    job stops short of processing every item -- not a specific one."""
    from tools.director_v02 import creator_jobs

    processed = []

    def fake_runner(c, capability_id: str):
        processed.append(capability_id)
        if len(processed) == 1:
            c.execute("UPDATE creator_jobs SET cancel_requested=1 WHERE job_id=?", (job_id_holder["job_id"],))
            c.commit()
        return True, None

    monkeypatch.setitem(creator_jobs._ITEM_RUNNERS, "TIER2_CERTIFICATION_SWEEP", fake_runner)

    c = engine_bootstrap.connect()
    job_id_holder: dict = {}
    try:
        job_id = creator_jobs.create_job(
            c, job_type="TIER2_CERTIFICATION_SWEEP",
            capability_ids=["ITEM_1", "ITEM_2", "ITEM_3", "ITEM_4"], created_by="test",
        )
        job_id_holder["job_id"] = job_id
        result = creator_jobs.run_job(job_id)
        assert result["status"] == "CANCELLED"
        assert len(processed) < 4
    finally:
        _cleanup_job(c, job_id)
        c.close()


def test_retry_only_touches_failed_items_never_succeeded_ones(monkeypatch):
    from tools.director_v02 import creator_jobs

    attempt = {"count": 0}

    def flaky_runner(c, capability_id: str):
        if capability_id == "FLAKY" and attempt["count"] == 0:
            attempt["count"] += 1
            return False, "first attempt fails"
        return True, None

    monkeypatch.setitem(creator_jobs._ITEM_RUNNERS, "TIER2_CERTIFICATION_SWEEP", flaky_runner)

    c = engine_bootstrap.connect()
    try:
        job_id = creator_jobs.create_job(
            c, job_type="TIER2_CERTIFICATION_SWEEP", capability_ids=["STABLE", "FLAKY"], created_by="test",
        )
        first = creator_jobs.run_job(job_id)
        assert first["status"] == "PARTIALLY_COMPLETED"

        retry_result = creator_jobs.retry_failed_items(c, job_id)
        assert retry_result["ok"] is True
        assert retry_result["items_reset"] == 1

        second = creator_jobs.run_job(job_id)
        assert second["status"] == "COMPLETED"
        assert second["completed"] == 2
    finally:
        _cleanup_job(c, job_id)
        c.close()


def test_retry_bounded_by_max_retries():
    from tools.director_v02 import creator_jobs

    c = engine_bootstrap.connect()
    try:
        job_id = creator_jobs.create_job(
            c, job_type="TIER2_CERTIFICATION_SWEEP", capability_ids=["X"], created_by="test", max_retries=0,
        )
        c.execute("UPDATE creator_job_items SET status='FAILED' WHERE job_id=?", (job_id,))
        c.commit()
        result = creator_jobs.retry_failed_items(c, job_id)
        assert result["ok"] is False
        assert "max_retries" in result["reason"]
    finally:
        _cleanup_job(c, job_id)
        c.close()


def test_any_job_running_reflects_real_running_state():
    """started_at must use the same tz-aware isoformat() the module's own
    _now() produces -- SQLite's datetime('now') is space-separated with no
    timezone, and string-sorts as "less than" an isoformat() cutoff on the
    same date, which would make _reclaim_stale_running_jobs misfire and
    wrongly reclaim a job that just started."""
    from tools.director_v02 import creator_jobs

    c = engine_bootstrap.connect()
    try:
        assert creator_jobs.any_job_running(c) is False
        job_id = creator_jobs.create_job(c, job_type="TIER2_CERTIFICATION_SWEEP", capability_ids=["X"], created_by="test")
        c.execute("UPDATE creator_jobs SET status='RUNNING', started_at=? WHERE job_id=?", (creator_jobs._now(), job_id))
        c.commit()
        assert creator_jobs.any_job_running(c) is True
    finally:
        _cleanup_job(c, job_id)
        c.close()


def test_stale_running_job_is_reclaimed():
    import datetime as _dt

    from tools.director_v02 import creator_jobs

    c = engine_bootstrap.connect()
    try:
        job_id = creator_jobs.create_job(c, job_type="TIER2_CERTIFICATION_SWEEP", capability_ids=["X"], created_by="test")
        old_start = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(minutes=creator_jobs.STALE_RUNNING_THRESHOLD_MINUTES + 5)).isoformat()
        c.execute("UPDATE creator_jobs SET status='RUNNING', started_at=? WHERE job_id=?", (old_start, job_id))
        c.commit()
        assert creator_jobs.any_job_running(c) is False  # reclaimed, not blocking
        status = creator_jobs.get_job_status(c, job_id)
        assert status["status"] == "FAILED"
    finally:
        _cleanup_job(c, job_id)
        c.close()


def test_get_job_status_marks_expired_past_expiry():
    import datetime as _dt

    from tools.director_v02 import creator_jobs

    c = engine_bootstrap.connect()
    try:
        job_id = creator_jobs.create_job(
            c, job_type="TIER2_CERTIFICATION_SWEEP", capability_ids=["X"], created_by="test", expiry_hours=1,
        )
        past = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=1)).isoformat()
        c.execute("UPDATE creator_jobs SET status='COMPLETED', expires_at=? WHERE job_id=?", (past, job_id))
        c.commit()
        status = creator_jobs.get_job_status(c, job_id)
        assert status["status"] == "EXPIRED"
    finally:
        _cleanup_job(c, job_id)
        c.close()


# --- Gateway route level: admin gating + request validation -----------------

def test_creator_job_routes_require_admin(client):
    assert client.post("/v1/admin/creator-jobs/tier2-certification", json={"capability_ids": ["X"]}).status_code == 401
    assert client.get("/v1/admin/creator-jobs/CJOB:fake").status_code == 401
    assert client.post("/v1/admin/creator-jobs/CJOB:fake/cancel").status_code == 401
    assert client.post("/v1/admin/creator-jobs/CJOB:fake/retry").status_code == 401


def test_creator_job_create_rejects_empty_capability_list(client, auth_headers):
    r = client.post("/v1/admin/creator-jobs/tier2-certification", json={"capability_ids": []}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_creator_job_create_rejects_extra_fields(client, auth_headers):
    # This app maps every request-validation failure (including Pydantic's
    # extra="forbid") to 400 INVALID_REQUEST via a shared exception handler
    # -- see gateway/app.py's validation_error_handler -- never raw 422.
    r = client.post(
        "/v1/admin/creator-jobs/tier2-certification",
        json={"capability_ids": ["X"], "sql": "DROP TABLE users"}, headers=auth_headers,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_creator_job_status_unknown_job_is_a_clean_error(client, auth_headers):
    r = client.get(f"/v1/admin/creator-jobs/CJOB:{uuid.uuid4().hex}", headers=auth_headers)
    assert r.status_code == 400


def test_creator_job_full_lifecycle_through_real_http_routes(client, auth_headers, monkeypatch):
    """create -> status -> cancel/retry, driven entirely through the real
    Gateway HTTP routes (TestClient runs BackgroundTasks synchronously
    before returning -- see test_admin_refresh.py's own note on this), with
    the real 100-round Tier-2 sweep monkeypatched out so this stays a fast
    unit test rather than a slow integration run."""
    from tools.director_v02 import creator_jobs

    monkeypatch.setitem(
        creator_jobs._ITEM_RUNNERS, "TIER2_CERTIFICATION_SWEEP",
        lambda c, capability_id: (True, None),
    )

    create = client.post(
        "/v1/admin/creator-jobs/tier2-certification",
        json={"capability_ids": ["NFL_DRAFT__DRAFTED_BY"]}, headers=auth_headers,
    )
    assert create.status_code == 200
    body = create.json()
    assert body["status"] == "STARTED"
    job_id = body["job_id"]

    status = client.get(f"/v1/admin/creator-jobs/{job_id}", headers=auth_headers)
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["status"] == "COMPLETED"
    assert len(status_body["completed_concepts"]) == 1

    # Already-terminal job: cancel is a clean no-op rejection, not an error.
    cancel = client.post(f"/v1/admin/creator-jobs/{job_id}/cancel", headers=auth_headers)
    assert cancel.status_code == 200
    assert cancel.json()["ok"] is False

    retry = client.post(f"/v1/admin/creator-jobs/{job_id}/retry", headers=auth_headers)
    assert retry.status_code == 200
    assert retry.json()["ok"] is False  # nothing FAILED to retry

    c = engine_bootstrap.connect()
    try:
        _cleanup_job(c, job_id)
    finally:
        c.close()


def test_creator_job_create_returns_already_running_without_double_starting(client, auth_headers, monkeypatch):
    from tools.director_v02 import creator_jobs

    started = []

    def slow_runner(c, capability_id):
        started.append(capability_id)
        return True, None

    monkeypatch.setitem(creator_jobs._ITEM_RUNNERS, "TIER2_CERTIFICATION_SWEEP", slow_runner)
    monkeypatch.setattr(creator_jobs, "any_job_running", lambda c: True)

    r = client.post(
        "/v1/admin/creator-jobs/tier2-certification",
        json={"capability_ids": ["NFL_DRAFT__DRAFTED_BY"]}, headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json() == {"status": "ALREADY_RUNNING"}
    assert started == []
