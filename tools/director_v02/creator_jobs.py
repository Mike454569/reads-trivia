"""Asynchronous Creator job infrastructure -- Phase 2.

Real, Phase-2-scoped use case: TIER2_CERTIFICATION_SWEEP, running the
100-round Tier-2 certification (health_probe.py) across a batch of
capabilities as isolated job items -- one failing item never discards the
others' results. Deliberately generic (job_type is just a string, item
processing is dispatched by type) so Phase 5's concept-building jobs can
reuse this exact same engine later without a rewrite; no concept-specific
code exists here (Creator Intelligence is explicitly out of Phase 2 scope).

Concurrency guard mirrors the EXISTING, already-proven pattern in
gateway/services/admin_refresh.py (`_running_row`/`_reclaim_stale_running_rows`)
rather than inventing a new one: only one creator_job may be RUNNING at a
time, and a job whose BackgroundTask died mid-flight (e.g. a `fly deploy`
killed the process, the exact real incident admin_refresh.py's own docstring
describes) is self-healingly reclaimed rather than blocking every future
job forever.
"""
from __future__ import annotations

import datetime as _dt
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

STALE_RUNNING_THRESHOLD_MINUTES = 30  # same real threshold admin_refresh.py uses, same real reasoning
DEFAULT_JOB_EXPIRY_HOURS = 72
DEFAULT_MAX_RETRIES = 1

VALID_JOB_STATUSES = frozenset({
    "PENDING", "RUNNING", "COMPLETED", "PARTIALLY_COMPLETED", "FAILED", "CANCELLED", "EXPIRED",
})
VALID_ITEM_STATUSES = frozenset({"PENDING", "RUNNING", "SUCCEEDED", "FAILED"})


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _reclaim_stale_running_jobs(c) -> None:
    cutoff = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(minutes=STALE_RUNNING_THRESHOLD_MINUTES)).isoformat()
    stale = c.execute(
        "SELECT job_id FROM creator_jobs WHERE status='RUNNING' AND started_at < ?", (cutoff,)
    ).fetchall()
    for row in stale:
        c.execute(
            "UPDATE creator_jobs SET status='FAILED', completed_at=? WHERE job_id=?",
            (_now(), row["job_id"]),
        )
        # Items still RUNNING under a reclaimed job are honestly FAILED too
        # -- never left claiming to still be in progress.
        c.execute(
            "UPDATE creator_job_items SET status='FAILED', failure_reason='job reclaimed as stale (process died mid-flight)', "
            "completed_at=? WHERE job_id=? AND status IN ('PENDING','RUNNING')",
            (_now(), row["job_id"]),
        )
    if stale:
        c.commit()


def any_job_running(c) -> bool:
    _reclaim_stale_running_jobs(c)
    row = c.execute("SELECT 1 FROM creator_jobs WHERE status='RUNNING' LIMIT 1").fetchone()
    return row is not None


def create_job(c, *, job_type: str, capability_ids: list[str], created_by: str,
                max_retries: int = DEFAULT_MAX_RETRIES, expiry_hours: int = DEFAULT_JOB_EXPIRY_HOURS) -> str:
    """Creates a job in PENDING status with one item per capability_id.
    Does NOT start execution -- see run_job() -- so creation itself is
    cheap and safe to call even when another job is currently running (the
    concurrency guard is enforced at RUN time, not creation time, matching
    admin_refresh.py's own check_can_start/run_fn_for split)."""
    job_id = "CJOB:" + uuid.uuid4().hex[:20]
    now = _now()
    expires_at = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=expiry_hours)).isoformat()
    c.execute(
        "INSERT INTO creator_jobs(job_id, job_type, requested_count, status, overall_progress, created_by, "
        "created_at, expires_at, max_retries) VALUES (?,?,?,?,?,?,?,?,?)",
        (job_id, job_type, len(capability_ids), "PENDING",
         '{"completed": 0, "failed": 0, "total": %d}' % len(capability_ids),
         created_by, now, expires_at, max_retries),
    )
    for capability_id in capability_ids:
        item_id = "CJITEM:" + uuid.uuid4().hex[:20]
        c.execute(
            "INSERT INTO creator_job_items(item_id, job_id, capability_id, status) VALUES (?,?,?,'PENDING')",
            (item_id, job_id, capability_id),
        )
    c.commit()
    return job_id


