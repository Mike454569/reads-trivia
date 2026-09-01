"""Backup / sanity-check / restore / run-tracking safety layer shared by the
NFL and CFB refresh orchestrators.

Nothing here is Engine-specific import logic -- it is the missing
production-safety wrapper around the EXISTING importers
(Reads_Football_Data_Engine_v4.0/backup_manager.py's own `create()` already
does a verified, integrity-checked SQLite backup; this module adds the one
thing it doesn't have -- `restore()` -- plus the before/after checks and a
run ledger that make "SOURCE -> ... -> ATOMIC PRODUCTION PROMOTION -> ...
-> BACKUP / LAST-KNOWN-GOOD PROTECTION" a real, enforced sequence rather
than a diagram).

`refresh_runs`: NOT a new table -- a real one already exists in the
production database (columns: run_id, started_at, finished_at, source_id,
dataset_name, status, rows_downloaded, rows_imported, rows_rejected,
qa_issue_count, log_json), with one real row already in it
(run_id=RUN:924da7dda4054881a609, status=BLOCKED_EXTERNAL_FETCH, dated
2026-08-07) -- clear evidence an earlier attempt at exactly this feature
existed, in an environment without real outbound network access (its own
log_json says so explicitly), and never got further than one blocked run.
No `.py` file anywhere in this repo (Engine directory or otherwise)
references this table -- it's an orphaned schema, not paired code -- so
this module adopts its exact existing shape rather than creating a second,
colliding `refresh_runs`-shaped table (the "do not create duplicate
pipelines" rule applies to schema, not just import logic). The only change
made to it is additive `ALTER TABLE ... ADD COLUMN` for the handful of
real fields that shape didn't have yet (league, backup_id, no_op) -- the
same precedented pattern `identity_bridge_v16.py` already uses on
`canonical_players`. No existing column, and no existing row, is touched
or renamed.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import backup_manager  # noqa: E402  Engine's own verified-backup helper, reused as-is, never modified

import datetime as _dt
import hashlib
import json
import shutil
import sqlite3
import uuid


def _db_path() -> Path:
    return ENGINE_DIR / "reads_football_v4.0.sqlite"


def ensure_refresh_tables(c: sqlite3.Connection) -> None:
    """Adopts the EXISTING refresh_runs table as-is (see module docstring)
    -- only adds the few real columns its original shape didn't have, via
    additive ALTER TABLE, never a competing CREATE TABLE."""
    c.execute("""
        CREATE TABLE IF NOT EXISTS refresh_runs (
            run_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            source_id TEXT,
            dataset_name TEXT,
            status TEXT NOT NULL,
            rows_downloaded INTEGER,
            rows_imported INTEGER,
            rows_rejected INTEGER,
            qa_issue_count INTEGER,
            log_json TEXT
        )
    """)
    cols = {row[1] for row in c.execute("PRAGMA table_info(refresh_runs)")}
    for name, decl in [("league", "TEXT"), ("backup_id", "TEXT"), ("no_op", "INTEGER NOT NULL DEFAULT 0")]:
        if name not in cols:
            c.execute(f"ALTER TABLE refresh_runs ADD COLUMN {name} {decl}")
    c.commit()


def new_run_id(league: str, dataset: str) -> str:
    # "RUN:" prefix matches the one real pre-existing row's own convention
    # (run_id=RUN:924da7dda4054881a609) rather than inventing a new one.
    return "RUN:" + hashlib.sha256(f"{league}|{dataset}|{uuid.uuid4().hex}".encode()).hexdigest()[:20]


def start_run(c: sqlite3.Connection, *, league: str, dataset: str, source_id: str | None) -> str:
    ensure_refresh_tables(c)
    run_id = new_run_id(league, dataset)
    c.execute(
        "INSERT INTO refresh_runs(run_id, league, dataset_name, source_id, started_at, status) VALUES (?,?,?,?,?,?)",
        (run_id, league, dataset, source_id, _dt.datetime.now(_dt.timezone.utc).isoformat(), "RUNNING"),
    )
    c.commit()
    return run_id


def finish_run(c: sqlite3.Connection, run_id: str, *, status: str, backup_id: str | None = None,
                rows_downloaded: int | None = None, rows_imported: int | None = None,
                rows_rejected: int | None = None, no_op: bool = False,
                failure_reason: str | None = None, detail: dict | None = None) -> None:
    log = dict(detail or {})
    if failure_reason:
        log["failure_reason"] = failure_reason
    # Reliability Cleanup pass: EVERY one of the 34 real refresh/import
    # scripts that call create_verified_backup() already calls this exact
    # function with backup_id=<that backup's id> on its success path (see
    # module docstring's real-incident history) -- so this single choke
    # point is where the backup's post-success cleanup belongs, rather than
    # editing 34 call sites individually. See _cleanup_backup_after_success's
    # own docstring for why only SUCCESS prunes, never a failure status.
    if status == "SUCCESS" and backup_id:
        log["backup_cleanup"] = _cleanup_backup_after_success(c, backup_id)
    c.execute(
        """UPDATE refresh_runs SET finished_at=?, status=?, backup_id=?, rows_downloaded=?, rows_imported=?,
           rows_rejected=?, no_op=?, log_json=? WHERE run_id=?""",
        (_dt.datetime.now(_dt.timezone.utc).isoformat(), status, backup_id, rows_downloaded, rows_imported,
         rows_rejected, 1 if no_op else 0, json.dumps(log, default=str), run_id),
    )
    c.commit()


def _cleanup_backup_after_success(c: sqlite3.Connection, backup_id: str) -> dict:
    """Reliability Cleanup pass: the real, confirmed-twice root cause of this
    project's Fly volume filling up. create_verified_backup() already prunes
    OLD backups before taking a new one, but nothing ever pruned the backup
    a run just took after that run actually succeeded -- it relied on some
    FUTURE run's own prune-before-create step to eventually clean up, which
    is fine for the daily scheduled refreshes but leaves a one-time script's
    backup (e.g. the NFL awards/championships Wikipedia backfill) sitting on
    the volume indefinitely. A backup is a transient safety net for the
    duration of ONE refresh call, not a permanent archive -- disaster
    recovery is Fly's own automated daily volume snapshots, a real,
    independent mechanism (see PRODUCTION_STATUS.md) -- so once a run
    reports SUCCESS, the backup it took has already served its only purpose
    and should not wait for anything else to remove it.

    Deliberately called ONLY for status == "SUCCESS" (see finish_run above),
    never for a failure: a failed run's backup is kept on purpose, even
    after restore_from_backup() has already used it to restore the live DB,
    so a human can still re-verify or manually re-restore from the exact
    file without falling back to Fly's slower snapshot-restore path.

    Defense in depth against the one mistake that would actually matter: this
    resolves the path from backup_registry (never trusts a caller-supplied
    path) and refuses to touch anything outside the backups/ directory this
    module manages, or the live DB path itself, no matter what the registry
    says.
    """
    row = c.execute("SELECT path FROM backup_registry WHERE backup_id=?", (backup_id,)).fetchone()
    if row is None:
        return {"pruned": False, "reason": "backup_id not found in backup_registry"}

    backup_path = Path(row[0]).resolve()
    live_db = _db_path().resolve()
    backups_dir = _backups_dir().resolve()
    if backup_path == live_db or backup_path.parent != backups_dir:
        # Never reached in real operation (backup_manager.create() always
        # writes into backups_dir) -- a hard refusal, not an assumption.
        return {"pruned": False, "reason": f"refused: path is not inside backups/: {backup_path}"}

    existed = backup_path.exists()
    backup_path.unlink(missing_ok=True)
    backup_path.with_name(backup_path.name + "-journal").unlink(missing_ok=True)
    c.execute("UPDATE backup_registry SET status='PRUNED_AFTER_SUCCESS' WHERE backup_id=?", (backup_id,))
    return {"pruned": True, "path": str(backup_path), "file_existed_before_prune": existed}


def _backups_dir() -> Path:
    return _db_path().parent / "backups"


def _prune_old_backups(*, keep: int = 1) -> None:
    """Real incident, fixed here: `backup_manager.create()` (vendored, never
    modified) has no retention policy of its own -- every refresh call
    creates a new ~1.6GB snapshot and NOTHING ever deletes an old one. Two
    refreshes run back-to-back (the real shape of the daily schedule, one
    dataset after another) filled the entire 5GB production volume solid
    (confirmed directly: `df -h /data` showed 100%, and the Gateway process
    itself then failed on every request with `OSError: [Errno 28] No space
    left on device` trying to write its own operational log -- a real,
    observed production outage, not a hypothetical). Backups are a
    transient safety net for the DURATION of one refresh call, not a
    permanent archive (rollback/disaster-recovery is Fly's own scheduled
    volume snapshots, a separate and already-real mechanism -- see
    READS_FINAL_LIVE_CERTIFICATION.md). Deleting everything except the
    `keep` most recent backups, called right before a new one is created,
    keeps steady-state disk usage bounded regardless of how many refreshes
    run in a day."""
    d = _backups_dir()
    if not d.is_dir():
        return
    backups = sorted(d.glob("reads_v2.1_*.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in backups[keep:]:
        stale.unlink(missing_ok=True)
        journal = stale.with_name(stale.name + "-journal")
        journal.unlink(missing_ok=True)


def create_verified_backup() -> dict:
    """Real, verified (PRAGMA integrity_check'd) snapshot via the Engine's
    own backup_manager.create() -- called BEFORE any refresh writes. Never
    reimplemented -- this is that exact function, unmodified.

    Prunes ALL existing backups first (keep=0), not just down to some
    positive count: the real production schedule runs FOUR datasets
    sequentially, one after another, the same day (the Gateway's global
    concurrency guard forces this). A backup only protects the run that
    created it -- once that run finishes (success or fail-restored),
    nothing needs yesterday's or this-morning's earlier backup anymore.
    Pruning to keep=1 *before* creating a new one still allows a brief
    window with two ~1.6GB backups plus the live DB on disk at once
    (concretely: exactly the shape of the real incident this function was
    added to fix) -- keep=0 means the disk only ever holds the live DB
    plus AT MOST one backup, from the run currently in flight.

    Reliability Cleanup pass: this was only half the fix. Pruning "before
    create" still left THIS run's own backup on disk indefinitely once the
    run succeeded, waiting for some future run to prune it before ITS own
    backup -- fine for the daily scheduled datasets, a real, confirmed
    outage risk for a one-time script with no scheduled "next run" (see
    finish_run's own docstring and PRODUCTION_STATUS.md for exactly this
    happening). finish_run() now prunes a run's backup immediately upon
    SUCCESS, so this function's "AT MOST one backup" guarantee holds
    continuously, not just until the next run happens to start."""
    _prune_old_backups(keep=0)
    return backup_manager.create()


def restore_from_backup(backup_path: str) -> dict:
    """The one real gap in backup_manager.py: it can create+verify a backup
    but has no restore. Real, careful restore: verify the backup's own
    integrity again (never trust a stale/corrupted file blindly), copy it to
    a temp file NEXT TO the live DB (same filesystem, so the final replace
    is atomic), verify the temp copy's integrity too, then atomically swap
    it into place with os.replace -- the live DB is never observed in a
    partially-written state by a concurrent reader."""
    import os

    src = Path(backup_path)
    check = backup_manager.verify(src)
    if check["integrity"] != "ok":
        raise RuntimeError(f"refusing to restore from a backup that fails its own integrity check: {check}")

    live = _db_path()
    tmp = live.with_suffix(".restoring.tmp")
    shutil.copyfile(src, tmp)
    tmp_check = backup_manager.verify(tmp)
    if tmp_check["integrity"] != "ok":
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"restore copy failed its own integrity check, aborted: {tmp_check}")
    os.replace(tmp, live)
    return {"restored_from": str(src), "sha256": tmp_check["sha256"]}


class SanityCheckFailure(RuntimeError):
    pass


def run_post_refresh_sanity_checks(c: sqlite3.Connection, *, table: str, rows_published: int,
                                    rows_rejected: int, rows_read: int,
                                    min_row_count_floor: int | None = None) -> None:
    """Real, generic guards against the failure modes explicitly called out
    for this system: impossible row-count drop, rejection-rate spike, and
    basic DB integrity -- run AFTER a refresh writes, so a bad upstream
    release is caught before anyone trusts the new data, not assumed safe
    because the import script itself didn't raise.

    Raises SanityCheckFailure (never silently continues) on any violation --
    the caller is responsible for restoring the pre-refresh backup when this
    fires."""
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SanityCheckFailure(f"PRAGMA integrity_check failed after refresh: {integrity}")

    fk_errors = c.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        raise SanityCheckFailure(f"{len(fk_errors)} foreign_key_check violation(s) after refresh")

    if rows_read > 0:
        rejection_rate = rows_rejected / rows_read
        if rejection_rate > 0.5:
            raise SanityCheckFailure(
                f"rejection rate {rejection_rate:.1%} ({rows_rejected}/{rows_read}) exceeds the 50% "
                f"safety threshold -- looks like a source format change, not ordinary row-level noise"
            )

    current_total = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if min_row_count_floor is not None and current_total < min_row_count_floor:
        raise SanityCheckFailure(
            f"{table} has {current_total} rows after refresh, below the {min_row_count_floor} floor -- "
            f"looks like an impossible data loss, not a real upstream change"
        )
