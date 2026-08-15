"""CFB conference standings / season records -- Engine-gap-audit operation
(CFBD-key-dependent).

Real source, confirmed live before writing any code: CFBD's `/records`
endpoint (`GET /records?year={season}`), one call per season returning
every team's real season record -- confirmed real shape: year, teamId,
team, classification, conference, division, expectedWins, and real nested
win/loss/tie breakdowns (total, conferenceGames, homeGames, awayGames,
neutralSiteGames, regularSeason, postseason).

Real, disclosed limitation: this endpoint has NO explicit rank/seed/
standing-position field -- it is season-END win/loss totals, not a
week-by-week standing snapshot (the source pack's own suggested
`fox_cfb_standings()` is an R-only cfbfastR helper, not part of this REST
API at all). Storing the real win/loss breakdowns honestly, rather than
fabricating a "standing" rank CFBD itself doesn't report, matches this
project's `Nulls` rule.

`team` is resolved via `import_data.resolve_school()` -- the same real
fuzzy-normalized match every other CFB importer in this codebase already
uses.

Scope: 2002-2025, matching `cfb_games_canonical`'s own existing real season
range. Surrogate autoincrement id + full delete-and-republish per source
scope (one row per team per season is the real natural shape, but school
resolution failures/edge cases are not worth risking a second silently-
wrong composite-key assumption after the real one found in
nfl_contracts_refresh.py).
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
DATASET = "cfb_standings"
SOURCE_ID = "CFBD_API_LIVE"
MIN_SEASON = 2002
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_standings (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            school_id INTEGER,
            school_name_raw TEXT NOT NULL,
            classification TEXT,
            conference TEXT,
            division TEXT,
            expected_wins REAL,
            total_games INTEGER, total_wins INTEGER, total_losses INTEGER, total_ties INTEGER,
            conf_games INTEGER, conf_wins INTEGER, conf_losses INTEGER, conf_ties INTEGER,
            home_games INTEGER, home_wins INTEGER, home_losses INTEGER, home_ties INTEGER,
            away_games INTEGER, away_wins INTEGER, away_losses INTEGER, away_ties INTEGER,
            postseason_games INTEGER, postseason_wins INTEGER, postseason_losses INTEGER,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id)
        )
    """)
    c.commit()


def _grp(rec: dict, key: str) -> dict:
    return rec.get(key) or {}


def run_cfb_standings_refresh(seasons: list[int] | None = None) -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_standings").fetchone()[0]
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
                "DELETE FROM cfb_standings WHERE source_id=? AND season=?",
                [(SOURCE_ID, s) for s in target_seasons],
            )

            for season in target_seasons:
                try:
                    records = _cfbd_client.get("/records", {"year": season})
                except _cfbd_client.CfbdUnavailable:
                    raise
                for rec in records:
                    team_raw = rec.get("team")
                    if not team_raw:
                        continue
                    school_id = import_data.resolve_school(c, team_raw)
                    total = _grp(rec, "total")
                    conf = _grp(rec, "conferenceGames")
                    home = _grp(rec, "homeGames")
                    away = _grp(rec, "awayGames")
                    post = _grp(rec, "postseason")
                    c.execute(
                        "INSERT INTO cfb_standings(season, school_id, school_name_raw, classification, "
                        "conference, division, expected_wins, total_games, total_wins, total_losses, total_ties, "
                        "conf_games, conf_wins, conf_losses, conf_ties, home_games, home_wins, home_losses, "
                        "home_ties, away_games, away_wins, away_losses, away_ties, postseason_games, "
                        "postseason_wins, postseason_losses, verification_status, source_id) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (season, school_id, team_raw, rec.get("classification"), rec.get("conference"),
                         rec.get("division"), rec.get("expectedWins"),
                         total.get("games"), total.get("wins"), total.get("losses"), total.get("ties"),
                         conf.get("games"), conf.get("wins"), conf.get("losses"), conf.get("ties"),
                         home.get("games"), home.get("wins"), home.get("losses"), home.get("ties"),
                         away.get("games"), away.get("wins"), away.get("losses"), away.get("ties"),
                         post.get("games"), post.get("wins"), post.get("losses"),
                         "SOURCE_BACKED", SOURCE_ID),
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
                c, table="cfb_standings", rows_published=total_published, rows_rejected=0,
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