def _run_tier2_item(c, capability_id: str) -> tuple[bool, str | None]:
    from tools.director_v02 import health_probe
    from tools.director_v02 import registry

    row = c.execute("SELECT * FROM capability_catalog WHERE capability_id=?", (capability_id,)).fetchone()
    if row is None:
        return False, f"no catalog row for {capability_id!r}"
    triple = (row["mechanic"], row["domain"], row["relationship_predicate"])
    cap = registry.CAPABILITY_REGISTRY.get(triple)
    if cap is None:
        return False, f"no registry.py entry for {triple!r}"
    result = health_probe.run_tier2_certification(
        c, capability_id, row["mechanic"], row["domain"], row["relationship_predicate"], cap,
    )
    return result["passed"], result.get("failure_reason")


_ITEM_RUNNERS = {
    "TIER2_CERTIFICATION_SWEEP": _run_tier2_item,
}


def run_job(job_id: str) -> dict:
    """The real, potentially long-running work -- called via FastAPI
    BackgroundTasks by the Gateway route, never awaited inline (same real
    reasoning as admin_refresh.py's own refresh routes: a 100-round-per-
    capability sweep across many capabilities can take minutes, well past
    any reasonable request timeout).

    Per-item isolation is the real point: an exception in ONE item's
    Tier-2 run is caught right there and recorded as that item's own
    failure -- it never aborts the job or discards already-SUCCEEDED items."""
    c = engine_bootstrap.connect()
    try:
        job = c.execute("SELECT * FROM creator_jobs WHERE job_id=?", (job_id,)).fetchone()
        if job is None:
            return {"status": "FAILED", "reason": f"no such job {job_id!r}"}
        runner = _ITEM_RUNNERS.get(job["job_type"])
        if runner is None:
            c.execute("UPDATE creator_jobs SET status='FAILED', completed_at=? WHERE job_id=?", (_now(), job_id))
            c.commit()
            return {"status": "FAILED", "reason": f"unknown job_type {job['job_type']!r}"}

        c.execute("UPDATE creator_jobs SET status='RUNNING', started_at=? WHERE job_id=?", (_now(), job_id))
        c.commit()

        items = c.execute(
            "SELECT * FROM creator_job_items WHERE job_id=? AND status IN ('PENDING','FAILED') ORDER BY item_id",
            (job_id,),
        ).fetchall()

        completed = c.execute(
            "SELECT COUNT(*) FROM creator_job_items WHERE job_id=? AND status='SUCCEEDED'", (job_id,)
        ).fetchone()[0]
        failed = 0

        for item in items:
            cancel_flag = c.execute("SELECT cancel_requested FROM creator_jobs WHERE job_id=?", (job_id,)).fetchone()[0]
            if cancel_flag:
                break

            c.execute(
                "UPDATE creator_job_items SET status='RUNNING', started_at=?, attempt_count=attempt_count+1 "
                "WHERE item_id=?",
                (_now(), item["item_id"]),
            )
            c.commit()

            try:
                passed, reason = runner(c, item["capability_id"])
            except Exception as e:  # a single item's real failure -- isolated, never propagated
                passed, reason = False, f"item runner raised: {e!r}"

            if passed:
                c.execute(
                    "UPDATE creator_job_items SET status='SUCCEEDED', failure_reason=NULL, completed_at=? "
                    "WHERE item_id=?",
                    (_now(), item["item_id"]),
                )
                completed += 1
            else:
                c.execute(
                    "UPDATE creator_job_items SET status='FAILED', failure_reason=?, completed_at=? WHERE item_id=?",
                    (reason, _now(), item["item_id"]),
                )
                failed += 1
            c.execute(
                "UPDATE creator_jobs SET overall_progress=? WHERE job_id=?",
                ('{"completed": %d, "failed": %d, "total": %d}' % (completed, failed, job["requested_count"]), job_id),
            )
            c.commit()

        cancel_flag = c.execute("SELECT cancel_requested FROM creator_jobs WHERE job_id=?", (job_id,)).fetchone()[0]
        total = job["requested_count"]
        if cancel_flag:
            final_status = "CANCELLED"
        elif failed == 0:
            final_status = "COMPLETED"
        elif completed > 0:
            final_status = "PARTIALLY_COMPLETED"
        else:
            final_status = "FAILED"

        c.execute("UPDATE creator_jobs SET status=?, completed_at=? WHERE job_id=?", (final_status, _now(), job_id))
        c.commit()
        return {"status": final_status, "job_id": job_id, "completed": completed, "failed": failed, "total": total}
    finally:
        c.close()


