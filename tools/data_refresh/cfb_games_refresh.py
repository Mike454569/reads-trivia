"""CFB production data refresh -- games/schedules/scores.

Real source, confirmed live before writing any code: cfbfastR-data's
per-season schedules CSV
(https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/schedules/csv/cfb_schedules_{season}.csv),
same repo/URL family fetch_cfb_roster_history.py and this package's own
cfb_refresh.py (rosters) already use, already `approved_for_import=1` in
the `sources` table as SPORTSDATAVERSE_CFB.

Real column-name drift found and handled (not silently ignored): the
Engine's vendored stage_cfb_games() (import_data.py) expects a CSV with
columns game_date/home_score/away_score/stadium_name (or stadium) --
the LIVE current cfbfastR-data schedules CSV instead has
start_date/home_points/away_points/venue. Confirmed directly (col() in
import_data.py does an EXACT key match, no fuzzy matching) that feeding
the live CSV to stage_cfb_games unchanged would silently stage every row
with NULL date/score/venue. Rather than edit vendored code (never done in
this project) or accept that silent data-quality bug, this module
remaps the real live headers to the exact names stage_cfb_games expects
before calling it -- reusing that real, tested staging logic unmodified,
just bridging it to the source's actual current shape.

Also does NOT call the vendored publish_cfb_games() -- that function
hardcodes source_id='READS_CFB_MASTER' (the sources table describes that
as "user-provided workbook", i.e. a manual one-time import, not a live
feed). Reusing it here would mislabel every automated update's provenance.
This module's own _publish() mirrors its real INSERT/UPDATE shape exactly
(same target table, same identity resolution via the real resolve_school()
helper, same ON CONFLICT semantics) but with the correct
source_id='SPORTSDATAVERSE_CFB' -- preserving accurate source attribution
(a genuine, not cosmetic, requirement) rather than duplicating logic for
its own sake.
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import sys
from pathlib import Path

from . import safety
from . import _pickem_status

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import import_data  # noqa: E402  Engine's own stage_cfb_games/resolve_school/col/parse_int, reused as-is

LEAGUE = "CFB"
DATASET = "cfb_games"
SOURCE_ID = "SPORTSDATAVERSE_CFB"
SCHEDULE_URL = "https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/schedules/csv/cfb_schedules_{season}.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"

# Live source header -> the exact header name import_data.stage_cfb_games()
# already looks for (see module docstring for why this remap exists).
_HEADER_REMAP = {"start_date": "game_date", "home_points": "home_score", "away_points": "away_score", "venue": "stadium_name"}


def _current_season() -> int:
    return _dt.datetime.now(_dt.timezone.utc).year


def _remap_csv(src_path: Path, dst_path: Path) -> None:
    with open(src_path, newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin)
        fieldnames = [_HEADER_REMAP.get(h, h) for h in reader.fieldnames]
        with open(dst_path, "w", newline="", encoding="utf-8") as fout:
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                writer.writerow({_HEADER_REMAP.get(k, k): v for k, v in row.items()})


def _publish(c, bid: str) -> int:
    """Mirrors import_data.publish_cfb_games()'s real INSERT/UPDATE shape
    exactly, with the one deliberate change of a correct source_id (see
    module docstring). Dynamic Weekly Pick'em pass: also captures
    neutral_site/home_division/away_division/season_type -- real fields
    already present in the live source CSV (confirmed directly) and
    already passed through into stage_cfb_games()'s own raw_json column
    unchanged (none of these are in _HEADER_REMAP, so raw_json's key names
    for them are stable regardless of which historical process staged a
    given row) -- and derives status/winner the same way
    nfl_games_refresh.py now does, via the shared _pickem_status helper.

    season_type is the critical fix here, a real, previously-hidden defect
    found while verifying this pass's own CFB week/season_type collision
    fix (tools/director_v04/weekly_pickem.py's _cfb_slate_rows()): this
    module's own _publish() NEVER captured season_type before this pass --
    confirmed directly, every row this script has ever written had it
    NULL, only ever populated for OLDER rows by whatever bulk process
    loaded this table before this script existed. Left uncaught, EVERY
    future season (starting with the real 2026 season this pass exists to
    add) would silently return zero games from the new
    `season_type='regular'` filter -- breaking the exact season Pick'em
    most needs. bowl_name is only ever set from the source's own real
    `notes` field for a real postseason row -- a regular-season row's
    `notes` can legitimately describe a real neutral-site event name (e.g.
    "Aer Lingus College Football Classic"), which is NOT a bowl name and
    must never be mislabeled as one."""
    published = 0
    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat()
    for r in c.execute(
        """SELECT game_id,season,week,game_date,home_school,away_school,home_score,away_score,
           stadium_name,conference_game,raw_json FROM staging_cfb_games WHERE batch_id=?""", (bid,)
    ):
        gid, season, week, date, home, away, hs, away_score, stadium, conf, raw_json = r
        hid = import_data.resolve_school(c, home)
        aid = import_data.resolve_school(c, away)
        if not hid or not aid:
            c.execute(
                "INSERT INTO qa_issues(severity,entity_type,entity_id,issue_type,detail) "
                "VALUES('WARN','cfb_game',?,'UNMAPPED_SCHOOL',?)",
                (gid, f"home={home} mapped={hid}; away={away} mapped={aid}"),
            )
            continue

        extra = json.loads(raw_json) if raw_json else {}

        def _bool_col(v):
            s = str(v).strip().lower()
            return 1 if s == "true" else (0 if s == "false" else None)

        neutral_site = _bool_col(extra.get("neutral_site"))
        home_division = extra.get("home_division") or None
        away_division = extra.get("away_division") or None
        if home_division in ("NA", "na"):
            home_division = None
        if away_division in ("NA", "na"):
            away_division = None

        season_type = extra.get("season_type") or None
        if season_type in ("NA", "na"):
            season_type = None
        bowl_name = None
        if season_type == "postseason":
            notes = extra.get("notes")
            bowl_name = notes if notes and notes not in ("NA", "na") else None

        # Player Experience pass: real conference names (e.g. "SEC", "Big
        # Ten"), confirmed live in this same raw_json blob (never touched
        # by _HEADER_REMAP) -- needed for the new POWER4/CONFERENCE Pick'em
        # slates. Plain overwrite (not COALESCE, unlike season_type/
        # bowl_name above): conference is always present in the live
        # source for a real, resolved school, never genuinely absent.
        home_conference = extra.get("home_conference") or None
        away_conference = extra.get("away_conference") or None
        if home_conference in ("NA", "na"):
            home_conference = None
        if away_conference in ("NA", "na"):
            away_conference = None

        existing = c.execute(
            "SELECT status, game_date FROM cfb_games_canonical WHERE game_id=?", (gid,)
        ).fetchone()
        existing_kickoff = _pickem_status.parse_iso(existing["game_date"]) if existing else None
        new_kickoff = _pickem_status.parse_iso(date)
        status, winner = _pickem_status.compute_status_and_winner(
            existing_status=existing["status"] if existing else None,
            existing_kickoff=existing_kickoff, new_kickoff=new_kickoff,
            home_score=hs, away_score=away_score, home_code=hid, away_code=aid,
        )

        c.execute(
            """INSERT INTO cfb_games_canonical(
               game_id,season,week,game_date,home_school_id,away_school_id,
               home_score,away_score,stadium_name,conference_game,verification_status,source_id,
               neutral_site,home_division,away_division,status,winner,updated_at,season_type,bowl_name,
               home_conference,away_conference)
               VALUES (?,?,?,?,?,?,?,?,?,?,'SOURCE_BACKED',?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(game_id) DO UPDATE SET season=excluded.season,week=excluded.week,game_date=excluded.game_date,
               home_school_id=excluded.home_school_id,away_school_id=excluded.away_school_id,
               home_score=excluded.home_score,away_score=excluded.away_score,stadium_name=excluded.stadium_name,
               conference_game=excluded.conference_game,verification_status='SOURCE_BACKED',source_id=?,
               neutral_site=excluded.neutral_site,home_division=excluded.home_division,
               away_division=excluded.away_division,status=excluded.status,winner=excluded.winner,
               updated_at=excluded.updated_at,
               season_type=COALESCE(excluded.season_type, cfb_games_canonical.season_type),
               bowl_name=COALESCE(excluded.bowl_name, cfb_games_canonical.bowl_name),
               home_conference=excluded.home_conference,away_conference=excluded.away_conference""",
            (gid, season, week, date, hid, aid, hs, away_score, stadium, conf, SOURCE_ID,
             neutral_site, home_division, away_division, status, winner, now_iso, season_type, bowl_name,
             home_conference, away_conference, SOURCE_ID),
        )
        published += 1
    return published


def run_cfb_games_refresh(*, season: int | None = None) -> dict:
    season = season or _current_season()
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_games_canonical").fetchone()[0]
    source_url = SCHEDULE_URL.format(season=season)
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    try:
        import urllib.error
        import urllib.request

        raw_path = IMPORTS_DIR / f"cfb_schedules_{season}_raw.csv"
        remapped_path = IMPORTS_DIR / f"cfb_schedules_{season}.csv"
        req = urllib.request.Request(source_url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(raw_path, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                c = engine_bootstrap.connect()
                safety.finish_run(c, run_id, status="SOURCE_NOT_YET_PUBLISHED", backup_id=backup["backup_id"],
                                   detail={"season": season, "source_url": source_url})
                c.close()
                return {"status": "SOURCE_NOT_YET_PUBLISHED", "run_id": run_id, "season": season,
                        "reason": f"{source_url} returned 404 -- not yet published upstream"}
            raise

        _remap_csv(raw_path, remapped_path)

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, remapped_path)
        c.execute("BEGIN")
        try:
            read, staged, rejected = import_data.stage_cfb_games(c, bid, remapped_path)
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
                c, table="cfb_games_canonical", rows_published=published, rows_rejected=rejected, rows_read=read,
                min_row_count_floor=baseline_count,
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
            rows_downloaded=read, rows_imported=published, rows_rejected=rejected, no_op=no_op,
            detail={"season": season, "batch_id": bid},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op, "season": season,
            "rows_downloaded": read, "rows_imported": published, "rows_rejected": rejected,
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
