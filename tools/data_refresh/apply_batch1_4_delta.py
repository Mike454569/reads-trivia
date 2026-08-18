"""Applies the Knowledge Expansion Batch 1-4 delta (built by
export_batch1_4_delta.py) onto a REAL production `reads_football_v4.0.sqlite`
file, additively -- never overwrites, never touches unrelated rows.

Deliberately stdlib-only (sqlite3, shutil, hashlib, json -- no project
imports) so this one file can be copied alone to wherever the production
volume is actually reachable (e.g. via `fly ssh sftp shell` / `fly ssh
console`) without needing the full repo checked out there.

Usage:
    python3 apply_batch1_4_delta.py <path-to-production.sqlite> <path-to-delta.sqlite>

What it does, in order, matching this project's existing safety.py
discipline (verified backup, integrity check before AND after, no
partial-apply -- one failure rolls the whole run back):
  1. Copies the production file to a timestamped backup path next to it
     and verifies the copy's SHA-256 against the source before proceeding
     -- refuses to continue if they don't match byte-for-byte.
  2. Runs PRAGMA integrity_check on production BEFORE touching it -- if
     production is already unhealthy, this refuses to layer new data on
     top of an unverified base.
  3. Creates each of the 12 new tables (CREATE TABLE IF NOT EXISTS, so a
     second run is a safe no-op) and copies all of its rows in from the
     delta file.
  4. Inserts the delta's filtered `relationships`/`coaches`/`cfb_coaches`/
     `sources` rows into production's real, existing versions of those
     tables using INSERT OR IGNORE keyed on each table's real primary key
     -- a row already present on production (e.g. if this is re-run) is
     silently skipped, never duplicated, and no existing production row
     in those tables is ever modified or deleted.
  5. Creates the 6 real, measured indexes on `nfl_plays`/`cfb_plays`
     (CREATE INDEX IF NOT EXISTS).
  6. Runs PRAGMA integrity_check + PRAGMA foreign_key_check on production
     AFTER, and reports a real before/after row count for every touched
     table.
  7. On ANY exception at any point, restores the pre-migration backup
     over the production file before re-raising, so production is never
     left partially migrated.
"""
from __future__ import annotations

import hashlib
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

NEW_TABLES = [
    "cfb_all_america_certified", "nfl_hof_inductees", "nfl_hof_inductee_teams",
    "nfl_all_pro_selections", "nfl_pro_bowl_selections", "nfl_coordinators",
    "cfb_coordinators", "nfl_player_background", "cfb_player_game_stats_real",
    "nfl_plays_defense_ext", "nfl_drives_real", "cfb_player_game_kicking_ext",
]

# (table, real primary/unique key columns used for INSERT OR IGNORE dedup)
FILTERED_TABLE_KEYS = {
    "relationships": None,  # no single PK column exposed in the filtered export; dedup via full-row NOT EXISTS below
    "coaches": ("coach_id",),
    "cfb_coaches": ("cfb_coach_id",),
    "sources": ("source_id",),
}

