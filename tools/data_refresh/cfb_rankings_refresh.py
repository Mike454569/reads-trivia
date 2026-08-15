"""CFB AP/Coaches Poll rankings -- Engine-gap-audit operation (CFBD-key-
dependent).

Real source, confirmed live before writing any code: CFBD's `/rankings`
endpoint (`GET /rankings?year={season}`), returning every poll for every
week of that season in one call -- confirmed real shape: season, seasonType,
week, polls[] (poll name e.g. "AP Top 25"/"Coaches Poll"/"Playoff
Committee Rankings"), each with ranks[] (rank, teamId, school, conference,
firstPlaceVotes, points). `school` is resolved via `import_data.
resolve_school()` -- the same real fuzzy-normalized match every other CFB
importer in this codebase already uses -- never a blind join on `teamId`
(this Engine has no existing CFBD-teamId column to join against).

Scope: 2002-2025, matching `cfb_games_canonical`'s own existing real season
range.

No natural composite key survives real-world editorial variation across
23 seasons of poll data cleanly enough to trust blindly (e.g. a poll
occasionally being reissued for a week) -- this table uses a surrogate
autoincrement id and full delete-and-republish per run for this source's
scope, the same lesson already learned building `nfl_contracts_refresh.py`
and `cfb_all_america_import.py`.
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
DATASET = "cfb_rankings"
SOURCE_ID = "CFBD_API_LIVE"
MIN_SEASON = 2002
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_rankings (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            week INTEGER NOT NULL,
            season_type TEXT NOT NULL,
            poll TEXT NOT NULL,
            rank INTEGER NOT NULL,
            school_id INTEGER,
            school_name_raw TEXT NOT NULL,
            conference TEXT,
            first_place_votes INTEGER,
            points INTEGER,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id)
        )
    """)
    c.commit()


def run_cfb_rankings_refresh(seasons: list[int] | None = None) -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_rankings").fetchone()[0]
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
            # Always scoped to target_seasons (never a bare "delete
            # everything for this source" branch) -- a no-args call now
            # means "just the current season" (see target_seasons above),
            # and a full-table delete on that path would wipe every prior
            # season's real, already-imported history on every scheduled
            # run while only re-fetching one season back.
            c.executemany(
                "DELETE FROM cfb_rankings WHERE source_id=? AND season=?",
                [(SOURCE_ID, s) for s in target_seasons],
            )

            for season in target_seasons:
                try:
                    weeks = _cfbd_client.get("/rankings", {"year": season})
                except _cfbd_client.CfbdUnavailable:
                    raise
                for wk in weeks:
                    for poll in wk.get("polls", []):
                        for r in poll.get("ranks", []):
                            school_raw = r.get("school")
                            if not school_raw:
                                continue
                            school_id = import_data.resolve_school(c, school_raw)
                            c.execute(
                                "INSERT INTO cfb_rankings(season, week, season_type, poll, rank, school_id, "
                                "school_name_raw, conference, first_place_votes, points, verification_status, "
                                "source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                (wk.get("season"), wk.get("week"), wk.get("seasonType"), poll.get("poll"),
                                 r.get("rank"), school_id, school_raw, r.get("conference"),
                                 r.get("firstPlaceVotes"), r.get("points"), "SOURCE_BACKED", SOURCE_ID),
                            )
                            total_published += 1
                time.sleep(0.5)
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
                c, table="cfb_rankings", rows_published=total_published, rows_rejected=0,
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
