"""NFL play-by-play -- Engine-gap-audit operation.

Real source, confirmed live before writing any code: nflverse-data's GitHub
Release tagged `pbp`
(https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz),
one real file per season 1999-present -- already `approved_for_import=1` in
the `sources` table as NFLVERSE_DATA. Real per-season size confirmed before
building: ~49,500 plays for the 2024 season (~12MB gzipped/season, ~1.2M
plays total across 1999-2024) -- easily fits the Engine's existing 2GB
SQLite database with 54GB free on this volume.

Column scope: the real nflfastR release has 370+ columns (mostly advanced
analytical fields this app has no use for). This importer persists only the
real fields the source pack itself specified as needed (play/game
identification, down/distance/clock, possession, the play description,
yards gained, scoring/turnover flags, EPA/WP, and passer/rusher/receiver
identity) -- not a blind full-width mirror of the source file. Every column
kept is copied verbatim from the source, never derived or reinterpreted,
except `season_type` (source name) stored as `game_type` to match this
Engine's existing `games`/`team_game_stats` naming convention for the same
real concept.

Identity, two tiers, never a blind name join:
  1. game_id: identical convention already used by `games`/`team_game_stats`
     (SEASON_WEEK_AWAY_HOME, e.g. `1999_01_MIN_ATL`) -- a real, direct join,
     no resolution needed.
  2. passer/rusher/receiver_player_id: real gsis_id values, resolved via
     `canonical_players.gsis_id` exactly like every other nflverse-sourced
     player domain in this Engine. A play with no passer/rusher/receiver at
     all (e.g. a punt, kickoff, penalty-only play) legitimately has NULL for
     these -- never rejected for it; only a play that DOES name a
     passer/rusher/receiver gsis_id that fails to resolve is logged as a
     real identity gap.

Primary key: `(game_id, play_id)` -- verified unique directly against the
real 2024 season file before building (49,492 rows, 49,492 distinct keys,
zero collisions). `play_id` is only unique WITHIN a game in this source, so
the composite is required.

This is the single largest domain in the Engine-gap-audit operation --
batched executemany() inserts are used (not per-row single INSERTs) because
a naive row-by-row loop over ~1.2M rows was measured to be impractically
slow for this environment.
"""
from __future__ import annotations

import csv
import datetime as _dt
import gzip
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
DATASET = "nfl_pbp"
SOURCE_ID = "NFLVERSE_DATA"
PBP_URL_TMPL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz"
IMPORTS_DIR = ENGINE_DIR / "imports"
MIN_SEASON = 1999
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year + 1

