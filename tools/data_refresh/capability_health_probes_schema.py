"""Health-probe + async-job schema -- Phase 2 migration.

Same real backup-before/verify-after/restore-on-failure discipline as
capability_catalog_schema.py (Phase 1) -- a one-time migration, not a
recurring refresh, so it is not registered in admin_refresh.py's dispatcher.

Three new tables:
  capability_health_probes  -- one row per (capability_id, tier), upserted
                                on every probe run. Tier 1 is TTL-cached by
                                callers reading `probed_at`; Tier 2 is the
                                100-round certification, always run fresh
                                (never cached -- it's the real gate for a
                                GENERATION_VERIFIED transition).
  creator_jobs               -- async job headers.
  creator_job_items           -- per-item status within a job -- one failed
                                item must never discard the others' results.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.data_refresh import safety  # noqa: E402


def _ensure_schema(c) -> None:
    # Real design fix, caught by a real failing test before this ever
    # shipped: a PRIMARY KEY of (capability_id, tier) can only ever hold the
    # LATEST probe result per capability -- which makes coverage-regression
    # detection (comparing against the PREVIOUS Tier-2 run) structurally
    # impossible, since there is nowhere for history to live. Surrogate
    # autoincrement key instead; "latest for capability X" is a real query
    # (ORDER BY probed_at DESC LIMIT 1), not a schema-enforced singleton.
    c.execute("""
        CREATE TABLE IF NOT EXISTS capability_health_probes (
            probe_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            capability_id        TEXT NOT NULL,
            tier                   TEXT NOT NULL,     -- "TIER1" | "TIER2"
            passed                  INTEGER NOT NULL,
            checks_json               TEXT NOT NULL,
            failure_reason             TEXT,
            rounds_run                   INTEGER,
            probed_at                      TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_health_probes_capability_tier_time
        ON capability_health_probes(capability_id, tier, probed_at DESC)
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS creator_jobs (
            job_id              TEXT PRIMARY KEY,
            job_type              TEXT NOT NULL,
            requested_count         INTEGER NOT NULL,
            status                   TEXT NOT NULL,
            overall_progress          TEXT,
            created_by                 TEXT,
            created_at                   TEXT NOT NULL,
            started_at                    TEXT,
            completed_at                    TEXT,
            expires_at                       TEXT,
            cancel_requested                   INTEGER NOT NULL DEFAULT 0,
            retry_count                          INTEGER NOT NULL DEFAULT 0,
            max_retries                            INTEGER NOT NULL DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS creator_job_items (
            item_id            TEXT PRIMARY KEY,
            job_id               TEXT NOT NULL REFERENCES creator_jobs(job_id),
            capability_id          TEXT NOT NULL,
            status                   TEXT NOT NULL,
            failure_reason             TEXT,
            attempt_count                 INTEGER NOT NULL DEFAULT 0,
            started_at                      TEXT,
            completed_at                      TEXT
        )
    """)
    c.commit()


def run_health_probe_schema_migration() -> dict:
    backup = safety.create_verified_backup()
    try:
        c = engine_bootstrap.connect()
        c.execute("BEGIN")
        try:
            _ensure_schema(c)
            c.commit()
        except Exception:
            c.rollback()
            raise

        integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"PRAGMA integrity_check failed after migration: {integrity}")
        fk_errors = c.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise RuntimeError(f"{len(fk_errors)} foreign_key_check violation(s) after migration")
        c.close()
        return {"status": "SUCCESS", "backup_id": backup["backup_id"]}
    except Exception as e:
        restore_info = safety.restore_from_backup(backup["path"])
        return {"status": "FAILED_RESTORED", "reason": repr(e), "backup": backup, "restore": restore_info}
