"""NFL passer rating -- Engine-gap-audit operation.

Zero new external source: every input this needs (completions, attempts,
yards, TDs, and now `pass_interceptions` -- INTs THROWN, added by the
`nfl_player_stats_refresh.py` extension alongside this module) already lives
in `player_season_stats`, itself sourced from NFLVERSE_DATA. This is a pure
derived computation over already-published, already-verified rows -- no
download, no staging, no identity resolution (the rows already exist).

Standard NFL passer rating formula (the same one Pro-Football-Reference and
the NFL itself use), each component clamped to [0, 2.375] before summing --
without the clamp, extreme single-season lines (e.g. a QB with very few
attempts and a lucky/unlucky bounce) can produce a raw rating far outside the
real 0-158.3 range the official formula is defined to produce:
    a = ((COMP/ATT) - 0.3) * 5
    b = ((YDS/ATT) - 3) * 0.25
    c = (TD/ATT) * 20
    d = 2.375 - ((INT/ATT) * 25)
    rating = ((a + b + c + d) / 6) * 100

ATT=0 rows are left with `passer_rating IS NULL` -- never computed, per the
source pack's own explicit rule ("ATT=0 => NULL"). `passer_rating_formula_version`
records which formula version produced the value, so a future correction never
has to guess whether an old row was ever (re)computed.

Verified against two well-known real seasons before trusting this formula:
Patrick Mahomes 2018 (383/580, 5097 yds, 50 TD, 12 INT) computes to 113.84,
matching the real, published 113.8 rating for that season.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR

from . import safety  # noqa: E402

LEAGUE = "NFL"
DATASET = "nfl_passer_rating"
SOURCE_ID = "NFLVERSE_DATA"  # underlying inputs' real source; this table adds no new external source
FORMULA_VERSION = "nfl-official-v1"


def _clamp(x: float) -> float:
    return max(0.0, min(2.375, x))


def compute_rating(completions: int, attempts: int, yards: int, tds: int, ints: int) -> float | None:
    if not attempts:
        return None
    a = _clamp(((completions / attempts) - 0.3) * 5)
    b = _clamp(((yards / attempts) - 3) * 0.25)
    c = _clamp((tds / attempts) * 20)
    d = _clamp(2.375 - ((ints / attempts) * 25))
    return round(((a + b + c + d) / 6) * 100, 1)


def _ensure_schema(c) -> None:
    cols = {r["name"] for r in c.execute("PRAGMA table_info(player_season_stats)").fetchall()}
    if "passer_rating" not in cols:
        c.execute("ALTER TABLE player_season_stats ADD COLUMN passer_rating REAL")
    if "passer_rating_formula_version" not in cols:
        c.execute("ALTER TABLE player_season_stats ADD COLUMN passer_rating_formula_version TEXT")
    c.commit()


def run_nfl_passer_rating_compute() -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM player_season_stats").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    computed = skipped_no_attempts = 0
    try:
        c = engine_bootstrap.connect()
        c.execute("BEGIN")
        try:
            rows = c.execute(
                "SELECT rowid, pass_completions, pass_attempts, pass_yards, pass_td, pass_interceptions "
                "FROM player_season_stats"
            ).fetchall()
            for row in rows:
                attempts = row["pass_attempts"]
                if not attempts:
                    skipped_no_attempts += 1
                    continue
                rating = compute_rating(
                    row["pass_completions"] or 0, attempts, row["pass_yards"] or 0,
                    row["pass_td"] or 0, row["pass_interceptions"] or 0,
                )
                c.execute(
                    "UPDATE player_season_stats SET passer_rating=?, passer_rating_formula_version=? WHERE rowid=?",
                    (rating, FORMULA_VERSION, row["rowid"]),
                )
                computed += 1
            c.commit()
        except Exception:
            c.rollback()
            raise

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="player_season_stats", rows_published=computed, rows_rejected=0,
                rows_read=computed + skipped_no_attempts, min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_imported=computed, failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_imported=computed, no_op=(computed == 0),
            detail={"formula_version": FORMULA_VERSION, "rows_skipped_no_attempts": skipped_no_attempts},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "rows_computed": computed,
            "rows_skipped_no_attempts": skipped_no_attempts, "backup_id": backup["backup_id"],
        }
    except Exception as e:
        # Closing the live connection before an atomic backup-restore
        # (os.replace over the live DB file) avoids a real, observed
        # cascading "database is locked" on the very next connection.
        try:
            c.close()
        except Exception:
            pass
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(
            c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
            failure_reason=repr(e), detail={"restore": restore_info},
        )
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(e), "backup": backup}
