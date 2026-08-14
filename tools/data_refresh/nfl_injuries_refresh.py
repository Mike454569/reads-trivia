"""NFL weekly injury reports -- Engine-gap-audit operation.

Real source, confirmed live before writing any code: nflverse-data's GitHub
Release tagged `injuries`
(https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv),
one real file per season 2009-present -- already `approved_for_import=1` in
the `sources` table as NFLVERSE_DATA.

Identity: the source file carries a real `gsis_id` directly (e.g.
`00-0039521`) -- the exact same id already on `canonical_players.gsis_id`,
resolved the same way `nfl_player_stats_refresh.py` already does (no new/
parallel key scheme). Team: the source's `team` column is already a
standard 2-3 letter code (e.g. `ARI`) -- matched directly against
`team_aliases.team_code` for the report's own season, never guessed.

Real key found before building: `(season, week, gsis_id, game_type)` is
NOT quite unique -- 2 real collisions out of 6,264 rows in the 2024 file
alone, both confirmed to be the SAME injury report revised later the same
week (e.g. Cade Stover, week 15 2024: `Questionable` at 03:34 UTC, revised
to `Out` at 14:17 UTC the same day). The source's own `date_modified`
timestamp resolves this honestly -- this importer keeps the row with the
LATEST `date_modified` for a given key (the most current status as of that
report), never an arbitrary pick between two real, different snapshots.

This table intentionally keeps ONE row per (season, week, gsis_id,
game_type) -- the final, most-current status for that report week -- not
every historical revision. `report_status`/`practice_status` describe two
DIFFERENT real things (the official Wed/Thu/Fri game-status designation vs.
that day's practice participation) and are kept as separate columns, never
collapsed into one.
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
import import_data  # noqa: E402

LEAGUE = "NFL"
DATASET = "nfl_injuries"
SOURCE_ID = "NFLVERSE_DATA"
INJURIES_URL_TMPL = "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"
MIN_SEASON = 2009
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year + 1


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_player_injuries (
            season INTEGER NOT NULL,
            week INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            player_key TEXT NOT NULL,
            team_code TEXT,
            position TEXT,
            report_primary_injury TEXT,
            report_secondary_injury TEXT,
            report_status TEXT,
            practice_primary_injury TEXT,
            practice_secondary_injury TEXT,
            practice_status TEXT,
            date_modified TEXT,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id),
            PRIMARY KEY (season, week, game_type, player_key)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS staging_nfl_injuries (
            batch_id TEXT NOT NULL REFERENCES import_batches(batch_id),
            source_row INTEGER NOT NULL,
            season TEXT, week TEXT, game_type TEXT, gsis_id TEXT, team TEXT, position TEXT,
            report_primary_injury TEXT, report_secondary_injury TEXT, report_status TEXT,
            practice_primary_injury TEXT, practice_secondary_injury TEXT, practice_status TEXT,
            date_modified TEXT,
            PRIMARY KEY (batch_id, source_row)
        )
    """)
    c.commit()


def _stage_one_season(c, bid: str, season: int, path: Path) -> tuple[int, int, int]:
    read = staged = rejected = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for local_i, row in enumerate(csv.DictReader(f), start=2):
            i = season * 100000 + local_i
            read += 1
            gsis_id = import_data.col(row, "gsis_id")
            week = import_data.col(row, "week")
            if not gsis_id or not week:
                import_data.reject(c, bid, i, "MISSING_KEY_FIELD", "injury row needs gsis_id + week", row)
                rejected += 1
                continue
            c.execute(
                "INSERT INTO staging_nfl_injuries(season, week, game_type, gsis_id, team, position, "
                "report_primary_injury, report_secondary_injury, report_status, practice_primary_injury, "
                "practice_secondary_injury, practice_status, date_modified, batch_id, source_row) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (str(season), week, import_data.col(row, "game_type"), gsis_id, import_data.col(row, "team"),
                 import_data.col(row, "position"), import_data.col(row, "report_primary_injury"),
                 import_data.col(row, "report_secondary_injury"), import_data.col(row, "report_status"),
                 import_data.col(row, "practice_primary_injury"), import_data.col(row, "practice_secondary_injury"),
                 import_data.col(row, "practice_status"), import_data.col(row, "date_modified"), bid, i),
            )
            staged += 1
    return read, staged, rejected


