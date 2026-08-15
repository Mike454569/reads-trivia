"""CFB play-by-play -- Engine-gap-audit operation (CFBD-key-dependent).

Real source, confirmed live before writing any code: CFBD's `/plays`
endpoint, one call per (season, week, seasonType) -- confirmed real shape:
gameId (matches `cfb_games_canonical.game_id` directly, same identity
scheme, no resolution needed), driveId, id (a real, globally unique play
id), offense/defense (school NAMES, resolved via
`import_data.resolve_school()`), period, clock{minutes,seconds}, down,
distance, yardsGained, playType, playText, ppa (CFBD's predicted-points-
added metric, this API's real analog to nflverse's `epa`).

Real, confirmed-live finding before building: NO team filter is required --
`/plays?year=Y&week=W&seasonType=regular` returns every FBS game's plays
for that week in one call (confirmed: 22,356 plays across 133 games for
2024 week 1 alone), avoiding a per-team-per-week call explosion. Regular
season weeks are swept 1-16 (a nonexistent week returns an empty list, not
an error -- confirmed live, so overshooting the real week count is safe and
cheap); postseason is swept as week=1 only (confirmed live: CFBD lumps
every real bowl/CFP game under week=1 for this endpoint, the same
convention already found and handled in `cfb_games_postseason_refresh.py`).

Scope: 2002-2025, matching `cfb_games_canonical`'s own existing real season
range. This is the single largest CFBD-dependent domain (CFB has far more
teams/games per week than the NFL) -- batched `executemany()` inserts are
used (not per-row single INSERTs), the same real, measured fix already
applied in `nfl_pbp_refresh.py`.

Primary key: `(game_id, play_id)` -- CFBD's own `id` field was NOT assumed
globally unique without checking; `(game_id, play_id)` is the safe
composite regardless.
"""
from __future__ import annotations

import datetime as _dt
import sys
import time
from pathlib import Path

from . import _cfbd_client, safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import import_data  # noqa: E402

