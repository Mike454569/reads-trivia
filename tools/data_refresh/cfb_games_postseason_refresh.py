"""CFB season_type + bowl/CFP game identification -- Engine-gap-audit
operation (CFBD-key-dependent).

Real, pre-existing bug found before building (not introduced here):
`cfb_games_canonical` has no `season_type` column at all, and CFBD's own
week numbering RESETS for postseason (week 1 = the first bowl week) --
confirmed directly: `game_id=401677192` (the real 2025-01-20 CFP National
Championship, Notre Dame vs Ohio State) and a real 2024-08-24 regular-season
opener are BOTH stored as `season=2024, week=1` with nothing to tell them
apart. Any existing capability reasoning about "week" for a CFB game is
currently ambiguous between an early regular-season week and a championship
game sharing the same nominal week number. This module is a real, additive
enrichment of the EXISTING table (never a second, competing games table) --
matched by the real, already-identical CFBD `game.id`
(`cfb_games_canonical.game_id` was confirmed live to already use this exact
numeric ID scheme, since both it and this API trace back to the same
underlying CFBD data).

New columns: `season_type` ('regular'/'postseason'), `bowl_name` (CFBD's own
`notes` field, e.g. "Cricket Celebration Bowl" -- the real event name, never
inferred from date), and the CFP-specific structured fields CFBD exposes on
`playoff` for actual College Football Playoff games (`is_playoff`,
`playoff_round`, `playoff_round_name`, `playoff_bracket_slot`, `home_seed`,
`away_seed`) -- all real, verbatim from the source, NULL for any
non-playoff game (a regular bowl has `playoff=null`; do not fabricate a
round/seed for it).

Scope: 2002-2025, matching `cfb_games_canonical`'s own existing real season
range (confirmed via `SELECT MIN(season), MAX(season)`) -- never reaching
into CFBD seasons this Engine doesn't already have games for.
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
DATASET = "cfb_games_postseason"
SOURCE_ID = "CFBD_API_LIVE"
MIN_SEASON = 2002
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year


def _ensure_schema(c) -> None:
    cols = {r["name"] for r in c.execute("PRAGMA table_info(cfb_games_canonical)").fetchall()}
    for name, decl in [
        ("season_type", "TEXT"), ("bowl_name", "TEXT"), ("is_playoff", "INTEGER"),
        ("playoff_round", "TEXT"), ("playoff_round_name", "TEXT"), ("playoff_bracket_slot", "TEXT"),
        ("home_seed", "INTEGER"), ("away_seed", "INTEGER"),
    ]:
        if name not in cols:
            c.execute(f"ALTER TABLE cfb_games_canonical ADD COLUMN {name} {decl}")
    c.commit()


def run_cfb_games_postseason_refresh(seasons: list[int] | None = None) -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_games_canonical").fetchone()[0]
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
    total_matched = total_unmatched = 0
    seasons_done: list[int] = []
    seasons_unavailable: list[int] = []

    try:
        c = engine_bootstrap.connect()
        c.execute("BEGIN")
        try:
            existing_ids = {r["game_id"] for r in c.execute("SELECT game_id FROM cfb_games_canonical")}
            for season in target_seasons:
                for season_type in ("regular", "postseason"):
                    try:
                        games = _cfbd_client.get("/games", {"year": season, "seasonType": season_type})
                    except _cfbd_client.CfbdUnavailable:
                        seasons_unavailable = target_seasons
                        raise
                    for g in games:
                        game_id = str(g["id"])
                        if game_id not in existing_ids:
                            total_unmatched += 1
                            continue
                        pf = g.get("playoff") or {}
                        c.execute(
                            "UPDATE cfb_games_canonical SET season_type=?, bowl_name=?, is_playoff=?, "
                            "playoff_round=?, playoff_round_name=?, playoff_bracket_slot=?, "
                            "home_seed=?, away_seed=? WHERE game_id=?",
                            (season_type, g.get("notes") or None, 1 if pf else 0,
                             pf.get("round"), pf.get("roundName"), pf.get("bracketSlot"),
                             pf.get("homeSeed"), pf.get("awaySeed"), game_id),
                        )
                        total_matched += 1
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
                c, table="cfb_games_canonical", rows_published=total_matched, rows_rejected=0,
                rows_read=total_matched + total_unmatched, min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_imported=total_matched, failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"], rows_imported=total_matched,
            no_op=(total_matched == 0),
            detail={"seasons_done": seasons_done, "rows_unmatched_to_existing_game": total_unmatched},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "rows_matched": total_matched,
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
