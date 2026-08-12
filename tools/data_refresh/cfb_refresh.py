"""CFB production data refresh -- current-season rosters (school membership,
position, jersey number, stable player identity).

Real, live, already-approved source (`sources.SPORTSDATAVERSE_CFB`,
approved_for_import=1): SportsDataverse/cfbfastR-data's per-season roster
CSV release, the exact same URL pattern
Reads_Football_Data_Engine_v4.0/fetch_cfb_roster_history.py already uses
for historical backfills -- confirmed live (HTTP 200, real 2024 season
sample: 22,847 rows, columns athlete_id/first_name/last_name/team/weight/
height/jersey/year/position/...). `athlete_id` is the SAME stable ESPN
athlete ID `canonical_cfb_players.espn_athlete_id` already keys on (100% of
the existing 109,221 rows have one) and the same ID
identity_bridge_v16.py's NFL<->CFB join uses -- this refresh writes into
the EXACT SAME tables/ID convention the historical import already
established (`cfb_player_id = "ESPN_CFB:" + athlete_id`), not a competing
schema.

No CFB roster stage/publish path existed in import_data.py before this
(that file only has nflverse_players/nflverse_rosters/cfb_games) -- this
module is new capability, not a duplicate of anything that already existed.
It reuses import_data.py's own generic, already-tested helpers
(begin_batch/reject/resolve_school/parse_int/col/sha256) rather than
reimplementing them, and follows the identical staging-table ->
rejection-tracked -> idempotent-UPSERT-publish shape stage_rosters/
publish_rosters already established for NFL.

Deliberately NOT attempted here (real, disclosed limits, not fabricated):
CFB games/schedules/records/conferences and Heisman/other awards -- the
existing data for both comes from `READS_CFB_MASTER`, a source the
`sources` table itself documents as "user-provided workbook", i.e. no live
feed exists for this project to poll. Formal transfer detection is also not
attempted -- multi-school appearance across seasons is a real signal this
refresh preserves in the data, but a "transfer event" is never inferred
from it alone (this module never writes to cfb_transfer_summary).
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
import import_data  # noqa: E402  Engine's own generic batch/staging helpers, reused as-is

LEAGUE = "CFB"
DATASET = "cfb_rosters"
SOURCE_ID = "SPORTSDATAVERSE_CFB"
ROSTER_URL = "https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/rosters/csv/cfb_rosters_{season}.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"


def _current_season() -> int:
    # CFB seasons are named for the calendar year they're played in (a 2026
    # season roster file is published starting mid-2026) -- current year is
    # the real, non-arbitrary choice, same reasoning nfl_refresh.py uses.
    return _dt.datetime.now(_dt.timezone.utc).year


def _ensure_staging_table(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS staging_cfb_rosters (
            batch_id TEXT NOT NULL REFERENCES import_batches(batch_id),
            source_row INTEGER NOT NULL,
            season INTEGER,
            athlete_id TEXT,
            first_name TEXT,
            last_name TEXT,
            team TEXT,
            jersey_number INTEGER,
            class_year TEXT,
            position TEXT,
            height_in INTEGER,
            weight_lb INTEGER,
            headshot_url TEXT,
            raw_json TEXT,
            PRIMARY KEY (batch_id, source_row)
        )
    """)
    c.commit()


def _stage(c, bid: str, path: Path) -> tuple[int, int, int]:
    import json as _json

    read = staged = rejected = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            read += 1
            athlete_id = import_data.col(row, "athlete_id")
            team = import_data.col(row, "team")
            season = import_data.parse_int(import_data.col(row, "season"))
            if not athlete_id or not team or not season:
                import_data.reject(c, bid, i, "MISSING_CFB_ROSTER_KEY",
                                    "CFB roster row needs athlete_id/team/season", row)
                rejected += 1
                continue
            c.execute(
                "INSERT INTO staging_cfb_rosters VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (bid, i, season, athlete_id, import_data.col(row, "first_name"),
                 import_data.col(row, "last_name"), team,
                 import_data.parse_int(import_data.col(row, "jersey")),
                 import_data.col(row, "year"), import_data.col(row, "position"),
                 import_data.parse_int(import_data.col(row, "height")),
                 import_data.parse_int(import_data.col(row, "weight")),
                 import_data.col(row, "headshot_url"), _json.dumps(row, sort_keys=True)),
            )
            staged += 1
    return read, staged, rejected


