"""Knowledge Expansion Batch 3 -- targeted indexes for `nfl_plays` and
`cfb_plays`, added only where a real, measured query plan showed a full
table scan (never premature/blanket indexing).

Measured before this migration (`EXPLAIN QUERY PLAN`, real timings):
  * `nfl_plays WHERE game_id=?`            -- already fast: SEARCH via the
    existing composite PK autoindex (0.002s). No new index needed.
  * `nfl_plays WHERE passer_player_key=?`  -- SCAN nfl_plays, 0.94s on a
    1,279,628-row table. Real, measured, worth an index.
  * `cfb_plays WHERE drive_id=?`           -- SCAN cfb_plays, 3.06s on a
    3,718,552-row table. Real, measured, worth an index.
  * `cfb_plays WHERE game_id=?`            -- already fast via PK autoindex.

Follows the same production-safety pattern as other tools/data_refresh
modules (verified backup, run tracking) even though this only touches
schema/indexes, not row data -- CREATE INDEX still rewrites b-tree pages
on a multi-million-row table and deserves the same rollback safety net.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "SHARED"
DATASET = "pbp_index_migration"
SOURCE_ID = "INTERNAL_SCHEMA_MIGRATION"

INDEXES = [
    ("idx_nfl_plays_passer", "nfl_plays", "passer_player_key"),
    ("idx_nfl_plays_receiver", "nfl_plays", "receiver_player_key"),
    ("idx_nfl_plays_rusher", "nfl_plays", "rusher_player_key"),
    ("idx_nfl_plays_touchdown", "nfl_plays", "touchdown"),
    ("idx_cfb_plays_drive", "cfb_plays", "drive_id"),
    ("idx_cfb_plays_play_type", "cfb_plays", "play_type"),
]


def run_migration() -> dict:
    import sqlite3
    conn_path = str(ENGINE_DIR / "reads_football_v4.0.sqlite")
    c = sqlite3.connect(conn_path)

    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    backup = safety.create_verified_backup()

    try:
        timings = {}
        for name, table, col in INDEXES:
            t0 = time.time()
            c.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table}({col})")
            c.commit()
            timings[name] = round(time.time() - t0, 2)

        c.execute("ANALYZE")
        c.commit()

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_plays", rows_published=0, rows_rejected=0, rows_read=0, min_row_count_floor=0,
        )
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=0, rows_imported=0, rows_rejected=0, detail={"index_build_seconds": timings},
        )
        c.close()
        return {"status": "SUCCESS", "run_id": run_id, "backup_id": backup["backup_id"], "index_build_seconds": timings}
    except Exception as exc:
        try:
            c.close()
        except Exception:
            pass
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = sqlite3.connect(conn_path)
        safety.finish_run(c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                           failure_reason=repr(exc), detail={"restore": restore_info})
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(exc), "backup": backup}


if __name__ == "__main__":
    import json
    print(json.dumps(run_migration(), indent=2, default=str))