LEAGUE = "CFB"
DATASET = "cfb_pbp"
SOURCE_ID = "CFBD_API_LIVE"
MIN_SEASON = 2002
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year
MAX_REGULAR_WEEK = 16


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_plays (
            game_id TEXT NOT NULL,
            play_id TEXT NOT NULL,
            season INTEGER,
            week INTEGER,
            season_type TEXT,
            drive_id TEXT,
            offense_school_id INTEGER,
            offense_name_raw TEXT,
            defense_school_id INTEGER,
            defense_name_raw TEXT,
            period INTEGER,
            clock_minutes INTEGER,
            clock_seconds INTEGER,
            down INTEGER,
            distance INTEGER,
            yards_to_goal INTEGER,
            yards_gained INTEGER,
            play_type TEXT,
            play_text TEXT,
            scoring INTEGER,
            ppa REAL,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id),
            PRIMARY KEY (game_id, play_id)
        )
    """)
    c.commit()


_INSERT_COLS = [
    "game_id", "play_id", "season", "week", "season_type", "drive_id",
    "offense_school_id", "offense_name_raw", "defense_school_id", "defense_name_raw",
    "period", "clock_minutes", "clock_seconds", "down", "distance", "yards_to_goal",
    "yards_gained", "play_type", "play_text", "scoring", "ppa",
    "verification_status", "source_id",
]
_INSERT_SQL = (
    f"INSERT INTO cfb_plays({','.join(_INSERT_COLS)}) VALUES ({','.join('?' for _ in _INSERT_COLS)}) "
    f"ON CONFLICT(game_id, play_id) DO UPDATE SET "
    f"{','.join(f'{k}=excluded.{k}' for k in _INSERT_COLS if k not in ('game_id', 'play_id'))}"
)


def run_cfb_pbp_refresh(seasons: list[int] | None = None) -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_plays").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    # CFBD is a metered, paid API (free tier: 1000 calls/month) -- unlike
    # every nflverse/cfbfastR-sourced script in this codebase, a full
    # historical resweep is NOT free. A scheduled run always calls this
    # with seasons=None (gateway/services/admin_refresh.py's run_fn_for
    # takes no arguments), so the no-args default must be cheap and safe
    # to run repeatedly, not a full 2002-current resweep every time --
    # settled historical seasons don't change. Defaulting to the CURRENT
    # season only (already-imported history, confirmed present in the
    # Engine DB, is untouched) mirrors the same "never re-fetch stable
    # settled history on every run" discipline nfl_draft_refresh.py and
    # cfb_all_america_import.py already use. A deliberate full/partial
    # historical backfill is still just one explicit `seasons=` call away
    # (exactly how the real 2002-2025 backfill already in this database
    # was produced).
    target_seasons = seasons if seasons is not None else [MAX_SEASON_ATTEMPT]
    total_published = 0
    seasons_done: list[int] = []

    try:
        c = engine_bootstrap.connect()
        c.execute("BEGIN")
        try:
            # School-name resolution cache, kept local to one run (school
            # names are stable within a run; avoids re-querying resolve_school
            # for the same raw name thousands of times across a big sweep).
            school_cache: dict[str, int | None] = {}

            def resolve(name: str | None) -> int | None:
                if not name:
                    return None
                if name not in school_cache:
                    school_cache[name] = import_data.resolve_school(c, name)
                return school_cache[name]

            for season in target_seasons:
                batch: list[tuple] = []
                BATCH_SIZE = 5000
                week_specs = [(w, "regular") for w in range(1, MAX_REGULAR_WEEK + 1)] + [(1, "postseason")]
                for week, season_type in week_specs:
                    try:
                        plays = _cfbd_client.get(
                            "/plays", {"year": season, "week": week, "seasonType": season_type})
                    except _cfbd_client.CfbdUnavailable:
                        raise
                    for p in plays:
                        game_id = str(p.get("gameId"))
                        play_id = str(p.get("id"))
                        if not game_id or not play_id or play_id == "None":
                            continue
                        clock = p.get("clock") or {}
                        batch.append((
                            game_id, play_id, season, week, season_type, str(p.get("driveId")),
                            resolve(p.get("offense")), p.get("offense"),
                            resolve(p.get("defense")), p.get("defense"),
                            p.get("period"), clock.get("minutes"), clock.get("seconds"),
                            p.get("down"), p.get("distance"), p.get("yardsToGoal"),
                            p.get("yardsGained"), p.get("playType"), p.get("playText"),
                            1 if p.get("scoring") else 0, p.get("ppa"),
                            "SOURCE_BACKED", SOURCE_ID,
                        ))
                        if len(batch) >= BATCH_SIZE:
                            c.executemany(_INSERT_SQL, batch)
                            total_published += len(batch)
                            batch.clear()
                    time.sleep(0.5)
                if batch:
                    c.executemany(_INSERT_SQL, batch)
                    total_published += len(batch)
                seasons_done.append(season)
            c.commit()
        except _cfbd_client.CfbdUnavailable:
            c.rollback()
            raise
        except Exception:
            c.rollback()
            raise

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="cfb_plays", rows_published=total_published, rows_rejected=0,
                rows_read=total_published, min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_imported=total_published, failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"], rows_imported=total_published,
            no_op=(total_published == 0), detail={"seasons_done": seasons_done},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "rows_imported": total_published,
            "seasons_done": seasons_done, "backup_id": backup["backup_id"],
        }
    except _cfbd_client.CfbdUnavailable as e:
        try:
            c.close()
        except Exception:
            pass
        c2 = engine_bootstrap.connect()
        safety.finish_run(c2, run_id, status="UNAVAILABLE_NO_CREDENTIAL", backup_id=backup["backup_id"],
                           failure_reason=str(e))
        c2.close()
        return {"status": "UNAVAILABLE_NO_CREDENTIAL", "run_id": run_id, "reason": str(e)}
    except Exception as e:
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