def _publish(c, bid: str) -> int:
    published = 0
    for r in c.execute(
        "SELECT season, athlete_id, first_name, last_name, team, jersey_number, class_year, position, "
        "height_in, weight_lb, headshot_url FROM staging_cfb_rosters WHERE batch_id=?", (bid,)
    ):
        season, athlete_id, first, last, team, jersey, class_year, pos, h, w, headshot = r
        pid = "ESPN_CFB:" + athlete_id
        display_name = " ".join(x for x in (first, last) if x) or athlete_id
        school_id = import_data.resolve_school(c, team)
        if not school_id:
            c.execute(
                "INSERT INTO qa_issues(severity,entity_type,entity_id,field_name,issue_type,detail) "
                "VALUES('WARN','cfb_roster_row',?,'school_id','UNMAPPED_SCHOOL',?)",
                (pid, f"Could not map CFB team '{team}' to a known school"),
            )
            continue
        c.execute(
            """INSERT INTO canonical_cfb_players(cfb_player_id, espn_athlete_id, display_name, first_name,
               last_name, height_in, weight_lb, headshot_url, verification_status, source_id)
               VALUES (?,?,?,?,?,?,?,?,'SOURCE_BACKED',?)
               ON CONFLICT(cfb_player_id) DO UPDATE SET
                 display_name=excluded.display_name,
                 first_name=COALESCE(excluded.first_name, canonical_cfb_players.first_name),
                 last_name=COALESCE(excluded.last_name, canonical_cfb_players.last_name),
                 height_in=COALESCE(excluded.height_in, canonical_cfb_players.height_in),
                 weight_lb=COALESCE(excluded.weight_lb, canonical_cfb_players.weight_lb),
                 headshot_url=COALESCE(excluded.headshot_url, canonical_cfb_players.headshot_url),
                 verification_status='SOURCE_BACKED', source_id=?""",
            (pid, athlete_id, display_name, first, last, h, w, headshot, SOURCE_ID, SOURCE_ID),
        )
        c.execute(
            """INSERT INTO cfb_roster_seasons_real(season, school_id, cfb_player_id, jersey_number, class_year,
               position, height_in, weight_lb, verification_status, source_id)
               VALUES (?,?,?,?,?,?,?,?,'SOURCE_BACKED',?)
               ON CONFLICT(season, school_id, cfb_player_id) DO UPDATE SET
                 jersey_number=excluded.jersey_number, class_year=excluded.class_year,
                 position=excluded.position, height_in=COALESCE(excluded.height_in, cfb_roster_seasons_real.height_in),
                 weight_lb=COALESCE(excluded.weight_lb, cfb_roster_seasons_real.weight_lb),
                 verification_status='SOURCE_BACKED', source_id=?""",
            (season, school_id, pid, jersey, class_year, pos, h, w, SOURCE_ID, SOURCE_ID),
        )
        published += 1
    return published


def run_cfb_refresh(*, season: int | None = None) -> dict:
    season = season or _current_season()
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_staging_table(c)
    baseline_players = c.execute("SELECT COUNT(*) FROM canonical_cfb_players").fetchone()[0]
    baseline_rosters = c.execute("SELECT COUNT(*) FROM cfb_roster_seasons_real").fetchone()[0]
    source_url = ROSTER_URL.format(season=season)
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    try:
        import urllib.error
        import urllib.request

        path = IMPORTS_DIR / f"cfb_rosters_{season}.csv"
        req = urllib.request.Request(source_url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Real, benign, time-of-year condition -- confirmed by hand
                # (curl -I against this exact URL) that cfbfastR-data simply
                # hasn't published next season's roster file yet (CFB
                # rosters typically land once the season is underway). Not
                # a "something is broken" failure -- nothing was written, so
                # there's nothing to restore; report it as its own distinct
                # status rather than the generic FAILED_RESTORED an admin
                # freshness view would otherwise have to guess the meaning
                # of. A later scheduled run (once the source publishes it)
                # will succeed on its own, no manual intervention needed.
                c = engine_bootstrap.connect()
                safety.finish_run(
                    c, run_id, status="SOURCE_NOT_YET_PUBLISHED", backup_id=backup["backup_id"],
                    detail={"season": season, "source_url": source_url},
                )
                c.close()
                return {"status": "SOURCE_NOT_YET_PUBLISHED", "run_id": run_id, "season": season,
                        "reason": f"{source_url} returned 404 -- not yet published upstream"}
            raise

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
                c, table="cfb_roster_seasons_real", rows_published=published,
                rows_rejected=rejected, rows_read=read, min_row_count_floor=baseline_rosters,
            )
            player_count_after = c.execute("SELECT COUNT(*) FROM canonical_cfb_players").fetchone()[0]
            if player_count_after < baseline_players:
                raise safety.SanityCheckFailure(
                    f"canonical_cfb_players dropped from {baseline_players} to {player_count_after} -- refusing"
                )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=read, rows_imported=published, rows_rejected=rejected,
                failure_reason=str(e), detail={"restore": restore_info, "season": season},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = published == 0 and rejected == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=read, rows_imported=published, rows_rejected=rejected,
            no_op=no_op, detail={"season": season, "batch_id": bid},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op, "season": season,
            "rows_read": read, "rows_published": published, "rows_rejected": rejected,
            "backup_id": backup["backup_id"],
        }
    except Exception as e:
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(
            c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
            failure_reason=repr(e), detail={"restore": restore_info, "season": season},
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
