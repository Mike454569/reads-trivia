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
    c.execute(
        """UPDATE refresh_runs SET finished_at=?, status=?, backup_id=?, rows_downloaded=?, rows_imported=?,
           rows_rejected=?, no_op=?, log_json=? WHERE run_id=?""",
        (_dt.datetime.now(_dt.timezone.utc).isoformat(), status, backup_id, rows_downloaded, rows_imported,
         rows_rejected, 1 if no_op else 0, json.dumps(log, default=str), run_id),
    )
    c.commit()


def create_verified_backup() -> dict:
    """Real, verified (PRAGMA integrity_check'd) snapshot via the Engine's
    own backup_manager.create() -- called BEFORE any refresh writes. Never
    reimplemented -- this is that exact function, unmodified."""
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