def _publish(c, bid: str) -> tuple[int, int]:
    canon = {r["gsis_id"]: r["player_id"] for r in
             c.execute("SELECT gsis_id, player_id FROM canonical_players WHERE gsis_id IS NOT NULL").fetchall()}
    valid_team_codes = {r[0] for r in c.execute("SELECT DISTINCT team_code FROM team_aliases").fetchall()}

    # Real per-key latest-revision resolution -- see module docstring. Group
    # in Python (not SQL) so the "keep latest date_modified" rule is explicit
    # and testable, not buried in an ON CONFLICT clause.
    best: dict[tuple, dict] = {}
    for row in c.execute(
        "SELECT season, week, game_type, gsis_id, team, position, report_primary_injury, "
        "report_secondary_injury, report_status, practice_primary_injury, practice_secondary_injury, "
        "practice_status, date_modified FROM staging_nfl_injuries WHERE batch_id=?", (bid,)
    ):
        gsis_id = row["gsis_id"]
        player_key = canon.get(gsis_id)
        if not player_key:
            continue
        key = (row["season"], row["week"], row["game_type"], player_key)
        existing = best.get(key)
        if existing is None or (row["date_modified"] or "") > (existing["date_modified"] or ""):
            best[key] = dict(row, player_key=player_key)

    total_staged_resolved = sum(
        1 for row in c.execute(
            "SELECT gsis_id FROM staging_nfl_injuries WHERE batch_id=?", (bid,)
        ).fetchall() if row["gsis_id"] in canon
    )

    published = 0
    for row in best.values():
        team_code = row["team"] if row["team"] in valid_team_codes else None
        rec = {
            "season": import_data.parse_int(row["season"]),
            "week": import_data.parse_int(row["week"]),
            "game_type": row["game_type"],
            "player_key": row["player_key"],
            "team_code": team_code,
            "position": row["position"],
            "report_primary_injury": row["report_primary_injury"],
            "report_secondary_injury": row["report_secondary_injury"],
            "report_status": row["report_status"],
            "practice_primary_injury": row["practice_primary_injury"],
            "practice_secondary_injury": row["practice_secondary_injury"],
            "practice_status": row["practice_status"],
            "date_modified": row["date_modified"],
            "verification_status": "SOURCE_BACKED",
            "source_id": SOURCE_ID,
        }
        cols = list(rec.keys())
        c.execute(
            f"""INSERT INTO nfl_player_injuries({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})
                ON CONFLICT(season, week, game_type, player_key) DO UPDATE SET
                {','.join(f"{k}=excluded.{k}" for k in cols if k not in ('season', 'week', 'game_type', 'player_key'))}""",
            [rec[k] for k in cols],
        )
        published += 1
    total_staged = c.execute(
        "SELECT COUNT(*) FROM staging_nfl_injuries WHERE batch_id=?", (bid,)
    ).fetchone()[0]
    unresolved = total_staged - total_staged_resolved
    return published, unresolved


def run_nfl_injuries_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM nfl_player_injuries").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    import time
    import urllib.error
    import urllib.request

    total_read = total_staged = total_rejected = total_published = total_unresolved = 0
    seasons_imported: list[int] = []
    seasons_not_published: list[int] = []

    try:
        manifest_path = IMPORTS_DIR / "nflverse_injuries_manifest.txt"
        manifest_path.write_text(
            "\n".join(INJURIES_URL_TMPL.format(season=s) for s in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1))
        )

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, manifest_path)
        c.execute("BEGIN")
        try:
            for season in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1):
                path = IMPORTS_DIR / f"nflverse_injuries_{season}.csv"
                url = INJURIES_URL_TMPL.format(season=season)
                req = urllib.request.Request(url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
                last_err: Exception | None = None
                for attempt in range(2):
                    try:
                        with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
                            while True:
                                chunk = resp.read(1024 * 1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        last_err = None
                        break
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            last_err = None
                            seasons_not_published.append(season)
                            break
                        last_err = e
                    except Exception as e:
                        last_err = e
                    time.sleep(2)
                if last_err is not None:
                    raise last_err
                if season in seasons_not_published:
                    continue
                time.sleep(0.3)

                read, staged, rejected = _stage_one_season(c, bid, season, path)
                total_read += read
                total_staged += staged
                total_rejected += rejected
                seasons_imported.append(season)

            published, unresolved = _publish(c, bid)
            total_published += published
            total_unresolved += unresolved

            qa_count = c.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
            c.execute(
                "UPDATE import_batches SET finished_at=?, status='PUBLISHED', rows_read=?, rows_staged=?, "
                "rows_published=?, rows_rejected=?, qa_issue_count=? WHERE batch_id=?",
                (_dt.datetime.now(_dt.timezone.utc).isoformat(), total_read, total_staged,
                 total_published, total_rejected, qa_count, bid),
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
                c, table="nfl_player_injuries", rows_published=total_published, rows_rejected=total_rejected,
                rows_read=total_read, min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=total_read, rows_imported=total_published, rows_rejected=total_rejected,
                failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = total_published == 0 and total_rejected == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=total_read, rows_imported=total_published, rows_rejected=total_rejected, no_op=no_op,
            detail={"batch_id": bid, "seasons_imported": seasons_imported,
                    "seasons_not_yet_published": seasons_not_published, "rows_unresolved_identity": total_unresolved},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "rows_downloaded": total_read, "rows_imported": total_published, "rows_rejected": total_rejected,
            "rows_unresolved_identity": total_unresolved, "seasons_imported": seasons_imported,
            "seasons_not_yet_published": seasons_not_published, "backup_id": backup["backup_id"],
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


def last_run_status() -> dict | None:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    row = c.execute(
        "SELECT * FROM refresh_runs WHERE league=? AND dataset_name=? ORDER BY started_at DESC LIMIT 1",
        (LEAGUE, DATASET),
    ).fetchone()
    c.close()
    return dict(row) if row else None