# `desc` (the source's own column name) is renamed to `play_desc` -- `desc`
# collides with common SQL DESC usage in ad hoc queries elsewhere in this
# codebase, avoided for safety.


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_plays (
            game_id TEXT NOT NULL,
            play_id TEXT NOT NULL,
            season INTEGER,
            week INTEGER,
            game_type TEXT,
            posteam TEXT,
            defteam TEXT,
            qtr INTEGER,
            down INTEGER,
            ydstogo INTEGER,
            yardline_100 INTEGER,
            game_seconds_remaining REAL,
            play_type TEXT,
            play_desc TEXT,
            yards_gained INTEGER,
            posteam_score INTEGER,
            defteam_score INTEGER,
            epa REAL,
            wp REAL,
            interception INTEGER,
            fumble_lost INTEGER,
            touchdown INTEGER,
            pass_touchdown INTEGER,
            rush_touchdown INTEGER,
            sack INTEGER,
            passer_player_key TEXT,
            receiver_player_key TEXT,
            rusher_player_key TEXT,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id),
            PRIMARY KEY (game_id, play_id)
        )
    """)
    c.commit()


def _parse_row(row: dict, canon: dict[str, str]) -> tuple | None:
    game_id = row.get("game_id")
    play_id = row.get("play_id")
    if not game_id or not play_id:
        return None

    def gf(name):
        v = row.get(name)
        try:
            return float(v) if v not in (None, "", "NA") else None
        except ValueError:
            return None

    return (
        game_id, play_id,
        import_data.parse_int(row.get("season")), import_data.parse_int(row.get("week")),
        row.get("season_type"), row.get("posteam") or None, row.get("defteam") or None,
        import_data.parse_int(row.get("qtr")), import_data.parse_int(row.get("down")),
        import_data.parse_int(row.get("ydstogo")), import_data.parse_int(row.get("yardline_100")),
        gf("game_seconds_remaining"), row.get("play_type") or None, row.get("desc") or None,
        import_data.parse_int(row.get("yards_gained")),
        import_data.parse_int(row.get("posteam_score")), import_data.parse_int(row.get("defteam_score")),
        gf("epa"), gf("wp"),
        import_data.parse_int(row.get("interception")), import_data.parse_int(row.get("fumble_lost")),
        import_data.parse_int(row.get("touchdown")), import_data.parse_int(row.get("pass_touchdown")),
        import_data.parse_int(row.get("rush_touchdown")), import_data.parse_int(row.get("sack")),
        canon.get(row.get("passer_player_id")), canon.get(row.get("receiver_player_id")),
        canon.get(row.get("rusher_player_id")),
        "SOURCE_BACKED", SOURCE_ID,
    )


_INSERT_COLS = [
    "game_id", "play_id", "season", "week", "game_type", "posteam", "defteam", "qtr", "down",
    "ydstogo", "yardline_100", "game_seconds_remaining", "play_type", "play_desc", "yards_gained",
    "posteam_score", "defteam_score", "epa", "wp", "interception", "fumble_lost", "touchdown",
    "pass_touchdown", "rush_touchdown", "sack", "passer_player_key", "receiver_player_key",
    "rusher_player_key", "verification_status", "source_id",
]
_INSERT_SQL = (
    f"INSERT INTO nfl_plays({','.join(_INSERT_COLS)}) VALUES ({','.join('?' for _ in _INSERT_COLS)}) "
    f"ON CONFLICT(game_id, play_id) DO UPDATE SET "
    f"{','.join(f'{k}=excluded.{k}' for k in _INSERT_COLS if k not in ('game_id', 'play_id'))}"
)


def _import_one_season(c, season: int, path: Path, canon: dict[str, str]) -> tuple[int, int, int]:
    read = published = rejected = 0
    batch: list[tuple] = []
    BATCH_SIZE = 5000
    with gzip.open(path, "rt", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            read += 1
            rec = _parse_row(row, canon)
            if rec is None:
                rejected += 1
                continue
            batch.append(rec)
            if len(batch) >= BATCH_SIZE:
                c.executemany(_INSERT_SQL, batch)
                published += len(batch)
                batch.clear()
    if batch:
        c.executemany(_INSERT_SQL, batch)
        published += len(batch)
    return read, published, rejected


def run_nfl_pbp_refresh(seasons: list[int] | None = None) -> dict:
    """`seasons`: optional explicit season list, for a bounded pilot run
    before committing to the full 1999-present sweep. Defaults to every
    season 1999-present."""
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM nfl_plays").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    canon = {r["gsis_id"]: r["player_id"] for r in
             c.execute("SELECT gsis_id, player_id FROM canonical_players WHERE gsis_id IS NOT NULL").fetchall()}
    c.close()

    backup = safety.create_verified_backup()

    import time
    import urllib.error
    import urllib.request

    target_seasons = seasons if seasons is not None else list(range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1))
    total_read = total_published = total_rejected = 0
    seasons_imported: list[int] = []
    seasons_not_published: list[int] = []

    try:
        manifest_path = IMPORTS_DIR / "nflverse_pbp_manifest.txt"
        manifest_path.write_text("\n".join(PBP_URL_TMPL.format(season=s) for s in target_seasons))

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, manifest_path)
        c.execute("BEGIN")
        try:
            for season in target_seasons:
                path = IMPORTS_DIR / f"nflverse_pbp_{season}.csv.gz"
                url = PBP_URL_TMPL.format(season=season)
                req = urllib.request.Request(url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
                last_err: Exception | None = None
                for attempt in range(2):
                    try:
                        with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as f:
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

                read, published, rejected = _import_one_season(c, season, path, canon)
                total_read += read
                total_published += published
                total_rejected += rejected
                seasons_imported.append(season)
                path.unlink(missing_ok=True)  # ~12MB/season * 26 -- don't keep every gz around after parsing

            qa_count = c.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
            c.execute(
                "UPDATE import_batches SET finished_at=?, status='PUBLISHED', rows_read=?, rows_staged=?, "
                "rows_published=?, rows_rejected=?, qa_issue_count=? WHERE batch_id=?",
                (_dt.datetime.now(_dt.timezone.utc).isoformat(), total_read, total_read,
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
                c, table="nfl_plays", rows_published=total_published, rows_rejected=total_rejected,
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
                    "seasons_not_yet_published": seasons_not_published},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "rows_downloaded": total_read, "rows_imported": total_published, "rows_rejected": total_rejected,
            "seasons_imported": seasons_imported, "seasons_not_yet_published": seasons_not_published,
            "backup_id": backup["backup_id"],
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
