"""NFL production data refresh -- games/schedules/scores.

Real source, confirmed live and matched against the Engine's existing data
before writing any code: nflverse-data's GitHub Release tagged `schedules`
(https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv),
already `approved_for_import=1` in the `sources` table as NFLVERSE_DATA
("Primary NFL releases"). Confirmed by direct inspection (not assumed) that
this is almost certainly the ORIGINAL source of the existing `games` table:
same `game_id` convention (`1999_01_MIN_ATL`), same row count (~7,549 vs the
table's 7,548), and its columns map 1:1 onto every real column `games`
already has (a few renamed -- gameday->game_date, result->result_margin,
total->total_points, div_game->division_game, away_qb_id->away_qb_source_id,
home_qb_id->home_qb_source_id, away_coach->away_coach_name,
home_coach->home_coach_name, stadium->stadium_name -- everything else
matches exactly).

No importer for `games` existed anywhere in this repo before this module
(confirmed by grep across the whole tree for "INTO games" -- see the
UNIFIED ENGINE v4.0 audit) -- the table's existing 1999-2026 rows (including
the real 2026 schedule, scores still NULL since those games haven't been
played) were populated once by a process that no longer exists here. This
is new, real capability, not a duplicate of anything.

Unlike the per-season roster CSVs, this is ONE file covering the entire
1999-present history -- small (~2.2MB), no need to chunk by season. Every
run re-publishes the whole file via an idempotent UPSERT keyed on the
real, stable game_id -- correct both for backfilling any truly new/changed
rows (a game that just went final, a late correction) and for the common
case where nothing changed.
"""
from __future__ import annotations

import csv
import datetime as _dt
import sys
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import import_data  # noqa: E402  Engine's own generic staging helpers (col/parse_int/reject/begin_batch), reused as-is

LEAGUE = "NFL"
DATASET = "nfl_games"
SOURCE_ID = "NFLVERSE_DATA"
GAMES_URL = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"

# Real CSV header -> real games table column, confirmed by direct diff of
# both real schemas (see module docstring) -- every mapped field really
# exists on both sides, nothing invented.
_COLUMN_MAP = {
    "game_id": "game_id", "season": "season", "game_type": "game_type", "week": "week",
    "gameday": "game_date", "weekday": "weekday", "gametime": "game_time",
    "away_team": "away_team", "away_score": "away_score", "home_team": "home_team", "home_score": "home_score",
    "result": "result_margin", "total": "total_points", "overtime": "overtime",
    "away_rest": "away_rest", "home_rest": "home_rest",
    "away_moneyline": "away_moneyline", "home_moneyline": "home_moneyline",
    "spread_line": "spread_line", "total_line": "total_line", "div_game": "division_game",
    "roof": "roof", "surface": "surface", "temp": "temperature", "wind": "wind",
    "away_qb_id": "away_qb_source_id", "home_qb_id": "home_qb_source_id",
    "away_qb_name": "away_qb_name", "home_qb_name": "home_qb_name",
    "away_coach": "away_coach_name", "home_coach": "home_coach_name",
    "referee": "referee", "stadium_id": "stadium_id", "stadium": "stadium_name",
}
_INT_COLS = {"season", "away_score", "home_score", "result_margin", "total_points", "overtime",
             "away_rest", "home_rest", "division_game"}
_FLOAT_COLS = {"away_moneyline", "home_moneyline", "spread_line", "total_line", "temperature", "wind"}


