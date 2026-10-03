"""CFB recruiting refresh from the official CFBD recruiting API.

Source: GET /recruiting/players. Current-season-only by default to protect API
quota; historical backfills are explicit via seasons=.
"""
from __future__ import annotations

import datetime as _dt

from . import _cfbd_client, safety
from tools.quiz_export import engine as engine_bootstrap

LEAGUE = "CFB"
DATASET = "cfb_recruiting"
SOURCE_ID = "CFBD_API_LIVE"
MIN_SEASON = 2000
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year + 1


def _ensure_schema(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_recruits (
            recruit_id TEXT PRIMARY KEY,
            athlete_id TEXT,
            cfb_player_id TEXT,
            class_year INTEGER NOT NULL,
            recruit_type TEXT,
            ranking INTEGER,
            recruit_name TEXT NOT NULL,
            high_school TEXT,
            committed_school_id TEXT,
            committed_school_name TEXT,
            position TEXT,
            height REAL,
            weight INTEGER,
            stars INTEGER,
            rating REAL,
            city TEXT,
            state_province TEXT,
            country TEXT,
            source_id TEXT NOT NULL,
            verification_status TEXT NOT NULL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS ix_cfb_recruits_year ON cfb_recruits(class_year,ranking)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_cfb_recruits_school ON cfb_recruits(committed_school_id,class_year)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_cfb_recruits_player ON cfb_recruits(cfb_player_id)")
    c.commit()


def _resolve_school(c, name):
    if not name:
        return None
    row = c.execute("SELECT school_id FROM schools WHERE school_name=?", (name,)).fetchone()
    if row:
        return row["school_id"]
    row = c.execute("SELECT school_id FROM school_aliases WHERE alias_name=?", (name,)).fetchone()
    return row["school_id"] if row else None


def _canonical_player_id(c, athlete_id):
    if not athlete_id:
        return None
    candidate = "ESPN_CFB:" + str(athlete_id)
    row = c.execute(
        "SELECT 1 FROM canonical_cfb_players WHERE cfb_player_id=? LIMIT 1",
        (candidate,),
    ).fetchone()
    return candidate if row else None


def run_cfb_recruiting_refresh(seasons=None):
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline = c.execute("SELECT COUNT(*) FROM cfb_recruits").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup_or_finish_failed(run_id)
    target = seasons if seasons is not None else [MAX_SEASON_ATTEMPT]
    downloaded = published = unresolved_school = 0
    done = []

    try:
        c = engine_bootstrap.connect()
        for year in target:
            rows = _cfbd_client.get("/recruiting/players", {"year": int(year)})
            downloaded += len(rows)
            c.execute("DELETE FROM cfb_recruits WHERE class_year=? AND source_id=?", (int(year), SOURCE_ID))
            for row in rows:
                rid = str(row.get("id") or "").strip()
                name = str(row.get("name") or "").strip()
                committed = row.get("committedTo")
                if not rid or not name:
                    continue
                school_id = _resolve_school(c, committed)
                if committed and not school_id:
                    unresolved_school += 1
                athlete_id = row.get("athleteId")
                cfb_player_id = _canonical_player_id(c, athlete_id)
                c.execute(
                    """INSERT OR REPLACE INTO cfb_recruits(
                       recruit_id,athlete_id,cfb_player_id,class_year,recruit_type,ranking,
                       recruit_name,high_school,committed_school_id,committed_school_name,
                       position,height,weight,stars,rating,city,state_province,country,
                       source_id,verification_status)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        rid,
                        str(athlete_id) if athlete_id is not None else None,
                        cfb_player_id,
                        int(row.get("year") or year),
                        str(row.get("recruitType") or "") or None,
                        row.get("ranking"),
                        name,
                        row.get("school"),
                        school_id,
                        committed,
                        row.get("position"),
                        row.get("height"),
                        row.get("weight"),
                        row.get("stars"),
                        row.get("rating"),
                        row.get("city"),
                        row.get("stateProvince"),
                        row.get("country"),
                        SOURCE_ID,
                        "SOURCE_BACKED",
                    ),
                )
                published += 1
            c.commit()
            done.append(int(year))

        safety.run_post_refresh_sanity_checks(
            c,
            table="cfb_recruits",
            rows_published=published,
            rows_rejected=0,
            rows_read=downloaded,
            min_row_count_floor=baseline,
        )
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=downloaded, rows_imported=published, rows_rejected=0,
            no_op=(published == 0),
            detail={
                "seasons_done": done,
                "rows_unresolved_school": unresolved_school,
            },
        )
        c.close()
        return {
            "status":"SUCCESS","run_id":run_id,"rows_downloaded":downloaded,
            "rows_imported":published,"rows_unresolved_school":unresolved_school,
            "seasons_done":done,"backup_id":backup["backup_id"],
        }
    except _cfbd_client.CfbdUnavailable as exc:
        c2 = engine_bootstrap.connect()
        safety.finish_run(
            c2, run_id, status="UNAVAILABLE_NO_CREDENTIAL", backup_id=backup["backup_id"],
            failure_reason=str(exc),
        )
        c2.close()
        return {"status":"UNAVAILABLE_NO_CREDENTIAL","run_id":run_id,"reason":str(exc)}
    except Exception as exc:
        try:
            c.close()
        except Exception:
            pass
        restore = safety.safe_restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(
            c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
            failure_reason=repr(exc), detail={"restore": restore},
        )
        c2.close()
        return {"status":"FAILED_RESTORED","run_id":run_id,"reason":repr(exc)}


def last_run_status():
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    row = c.execute(
        "SELECT * FROM refresh_runs WHERE league=? AND dataset_name=? ORDER BY started_at DESC LIMIT 1",
        (LEAGUE, DATASET),
    ).fetchone()
    c.close()
    return dict(row) if row else None
