"""CFB game weather -- Engine-gap-audit operation (CFBD-key-dependent,
Patreon Tier 1+ required on the underlying API key).

Real source, confirmed live before writing any code: CFBD's `/games/weather`
endpoint. This endpoint returned a real, explicit 401 ("requires a Patreon
subscription at Tier 1 or higher") against the free-tier key used to build
every other CFBD-dependent script in this operation -- confirmed genuinely
unblocked only after the user upgraded their Patreon subscription AND
regenerated their API key (the first regenerated key alone was NOT
sufficient; the Patreon-to-CFBD-account link itself needed to actually
process before the same key started working). Real shape confirmed live:
one entry per game -- `id` (matches `cfb_games_canonical.game_id` directly,
same identity scheme, no resolution needed), gameIndoors, temperature,
dewPoint, humidity, precipitation, snowfall, windDirection, windSpeed,
pressure, weatherConditionCode/weatherCondition.

This is a real, additive enrichment of the EXISTING `cfb_games_canonical`
table (never a second, competing games table) -- the same pattern already
used for `cfb_games_postseason_refresh.py`'s bowl/CFP fields.

Cost-conscious default, same real reasoning as every other CFBD-dependent
script in this operation (CFBD's free/paid tiers are a metered API, unlike
nflverse/cfbfastR): a no-args scheduled call only fetches the CURRENT
season, never a full 2002-current resweep every run -- settled historical
seasons don't change. An explicit `seasons=` call is how the real
2002-2025 historical backfill is produced (one deliberate operation, not
the default recurring behavior).
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
DATASET = "cfb_weather"
SOURCE_ID = "CFBD_API_LIVE"
MIN_SEASON = 2002
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year


def _ensure_schema(c) -> None:
    cols = {r["name"] for r in c.execute("PRAGMA table_info(cfb_games_canonical)").fetchall()}
    for name, decl in [
        ("game_indoors", "INTEGER"), ("temperature", "REAL"), ("dew_point", "REAL"),
        ("humidity", "REAL"), ("precipitation", "REAL"), ("snowfall", "REAL"),
        ("wind_direction", "REAL"), ("wind_speed", "REAL"), ("pressure", "REAL"),
        ("weather_condition", "TEXT"),
    ]:
        if name not in cols:
            c.execute(f"ALTER TABLE cfb_games_canonical ADD COLUMN {name} {decl}")
    c.commit()


def run_cfb_weather_refresh(seasons: list[int] | None = None) -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_games_canonical").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    # See module docstring -- current-season-only default, same real
    # metered-API reasoning as every other CFBD-dependent script here.
    target_seasons = seasons if seasons is not None else [MAX_SEASON_ATTEMPT]
    total_matched = total_unmatched = 0
    seasons_done: list[int] = []

    try:
        c = engine_bootstrap.connect()
        c.execute("BEGIN")
        try:
            existing_ids = {r["game_id"] for r in c.execute("SELECT game_id FROM cfb_games_canonical")}
            for season in target_seasons:
                try:
                    rows = _cfbd_client.get("/games/weather", {"year": season})
                except _cfbd_client.CfbdUnavailable:
                    raise
                for g in rows:
                    game_id = str(g.get("id"))
                    if game_id not in existing_ids:
                        total_unmatched += 1
                        continue
                    c.execute(
                        "UPDATE cfb_games_canonical SET game_indoors=?, temperature=?, dew_point=?, "
                        "humidity=?, precipitation=?, snowfall=?, wind_direction=?, wind_speed=?, "
                        "pressure=?, weather_condition=? WHERE game_id=?",
                        (1 if g.get("gameIndoors") else 0, g.get("temperature"), g.get("dewPoint"),
                         g.get("humidity"), g.get("precipitation"), g.get("snowfall"),
                         g.get("windDirection"), g.get("windSpeed"), g.get("pressure"),
                         g.get("weatherCondition"), game_id),
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