def _ensure_staging_table(c) -> None:
    cols_sql = ",\n            ".join(f"{dest} TEXT" for dest in dict.fromkeys(_COLUMN_MAP.values()))
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS staging_nfl_games (
            batch_id TEXT NOT NULL REFERENCES import_batches(batch_id),
            source_row INTEGER NOT NULL,
            {cols_sql},
            PRIMARY KEY (batch_id, source_row)
        )
    """)
    c.commit()


def _stage(c, bid: str, path: Path) -> tuple[int, int, int]:
    read = staged = rejected = 0
    dest_cols = list(dict.fromkeys(_COLUMN_MAP.values()))
    placeholders = ",".join("?" for _ in dest_cols) + ",?,?"
    with open(path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            read += 1
            game_id = import_data.col(row, "game_id")
            season = import_data.col(row, "season")
            if not game_id or not season:
                import_data.reject(c, bid, i, "MISSING_GAME_KEY", "NFL game row needs game_id/season", row)
                rejected += 1
                continue
            values = [import_data.col(row, src) for src in _COLUMN_MAP]  # preserves _COLUMN_MAP's key order = dest_cols order
            c.execute(
                f"INSERT INTO staging_nfl_games({','.join(dest_cols)}, batch_id, source_row) VALUES ({placeholders})",
                (*values, bid, i),
            )
            staged += 1
    return read, staged, rejected


def _publish(c, bid: str) -> int:
    dest_cols = list(dict.fromkeys(_COLUMN_MAP.values()))
    published = 0
    for row in c.execute(f"SELECT {','.join(dest_cols)} FROM staging_nfl_games WHERE batch_id=?", (bid,)):
        rec = dict(zip(dest_cols, row))
        for k in _INT_COLS:
            rec[k] = import_data.parse_int(rec.get(k))
        for k in _FLOAT_COLS:
            v = rec.get(k)
            try:
                rec[k] = float(v) if v not in (None, "") else None
            except (TypeError, ValueError):
                rec[k] = None
        rec["source_id"] = SOURCE_ID
        cols = list(rec.keys())
        c.execute(
            f"""INSERT INTO games({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})
                ON CONFLICT(game_id) DO UPDATE SET {','.join(f"{k}=excluded.{k}" for k in cols if k != 'game_id')}""",
            [rec[k] for k in cols],
        )
        published += 1
    return published


def run_nfl_games_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_staging_table(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    try:
        import urllib.error
        import urllib.request

        path = IMPORTS_DIR / "nflverse_games.csv"
        req = urllib.request.Request(GAMES_URL, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, path)
        c.execute("BEGIN")
        try:
            read, staged, rejected = _stage(c, bid, path)
            published = _publish(c, bid)
            qa_count = c.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
            c.execute(
                "UPDATE import_batches SET finished_at=?, status='PUBLISHED', rows_read=?, rows_staged=?, "
                "rows_published=?, rows_rejected=?, qa_issue_count=? WHERE batch_id=?",
                (_dt.datetime.now(_dt.timezone.utc).isoformat(), read, staged, published, rejected, qa_count, bid),
            )
            c.commit()
        except Exception:
            c.rollback()
            c.execute("UPDATE import_batches SET finished_at=?, status='ROLLED_BACK' WHERE batch_id=?",
                       (_dt.datetime.now(_dt.timezone.utc).isoformat(), bid))
            c.commit()
            raise

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="games", rows_published=published, rows_rejected=rejected, rows_read=read,
                min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=read, rows_imported=published, rows_rejected=rejected,
                failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = published == 0 and rejected == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=read, rows_imported=published, rows_rejected=rejected, no_op=no_op,
            detail={"batch_id": bid},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "rows_downloaded": read, "rows_imported": published, "rows_rejected": rejected,
            "backup_id": backup["backup_id"],
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            c = engine_bootstrap.connect()
            safety.finish_run(c, run_id, status="SOURCE_NOT_YET_PUBLISHED", backup_id=backup["backup_id"],
                               detail={"source_url": GAMES_URL})
            c.close()
            return {"status": "SOURCE_NOT_YET_PUBLISHED", "run_id": run_id,
                    "reason": f"{GAMES_URL} returned 404"}
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                           failure_reason=repr(e), detail={"restore": restore_info})
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(e), "backup": backup}
    except Exception as e:
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(
            c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
            failure_reason=repr(e), detail={"restore": restore_info},
        )
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(e), "backup": backup}


def last_run_status() -> dict | None:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    row = c.execute(
        "SELECT * FROM refresh_runs WHERE league=? AND dataset_name=? ORDER BY started_at DESC LIMIT 1",
        (LEAGUE, DATASET),
    ).fetchone()
    c.close()
    return dict(row) if row else None