NEW_INDEXES = [
    ("idx_nfl_plays_passer", "nfl_plays", "passer_player_key"),
    ("idx_nfl_plays_receiver", "nfl_plays", "receiver_player_key"),
    ("idx_nfl_plays_rusher", "nfl_plays", "rusher_player_key"),
    ("idx_nfl_plays_touchdown", "nfl_plays", "touchdown"),
    ("idx_cfb_plays_drive", "cfb_plays", "drive_id"),
    ("idx_cfb_plays_play_type", "cfb_plays", "play_type"),
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _verified_backup(prod_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = prod_path.parent / f"{prod_path.stem}.pre_batch1_4_migration.{stamp}.sqlite"
    shutil.copy2(prod_path, backup_path)
    src_hash, backup_hash = _sha256(prod_path), _sha256(backup_path)
    if src_hash != backup_hash:
        backup_path.unlink(missing_ok=True)
        raise RuntimeError(f"Backup verification FAILED (hash mismatch) -- refusing to proceed. "
                            f"source={src_hash} backup={backup_hash}")
    return backup_path


def _integrity_check(conn: sqlite3.Connection, label: str) -> None:
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"PRAGMA integrity_check ({label}) FAILED: {result}")
    fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        raise RuntimeError(f"PRAGMA foreign_key_check ({label}) found {len(fk_errors)} violation(s): {fk_errors[:5]}")


def apply_delta(prod_db_path: str, delta_db_path: str) -> dict:
    prod_path, delta_path = Path(prod_db_path), Path(delta_db_path)
    if not prod_path.exists():
        raise FileNotFoundError(f"Production DB not found: {prod_path}")
    if not delta_path.exists():
        raise FileNotFoundError(f"Delta DB not found: {delta_path}")

    report: dict = {"backup_path": None, "before": {}, "after": {}, "indexes_created": []}

    backup_path = _verified_backup(prod_path)
    report["backup_path"] = str(backup_path)

    conn = sqlite3.connect(str(prod_path))
    try:
        _integrity_check(conn, "before")

        conn.execute(f"ATTACH DATABASE '{delta_path}' AS delta")

        for t in NEW_TABLES:
            before = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (t,)
            ).fetchone()[0]
            report["before"][t] = (
                conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] if before else 0
            )
            create_sql = conn.execute(
                "SELECT sql FROM delta.sqlite_master WHERE type='table' AND name=?", (t,)
            ).fetchone()[0]
            conn.execute(create_sql.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1))
            if t == "nfl_hof_inductee_teams":
                # Real, confirmed edge case (caught by this script's own
                # before/after idempotency test): this one table has no
                # PK/UNIQUE constraint at all, so "INSERT OR IGNORE" can't
                # dedup it -- every re-run would double it. Its real
                # natural key is (hof_id, team_order), matching exactly
                # how nfl_hof_import.py itself writes one row per ordered
                # team-history entry per inductee.
                conn.execute("""
                    INSERT INTO main.nfl_hof_inductee_teams(hof_id, team_name_raw, years_raw, team_order)
                    SELECT d.hof_id, d.team_name_raw, d.years_raw, d.team_order FROM delta.nfl_hof_inductee_teams d
                    WHERE NOT EXISTS (
                        SELECT 1 FROM main.nfl_hof_inductee_teams m
                        WHERE m.hof_id = d.hof_id AND m.team_order = d.team_order
                    )
                """)
            else:
                conn.execute(f"INSERT OR IGNORE INTO main.{t} SELECT * FROM delta.{t}")
            report["after"][t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

        for t in ("coaches", "cfb_coaches", "sources"):
            report["before"][t] = conn.execute(f"SELECT COUNT(*) FROM main.{t}").fetchone()[0]
            conn.execute(f"INSERT OR IGNORE INTO main.{t} SELECT * FROM delta.{t}")
            report["after"][t] = conn.execute(f"SELECT COUNT(*) FROM main.{t}").fetchone()[0]

        # relationships has no single-column PK exposed here -- dedup by
        # the real composite uniqueness the schema itself enforces
        # (subject_type, subject_id, predicate, object_type, object_id,
        # season_start, season_end), matching every INSERT already used
        # throughout tools/data_refresh/*.py's own ON CONFLICT clause.
        report["before"]["relationships"] = conn.execute("SELECT COUNT(*) FROM main.relationships").fetchone()[0]
        conn.execute("""
            INSERT INTO main.relationships(subject_type, subject_id, predicate, object_type, object_id,
                season_start, season_end, source_id, verification_status)
            SELECT d.subject_type, d.subject_id, d.predicate, d.object_type, d.object_id,
                d.season_start, d.season_end, d.source_id, d.verification_status
            FROM delta.relationships d
            WHERE NOT EXISTS (
                SELECT 1 FROM main.relationships m
                WHERE m.subject_type=d.subject_type AND m.subject_id=d.subject_id AND m.predicate=d.predicate
                  AND m.object_type=d.object_type AND m.object_id=d.object_id
                  AND m.season_start=d.season_start AND m.season_end=d.season_end
            )
        """)
        report["after"]["relationships"] = conn.execute("SELECT COUNT(*) FROM main.relationships").fetchone()[0]

        for name, table, col in NEW_INDEXES:
            conn.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table}({col})")
            report["indexes_created"].append(name)

        conn.commit()
        conn.execute("DETACH DATABASE delta")

        _integrity_check(conn, "after")
        conn.close()
        return {"status": "SUCCESS", **report}
    except Exception as exc:
        try:
            conn.close()
        except Exception:
            pass
        shutil.copy2(backup_path, prod_path)
        return {"status": "FAILED_RESTORED", "reason": repr(exc), **report}


if __name__ == "__main__":
    import json
    if len(sys.argv) != 3:
        print("Usage: python3 apply_batch1_4_delta.py <production.sqlite> <delta.sqlite>")
        sys.exit(1)
    result = apply_delta(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["status"] == "SUCCESS" else 1)
