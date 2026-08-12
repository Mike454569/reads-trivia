"""NFL production data refresh -- players + current-season rosters.

Orchestrates the EXISTING, already-tested importer
(Reads_Football_Data_Engine_v4.0/fetch_nflverse_current.py ->
import_data.py) with the new safety layer (safety.py): verified backup
before, real sanity checks after, automatic restore-from-backup if those
checks fail. Never reimplements the download or staging/publish logic --
imports and calls the real functions those existing modules already expose.

Real source, unchanged from the existing importer: nflverse-data's GitHub
releases (players.csv, roster_<year>.csv) -- publicly documented, already
`approved_for_import=1` in the `sources` table (NFLVERSE_PLAYERS,
NFLVERSE_ROSTERS).

Deliberately does NOT call identity_bridge_v16.py (an earlier version of
this module did, and it real-world crashed -- see the UNIFIED ENGINE v4.0
audit, Section on identity bridge refresh). Two real findings, direct DB
inspection, not assumed:
  1. identity_bridge_v16.py writes to cross_league_identity_bridge_v16
     (107 rows) -- a DIFFERENT, much smaller table than
     cfb_nfl_identity_bridge_certified (2,542 rows), the one Lineup/Coach
     Connections actually query. Nothing in this repo currently writes to
     cfb_nfl_identity_bridge_certified at all -- its 2,542 rows all share
     the exact same promoted_at timestamp (2026-08-11T18:17:03Z), meaning
     it was a one-time bulk promotion by a process that no longer exists
     here, not a re-runnable pipeline.
  2. identity_bridge_v16.py also reliably crashes (real, uncaught
     sqlite3.IntegrityError on canonical_players.gsis_id) whenever a bridge
     match lands on any of the ~11,040 canonical_players rows from an older
     `PFR:<id>`-keyed import convention that already carry a gsis_id -- its
     own INSERT only upserts on a player_id conflict, not a gsis_id one.
  Calling a script that (a) doesn't feed the table production actually
  uses and (b) crashes on real data would add nothing but noise/failure
  reports to every refresh run, so this orchestrator stops calling it.
  Refreshing the REAL certified bridge remains a genuine, disclosed gap --
  see the freshness status report -- not something silently faked here by
  re-running the wrong script and calling it done.
"""
from __future__ import annotations

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
import fetch_nflverse_current  # noqa: E402  Engine's own real fetch+import orchestration, reused as-is

LEAGUE = "NFL"
DATASET = "players_and_rosters"


def _current_seasons() -> list[int]:
    # Real, not arbitrary: the current calendar year (the season that would
    # be active or about to start) plus the prior year, so a refresh run
    # near a season boundary still catches late roster moves on last
    # season's file too. Matches fetch_nflverse_current.py's own default
    # range in spirit (it defaults to 2020-2026) without hardcoding an
    # eventually-stale upper bound.
    year = _dt.datetime.now(_dt.timezone.utc).year
    return [year - 1, year]


def run_nfl_refresh(*, seasons: list[int] | None = None) -> dict:
    seasons = seasons or _current_seasons()

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    baseline_players = c.execute("SELECT COUNT(*) FROM canonical_players").fetchone()[0]
    baseline_rosters = c.execute("SELECT COUNT(*) FROM canonical_roster_seasons").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id="NFLVERSE_PLAYERS")
    c.close()

    backup = safety.create_verified_backup()

    try:
        players_meta = fetch_nflverse_current.download(
            fetch_nflverse_current.PLAYERS_URL, fetch_nflverse_current.IMPORTS / "nflverse_players.csv"
        )
        players_meta["import"] = fetch_nflverse_current.run_import(
            "nflverse_players", fetch_nflverse_current.IMPORTS / "nflverse_players.csv"
        )

        roster_metas = []
        for season in seasons:
            p = fetch_nflverse_current.IMPORTS / f"roster_{season}.csv"
            meta = fetch_nflverse_current.download(fetch_nflverse_current.ROSTER_URL.format(season=season), p)
            meta["import"] = fetch_nflverse_current.run_import("nflverse_rosters", p)
            roster_metas.append(meta)

        # No identity-bridge step here -- see module docstring for the real,
        # measured reason (identity_bridge_v16.py doesn't feed the table
        # production actually uses, and crashes on real data besides).
        identity_bridge_status = "NOT_ATTEMPTED_NO_REUSABLE_BUILDER"

        c = engine_bootstrap.connect()
        # rows_downloaded/_imported/_rejected are pulled from import_batches directly (import_data.py
        # already recorded them durably there) rather than re-parsing subprocess stdout.
        recent_batches = c.execute(
            "SELECT rows_read, rows_published, rows_rejected FROM import_batches "
            "WHERE dataset_name IN ('nflverse_players','nflverse_rosters') AND status='PUBLISHED' "
            "ORDER BY started_at DESC LIMIT ?",
            (1 + len(seasons),),
        ).fetchall()
        total_downloaded = sum(r["rows_read"] or 0 for r in recent_batches)
        total_imported = sum(r["rows_published"] or 0 for r in recent_batches)
        total_rejected = sum(r["rows_rejected"] or 0 for r in recent_batches)

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="canonical_roster_seasons", rows_published=total_imported,
                rows_rejected=total_rejected, rows_read=total_downloaded,
                # Never allowed to drop below what was already there -- a refresh
                # is additive/corrective, never a legitimate way to lose rows.
                min_row_count_floor=baseline_rosters,
            )
            player_count_after = c.execute("SELECT COUNT(*) FROM canonical_players").fetchone()[0]
            if player_count_after < baseline_players:
                raise safety.SanityCheckFailure(
                    f"canonical_players dropped from {baseline_players} to {player_count_after} -- refusing"
                )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=total_downloaded, rows_imported=total_imported, rows_rejected=total_rejected,
                failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = total_imported == 0 and total_rejected == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=total_downloaded, rows_imported=total_imported, rows_rejected=total_rejected,
            no_op=no_op, detail={"seasons": seasons, "identity_bridge_status": identity_bridge_status},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "rows_downloaded": total_downloaded, "rows_imported": total_imported, "rows_rejected": total_rejected,
            "seasons": seasons, "backup_id": backup["backup_id"],
            "identity_bridge_status": identity_bridge_status,
        }
    except Exception as e:
        # Any unexpected failure (network error, malformed CSV the staging
        # layer itself didn't catch, etc.) -- fail closed, restore, never
        # leave production in a half-updated or unknown state.
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
