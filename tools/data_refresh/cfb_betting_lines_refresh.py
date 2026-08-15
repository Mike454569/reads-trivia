"""CFB betting lines -- Engine-gap-audit operation (CFBD-key-dependent).

Real source, confirmed live before writing any code: CFBD's `/lines`
endpoint (`GET /lines?year={season}`), one call per season. Confirmed real
shape: one entry per game (`id` = the same real CFBD game id already used
as `cfb_games_canonical.game_id` -- a direct join, no identity resolution
needed) with a nested `lines[]` array, one row per real sportsbook provider
(DraftKings, Bovada, etc.), each with spread/overUnder/moneyline fields --
real per-provider values are kept distinct, never averaged or collapsed
into one number (this project's own established discipline: never invent a
single "the odds" figure when multiple real, disclosed sources disagree).

Only games with a matching row already in `cfb_games_canonical` are
published -- an unmatched game_id is logged, never guessed at via a
secondary join.

Scope: 2002-2025, matching `cfb_games_canonical`'s own existing real season
range. Surrogate autoincrement id + full delete-and-republish per source
scope (one real game can have several provider rows, so no natural
single-column key exists).
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

LEAGUE = "CFB"
DATASET = "cfb_betting_lines"
SOURCE_ID = "CFBD_API_LIVE"
MIN_SEASON = 2002
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_betting_lines (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            provider TEXT NOT NULL,
            spread REAL,
            spread_open REAL,
            over_under REAL,
            over_under_open REAL,
            home_moneyline INTEGER,
            away_moneyline INTEGER,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id)
        )
    """)
    c.commit()


def run_cfb_betting_lines_refresh(seasons: list[int] | None = None) -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_betting_lines").fetchone()[0]
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
    total_published = total_unmatched = 0
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
                "DELETE FROM cfb_betting_lines WHERE source_id=? AND season=?",
                [(SOURCE_ID, s) for s in target_seasons],
            )

            existing_game_ids = {r["game_id"] for r in c.execute("SELECT game_id FROM cfb_games_canonical")}
            for season in target_seasons:
                try:
                    games = _cfbd_client.get("/lines", {"year": season})
                except _cfbd_client.CfbdUnavailable:
                    raise
                for g in games:
                    game_id = str(g["id"])
                    if game_id not in existing_game_ids:
                        total_unmatched += 1
                        continue
                    for ln in g.get("lines", []):
                        provider = ln.get("provider")
                        if not provider:
                            continue
                        c.execute(
                            "INSERT INTO cfb_betting_lines(game_id, season, provider, spread, spread_open, "
                            "over_under, over_under_open, home_moneyline, away_moneyline, verification_status, "
                            "source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (game_id, season, provider, ln.get("spread"), ln.get("spreadOpen"),
                             ln.get("overUnder"), ln.get("overUnderOpen"), ln.get("homeMoneyline"),
                             ln.get("awayMoneyline"), "SOURCE_BACKED", SOURCE_ID),
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
                c, table="cfb_betting_lines", rows_published=total_published, rows_rejected=0,
                rows_read=total_published + total_unmatched, min_row_count_floor=baseline_count,
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
            no_op=(total_published == 0),
            detail={"seasons_done": seasons_done, "rows_unmatched_to_existing_game": total_unmatched},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "rows_imported": total_published,
            "rows_unmatched_to_existing_game": total_unmatched, "seasons_done": seasons_done,
            "backup_id": backup["backup_id"],
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
