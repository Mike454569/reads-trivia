"""Regression guard for the real, twice-confirmed production incident:
tools/data_refresh/safety.py's create_verified_backup() pruned OLD backups
before taking a new one, but nothing ever pruned the backup a run just took
after that run succeeded -- leaving a ~4GB file on the Fly volume
indefinitely (a one-time script has no "next run" to rely on for cleanup).
See PRODUCTION_STATUS.md for the full incident history.

These tests exercise the real behavior against a throwaway sqlite database
and a throwaway backups/ directory -- never the real local dev database, and
never anything on Fly -- by monkeypatching safety.ENGINE_DIR, which
safety._db_path()/_backups_dir() read at call time.
"""
from __future__ import annotations

import sqlite3

import pytest

from tools.data_refresh import safety


def _make_engine_dir(tmp_path):
    engine_dir = tmp_path / "engine"
    engine_dir.mkdir()
    (engine_dir / "backups").mkdir()
    db_path = engine_dir / "reads_football_v4.0.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE backup_registry(
            backup_id TEXT PRIMARY KEY, backup_type TEXT NOT NULL, database_version TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, path TEXT NOT NULL, sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'VERIFIED', notes TEXT
        )
    """)
    conn.commit()
    safety.ensure_refresh_tables(conn)
    return engine_dir, conn


def _register_backup(conn, engine_dir, backup_id: str, path, status: str = "VERIFIED"):
    conn.execute(
        "INSERT INTO backup_registry(backup_id, backup_type, database_version, path, sha256, size_bytes, status) "
        "VALUES (?, 'FULL', '2.1.0', ?, 'deadbeef', 123, ?)",
        (backup_id, str(path), status),
    )
    conn.commit()


@pytest.fixture
def engine(tmp_path, monkeypatch):
    engine_dir, conn = _make_engine_dir(tmp_path)
    monkeypatch.setattr(safety, "ENGINE_DIR", engine_dir)
    yield engine_dir, conn
    conn.close()


def test_cleanup_deletes_the_backup_file_and_marks_registry_pruned(engine):
    engine_dir, conn = engine
    backup_path = engine_dir / "backups" / "reads_v2.1_20260101T000000Z.sqlite"
    backup_path.write_text("fake backup contents")
    _register_backup(conn, engine_dir, "BKP:test1", backup_path)

    result = safety._cleanup_backup_after_success(conn, "BKP:test1")

    assert result["pruned"] is True
    assert not backup_path.exists(), "backup file must actually be deleted after a successful run"
    status = conn.execute("SELECT status FROM backup_registry WHERE backup_id=?", ("BKP:test1",)).fetchone()[0]
    assert status == "PRUNED_AFTER_SUCCESS", "registry must reflect the cleanup for a clear audit trail"


def test_finish_run_with_status_success_triggers_cleanup_automatically(engine):
    """The real fix is in finish_run(), the single choke point all 34 real
    refresh scripts already call on their success path -- not something
    every caller needs to opt into separately."""
    engine_dir, conn = engine
    backup_path = engine_dir / "backups" / "reads_v2.1_20260101T000000Z.sqlite"
    backup_path.write_text("fake backup contents")
    _register_backup(conn, engine_dir, "BKP:test2", backup_path)
    run_id = safety.start_run(conn, league="NFL", dataset="unit_test", source_id="TEST")

    safety.finish_run(conn, run_id, status="SUCCESS", backup_id="BKP:test2",
                       rows_downloaded=1, rows_imported=1, rows_rejected=0)

    assert not backup_path.exists()
    log_json = conn.execute("SELECT log_json FROM refresh_runs WHERE run_id=?", (run_id,)).fetchone()[0]
    assert "backup_cleanup" in log_json, "cleanup must be logged clearly in the run's own audit record"
    assert '"pruned": true' in log_json


def test_a_failed_run_keeps_its_backup_for_manual_recovery(engine):
    """Requirement: keep the backup only if the operation fails and
    recovery may be needed -- finish_run() must never prune on anything
    other than SUCCESS, even though a FAILED_RESTORED run also carries a
    real backup_id (the one restore_from_backup() already used)."""
    engine_dir, conn = engine
    backup_path = engine_dir / "backups" / "reads_v2.1_20260101T000000Z.sqlite"
    backup_path.write_text("fake backup contents")
    _register_backup(conn, engine_dir, "BKP:test3", backup_path)
    run_id = safety.start_run(conn, league="NFL", dataset="unit_test", source_id="TEST")

    safety.finish_run(conn, run_id, status="FAILED_RESTORED", backup_id="BKP:test3",
                       failure_reason="simulated failure")

    assert backup_path.exists(), "a failed run's backup must be kept, not pruned"
    status = conn.execute("SELECT status FROM backup_registry WHERE backup_id=?", ("BKP:test3",)).fetchone()[0]
    assert status == "VERIFIED", "registry status must be untouched for a kept backup"


def test_cleanup_refuses_to_touch_a_path_outside_the_backups_directory(engine):
    """Defense in depth: even if backup_registry somehow pointed outside
    backups/, cleanup must refuse rather than delete it."""
    engine_dir, conn = engine
    rogue_path = engine_dir / "not_a_real_backup.sqlite"
    rogue_path.write_text("should never be touched")
    _register_backup(conn, engine_dir, "BKP:rogue", rogue_path)

    result = safety._cleanup_backup_after_success(conn, "BKP:rogue")

    assert result["pruned"] is False
    assert rogue_path.exists(), "a path outside backups/ must never be deleted"


def test_cleanup_never_deletes_the_live_database_even_if_registry_points_at_it(engine):
    """The one mistake that would actually matter. A backup_registry row
    can never legitimately point at the live DB, but this must be an
    enforced refusal, not an assumption about what the registry contains."""
    engine_dir, conn = engine
    live_db = engine_dir / "reads_football_v4.0.sqlite"
    assert live_db.exists()
    _register_backup(conn, engine_dir, "BKP:evil", live_db)

    result = safety._cleanup_backup_after_success(conn, "BKP:evil")

    assert result["pruned"] is False
    assert live_db.exists(), "the live database must never be deleted by backup cleanup"


def test_cleanup_handles_an_unknown_backup_id_gracefully(engine):
    _engine_dir, conn = engine
    result = safety._cleanup_backup_after_success(conn, "BKP:does-not-exist")
    assert result["pruned"] is False
    assert "not found" in result["reason"]


def test_cleanup_is_idempotent_if_run_twice(engine):
    engine_dir, conn = engine
    backup_path = engine_dir / "backups" / "reads_v2.1_20260101T000000Z.sqlite"
    backup_path.write_text("fake backup contents")
    _register_backup(conn, engine_dir, "BKP:twice", backup_path)

    first = safety._cleanup_backup_after_success(conn, "BKP:twice")
    second = safety._cleanup_backup_after_success(conn, "BKP:twice")

    assert first["pruned"] is True
    assert second["pruned"] is True  # unlink(missing_ok=True) -- re-running never raises
    assert not backup_path.exists()