def get_job_status(c, job_id: str) -> dict | None:
    job = c.execute("SELECT * FROM creator_jobs WHERE job_id=?", (job_id,)).fetchone()
    if job is None:
        return None
    if job["status"] in ("COMPLETED", "PARTIALLY_COMPLETED", "FAILED", "CANCELLED") and job["expires_at"]:
        if _dt.datetime.now(_dt.timezone.utc) > _dt.datetime.fromisoformat(job["expires_at"]):
            c.execute("UPDATE creator_jobs SET status='EXPIRED' WHERE job_id=?", (job_id,))
            c.commit()
            job = c.execute("SELECT * FROM creator_jobs WHERE job_id=?", (job_id,)).fetchone()
    items = c.execute(
        "SELECT item_id, capability_id, status, failure_reason, attempt_count FROM creator_job_items "
        "WHERE job_id=? ORDER BY item_id", (job_id,),
    ).fetchall()
    return {
        "job_id": job["job_id"], "job_type": job["job_type"], "status": job["status"],
        "requested_count": job["requested_count"], "overall_progress": job["overall_progress"],
        "created_at": job["created_at"], "started_at": job["started_at"], "completed_at": job["completed_at"],
        "expires_at": job["expires_at"], "retry_count": job["retry_count"],
        "items": [dict(i) for i in items],
        "completed_concepts": [dict(i) for i in items if i["status"] == "SUCCEEDED"],
        "failed_concepts": [dict(i) for i in items if i["status"] == "FAILED"],
    }


def cancel_job(c, job_id: str) -> dict:
    job = c.execute("SELECT status FROM creator_jobs WHERE job_id=?", (job_id,)).fetchone()
    if job is None:
        return {"ok": False, "reason": f"no such job {job_id!r}"}
    if job["status"] not in ("PENDING", "RUNNING"):
        return {"ok": False, "reason": f"job is already {job['status']} -- cannot cancel"}
    c.execute("UPDATE creator_jobs SET cancel_requested=1 WHERE job_id=?", (job_id,))
    c.commit()
    return {"ok": True, "job_id": job_id, "note": "cancellation requested -- a running item finishes before the job stops"}


def retry_failed_items(c, job_id: str) -> dict:
    """Retries ONLY the FAILED items -- SUCCEEDED items are never re-run or
    discarded. Bounded by max_retries (never an unbounded retry loop)."""
    job = c.execute("SELECT * FROM creator_jobs WHERE job_id=?", (job_id,)).fetchone()
    if job is None:
        return {"ok": False, "reason": f"no such job {job_id!r}"}
    if job["retry_count"] >= job["max_retries"]:
        return {"ok": False, "reason": f"max_retries ({job['max_retries']}) already exhausted"}
    if job["status"] == "RUNNING":
        return {"ok": False, "reason": "job is currently running"}

    failed_items = c.execute(
        "SELECT item_id FROM creator_job_items WHERE job_id=? AND status='FAILED'", (job_id,)
    ).fetchall()
    if not failed_items:
        return {"ok": False, "reason": "no failed items to retry"}

    c.execute(
        "UPDATE creator_job_items SET status='PENDING', failure_reason=NULL WHERE job_id=? AND status='FAILED'",
        (job_id,),
    )
    c.execute(
        "UPDATE creator_jobs SET status='PENDING', retry_count=retry_count+1, cancel_requested=0 WHERE job_id=?",
        (job_id,),
    )
    c.commit()
    return {"ok": True, "job_id": job_id, "items_reset": len(failed_items)}
