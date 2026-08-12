"""Reads Engine Gateway -- admin-triggered NFL/CFB production data refresh.

Thin wrapper around tools/data_refresh/{nfl_refresh,cfb_refresh}.py (the
real orchestration -- backup, download, stage, publish, sanity-check,
restore-on-failure, run-tracking) -- this module adds exactly the two
things a Gateway route needs that those scripts don't have on their own:

1. A real refresh can take minutes (network download of a real CSV, a full
   backup-copy of the ~1.6GB Engine DB, staging/publish writes, a sanity
   pass). Running that synchronously inside an HTTP request risks a client
   or reverse-proxy timeout well before the work finishes -- especially the
   Netlify Scheduled Function that triggers this in production, which has
   its own execution-time budget completely separate from however long the
   refresh actually takes. So the route starts the real work as a
   background task and returns immediately; the caller polls
   /v1/admin/refresh/status for the real outcome (same "kick off, then
   poll" shape as any other long-running admin operation in this class of
   system).
2. A concurrency guard: two overlapping runs for the same league would both
   try to back up/restore the same live DB file, which is not a safe
   interleaving. refresh_runs already records a real RUNNING row for the
   duration of a run (safety.start_run/finish_run) -- this checks for one
   before starting a new run rather than trusting the caller not to
   double-trigger.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.data_refresh import cfb_refresh, nfl_refresh, safety  # noqa: E402
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

_RUNNERS = {"nfl": (nfl_refresh, "NFL", nfl_refresh.DATASET), "cfb": (cfb_refresh, "CFB", cfb_refresh.DATASET)}


def _is_running(league: str, dataset: str) -> bool:
    c = engine_bootstrap.connect()
    try:
        safety.ensure_refresh_tables(c)
        row = c.execute(
            "SELECT 1 FROM refresh_runs WHERE league=? AND dataset_name=? AND status='RUNNING' LIMIT 1",
            (league, dataset),
        ).fetchone()
        return row is not None
    finally:
        c.close()


def check_can_start(league_key: str) -> dict:
    """league_key is 'nfl' or 'cfb' (the Gateway route's own path segment,
    kept distinct from the real league label stored in refresh_runs). Pure
    status check -- does NOT start anything; the route handler schedules
    the actual background task itself (via run_fn_for) only when this
    returns status=OK, so this function never needs to hand back a raw
    callable inside a dict a caller might otherwise be tempted to
    serialize."""
    if league_key not in _RUNNERS:
        raise ValueError(f"unknown league_key: {league_key!r}")
    _, league, dataset = _RUNNERS[league_key]
    if _is_running(league, dataset):
        return {"status": "ALREADY_RUNNING", "league": league, "dataset": dataset}
    return {"status": "OK", "league": league, "dataset": dataset}


def run_fn_for(league_key: str):
    """The real, synchronous, potentially multi-minute refresh function for
    this league -- callers pass this to FastAPI's BackgroundTasks, never
    call it inline inside a request handler (see module docstring)."""
    module, _, _ = _RUNNERS[league_key]
    return module.run_nfl_refresh if league_key == "nfl" else module.run_cfb_refresh


def _safe_run_summary(run: Optional[dict]) -> Optional[dict]:
    """Never leaks a raw filesystem path (backup path, DB path) or the full
    log_json blob (which can legitimately contain an exception repr with
    internal detail) to a client -- admin-gated or not, this response can
    end up in a browser devtools panel, so the same "safe subset only"
    discipline as every other admin diagnostic route in this Gateway
    applies here too. The one exception is identity_bridge_status (NFL
    runs only) -- a short, pre-classified string (never a raw stderr
    blob), deliberately surfaced here since a silently-failing identity
    bridge is exactly the kind of thing an admin freshness view exists to
    catch (see nfl_refresh.py's own module comment on the real, disclosed
    legacy-ID-collision failure mode)."""
    if not run:
        return None
    summary = {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "rows_downloaded": run.get("rows_downloaded"),
        "rows_imported": run.get("rows_imported"),
        "rows_rejected": run.get("rows_rejected"),
        "no_op": bool(run.get("no_op")),
    }
    import json as _json
    try:
        log = _json.loads(run.get("log_json") or "{}")
    except (TypeError, ValueError):
        log = {}
    if "identity_bridge_status" in log:
        summary["identity_bridge_status"] = log["identity_bridge_status"]
    return summary


def refresh_status() -> dict:
    return {
        "nfl": _safe_run_summary(nfl_refresh.last_run_status()),
        "cfb": _safe_run_summary(cfb_refresh.last_run_status()),
    }
