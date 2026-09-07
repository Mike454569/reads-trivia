"""Closeout pass (Part 1D): permanent regression coverage for a real,
confirmed-live production incident. Every one of the 34 real refresh/import
scripts called the bare `safety.create_verified_backup()` BEFORE entering
its own try/except block -- so when that call raised (concretely: production
once had /data/engine/backups root-owned while the Gateway runs as an
unprivileged user, so every backup attempt raised
sqlite3.OperationalError('unable to open database file')), the exception
escaped every failure handler in the calling script. finish_run() was never
called, so the run's refresh_runs row sat at status='RUNNING' forever --
invisible to /v1/admin/refresh/status and /v1/admin/pickem/health except via
the much slower 30-minute stale-reclaim watchdog, which is a real safety net
but was never meant to be the PRIMARY detection path for an immediate,
deterministic failure like this.

Confirmed happening AGAIN, live, during this very pass: a real cfb_games
refresh's restore-from-backup step itself hit `OSError: No space left on
device` (the live DB has grown to ~4.1GB, so live+backup+restore-tmp no
longer fits the 9.8GB volume) -- the restore call sat inside a bare
`except Exception` block with no protection of its own, so THAT exception
also escaped uncaught and left the run RUNNING for 100+ minutes until the
stale watchdog reclaimed it.

The fix (tools/data_refresh/safety.py):
- create_verified_backup_or_finish_failed(run_id) wraps the real backup
  call; ANY exception there is caught, finish_run() is called with an
  accurate FAILED_BACKUP terminal status, and BackupCreationFailure is
  raised so the caller still sees a real exception.
- safe_restore_from_backup(path) wraps the real restore call so a SECOND
  failure during recovery-from-a-failure can never itself escape uncaught;
  it returns a {"restored": False, "restore_error": ...} dict instead of
  raising, so the caller's own finish_run() call downstream always executes.

These tests use the real Engine database (skipped without READS_ENGINE_DIR,
same convention as test_admin_refresh.py) but only ever touch throwaway
refresh_runs rows -- never a real backup file -- by monkeypatching the
underlying create_verified_backup()/restore_from_backup() functions to raise
synthetic failures.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from gateway.services import admin_refresh  # noqa: E402
from tools.data_refresh import safety  # noqa: E402
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _run_row(run_id: str) -> dict:
    c = engine_bootstrap.connect()
    row = c.execute("SELECT * FROM refresh_runs WHERE run_id=?", (run_id,)).fetchone()
    c.close()
    return dict(row) if row else None


def _cleanup(run_id: str) -> None:
    c = engine_bootstrap.connect()
    c.execute("DELETE FROM refresh_runs WHERE run_id=?", (run_id,))
    c.commit()
    c.close()


@pytest.fixture
def real_run():
    """A real, freshly-started refresh_runs row -- exactly what every one of
    the 34 refresh scripts has in scope at the point they used to call the
    bare create_verified_backup(). Cleaned up unconditionally afterward so a
    failed test never leaves a synthetic row polluting the real dataset."""
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    run_id = safety.start_run(c, league="NFL", dataset="unit_test_backup_failure", source_id="TEST")
    c.close()
    yield run_id
    _cleanup(run_id)


def test_backup_exception_transitions_run_to_failed_backup_not_running(real_run, monkeypatch):
    run_id = real_run

    def boom():
        raise OSError("unable to open database file")

    monkeypatch.setattr(safety, "create_verified_backup", boom)

    with pytest.raises(safety.BackupCreationFailure):
        safety.create_verified_backup_or_finish_failed(run_id)

    row = _run_row(run_id)
    assert row["status"] == "FAILED_BACKUP", "must be a real terminal state, never left at RUNNING"
    assert row["finished_at"] is not None


def test_backup_exception_records_the_real_error(real_run, monkeypatch):
    run_id = real_run

    def boom():
        raise OSError("unable to open database file: /data/engine/backups/x.sqlite")

    monkeypatch.setattr(safety, "create_verified_backup", boom)

    with pytest.raises(safety.BackupCreationFailure):
        safety.create_verified_backup_or_finish_failed(run_id)

    row = _run_row(run_id)
    assert "unable to open database file" in row["log_json"]


def test_subsequent_refresh_can_start_immediately_after_a_backup_failure(real_run, monkeypatch):
    """The real point of this fix: no more waiting on the 30-minute stale
    watchdog. The global concurrency guard must see this run as finished
    (some FAILED status), not RUNNING, the instant the backup call fails --
    not 30+ minutes later."""
    run_id = real_run

    def boom():
        raise OSError("unable to open database file")

    monkeypatch.setattr(safety, "create_verified_backup", boom)
    with pytest.raises(safety.BackupCreationFailure):
        safety.create_verified_backup_or_finish_failed(run_id)

    result = admin_refresh.check_can_start("nfl")
    assert result["status"] == "OK", "a FAILED_BACKUP row must never block new refreshes the way RUNNING does"


def test_health_endpoint_surfaces_the_failure_immediately(real_run, monkeypatch):
    """/v1/admin/refresh/status (and by extension /v1/admin/pickem/health)
    must show the real failure right away, not a stale RUNNING row that
    looks identical to a refresh still genuinely in progress."""
    run_id = real_run

    def boom():
        raise OSError("unable to open database file")

    monkeypatch.setattr(safety, "create_verified_backup", boom)
    with pytest.raises(safety.BackupCreationFailure):
        safety.create_verified_backup_or_finish_failed(run_id)

    # This run used dataset_name="unit_test_backup_failure", which isn't one
    # of refresh_status()'s named datasets -- so read the row directly the
    # same way refresh_status()'s own _safe_run_summary would see it.
    row = _run_row(run_id)
    assert row["status"] not in ("RUNNING",)


def test_backup_creation_failure_wraps_the_original_sqlite_error(real_run, monkeypatch):
    import sqlite3

    run_id = real_run

    def boom():
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(safety, "create_verified_backup", boom)

    with pytest.raises(safety.BackupCreationFailure) as exc_info:
        safety.create_verified_backup_or_finish_failed(run_id)
    assert "unable to open database file" in str(exc_info.value)


def test_successful_backup_still_returns_the_real_backup_dict(real_run, monkeypatch):
    """The wrapper must be transparent on the success path -- same return
    shape as the bare create_verified_backup(), nothing added or hidden."""
    run_id = real_run
    fake_result = {"backup_id": "BKP:fake", "path": "/fake/path.sqlite", "sha256": "abc", "size_bytes": 1}
    monkeypatch.setattr(safety, "create_verified_backup", lambda: fake_result)

    result = safety.create_verified_backup_or_finish_failed(run_id)

    assert result == fake_result
    # The run is NOT finished by the success path -- that remains the
    # caller's own job (finish_run(status="SUCCESS", ...) after the real
    # refresh work completes), same as before this fix.
    row = _run_row(run_id)
    assert row["status"] == "RUNNING"


def test_safe_restore_from_backup_never_raises_even_if_restore_itself_fails(monkeypatch):
    """Real, confirmed-live incident during this pass: a restore-from-backup
    attempt itself hit OSError('No space left on device') because the live
    DB (~4.1GB) plus a full backup plus a restore temp file no longer fits
    the production volume. That second failure, inside the caller's own
    `except Exception:` block, used to propagate uncaught -- leaving the run
    RUNNING a second time, one step later. This must never raise."""
    def boom(path):
        raise OSError("No space left on device")

    monkeypatch.setattr(safety, "restore_from_backup", boom)

    result = safety.safe_restore_from_backup("/fake/backup/path.sqlite")

    assert result["restored"] is False
    assert "No space left on device" in result["restore_error"]


def test_safe_restore_from_backup_passes_through_a_real_success(monkeypatch):
    fake_result = {"restored_from": "/fake/path.sqlite", "sha256": "abc123"}
    monkeypatch.setattr(safety, "restore_from_backup", lambda path: fake_result)

    result = safety.safe_restore_from_backup("/fake/backup/path.sqlite")

    assert result == fake_result


def _calls_matching(tree, *, attr_owner: str, attr_name: str):
    """Real ast.Call nodes only -- never a docstring/comment string that
    happens to mention the same text, which a naive substring search would
    false-positive on (a docstring explaining the OLD bug this pass fixed
    legitimately contains the literal old call text)."""
    import ast

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (isinstance(func, ast.Attribute) and func.attr == attr_name
                and isinstance(func.value, ast.Name) and func.value.id == attr_owner):
            yield node


def _is_run_tracked(tree) -> bool:
    return any(_calls_matching(tree, attr_owner="safety", attr_name="start_run"))


def test_all_34_refresh_scripts_use_the_guarded_backup_call_not_the_bare_one():
    """Structural regression guard: a future new refresh script (or an edit
    to an existing one) that copies the OLD bare
    `backup = safety.create_verified_backup()` pattern instead of the
    guarded wrapper would silently reintroduce the exact class of bug this
    whole test file exists to close. Scoped to scripts that actually call
    safety.start_run() (real, run-tracked refreshes) -- the handful of
    one-off schema-migration scripts that call create_verified_backup()
    without ever calling start_run()/finish_run() are correctly exempt,
    since create_verified_backup_or_finish_failed(run_id) requires a real
    run_id to finish on failure and those scripts have none. Parses real
    ast.Call nodes, not a raw substring search, so a docstring that merely
    DESCRIBES the old bug (as several of these files' own historical-
    incident comments now do) is never mistaken for a live call site."""
    import ast

    data_refresh_dir = REPO_ROOT / "tools" / "data_refresh"
    violations = []
    for path in sorted(data_refresh_dir.glob("*.py")):
        if path.name == "safety.py":
            continue
        tree = ast.parse(path.read_text())
        if not _is_run_tracked(tree):
            continue  # not a run-tracked refresh script -- the guard doesn't apply
        if any(_calls_matching(tree, attr_owner="safety", attr_name="create_verified_backup")):
            violations.append(path.name)
    assert violations == [], (
        f"these run-tracked refresh scripts still call the bare, unguarded "
        f"create_verified_backup() instead of create_verified_backup_or_finish_failed(run_id): {violations}"
    )


def test_all_run_tracked_scripts_use_the_safe_restore_wrapper_too():
    import ast

    data_refresh_dir = REPO_ROOT / "tools" / "data_refresh"
    violations = []
    for path in sorted(data_refresh_dir.glob("*.py")):
        if path.name == "safety.py":
            continue
        tree = ast.parse(path.read_text())
        if not _is_run_tracked(tree):
            continue
        if any(_calls_matching(tree, attr_owner="safety", attr_name="restore_from_backup")):
            violations.append(path.name)
    assert violations == [], (
        f"these run-tracked refresh scripts still call the bare, unguarded "
        f"restore_from_backup() instead of safe_restore_from_backup(): {violations}"
    )
