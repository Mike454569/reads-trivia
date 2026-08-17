"""Reads Engine Gateway -- admin-triggered NFL/CFB production data refresh.

Thin wrapper around tools/data_refresh/{nfl_refresh,cfb_refresh,
nfl_games_refresh,cfb_games_refresh}.py (the real orchestration --
backup, download, stage, publish, sanity-check, restore-on-failure,
run-tracking) -- this module adds exactly the two things a Gateway route
needs that those scripts don't have on their own:

1. A real refresh can take minutes (network download of a real CSV, a full
   backup-copy of the ~1.6GB Engine DB, staging/publish writes, a sanity
   pass). Running that synchronously inside an HTTP request risks a client
   or reverse-proxy timeout well before the work finishes -- especially the
   Netlify Scheduled Function that triggers this in production, which has
   its own execution-time budget completely separate from however long the
   refresh actually takes. So the route starts the real work as a
   background task and returns immediately; the caller polls
   /v1/admin/refresh/status for the real outcome (same "kick off, then
   poll" shape as any other long-running admin operation in this class of
   system).
2. A GLOBAL concurrency guard -- only ONE refresh runs at a time, across
   ALL datasets, not just per-dataset. Two overlapping runs for the SAME
   dataset would obviously interleave unsafely, but even two DIFFERENT
   datasets running together is real capacity risk here, not just a
   theoretical one: the Gateway machine is a single shared-CPU, 1GB-memory
   box (gateway/fly.toml), and every refresh's backup step copies the full
   ~1.6GB Engine DB -- four datasets firing near-simultaneously (the real
   shape of the scheduled trigger) would mean up to ~6.4GB of concurrent
   file-copy I/O and four Python processes' memory footprint on that same
   1GB machine. refresh_runs already records a real RUNNING row for the
   duration of a run (safety.start_run/finish_run) -- this checks for ANY
   such row before starting a new one, regardless of which dataset it
   belongs to.

Real incident, fixed here: tools/data_refresh/*.py import Engine scripts
(fetch_nflverse_current, import_data, backup_manager) directly from
Reads_Football_Data_Engine_v4.0/ -- a directory mounted from a persistent
volume in production, never baked into the Gateway's Docker image (see
gateway/Dockerfile's own module docstring). A local dev copy of that
directory having every file this module expects is not proof the
PRODUCTION volume does. The first deploy of this module imported
tools.data_refresh at module load time, and since gateway/app.py imports
this module at ITS load time too, one missing file on the production
volume took down the entire Gateway on every boot (a real crash loop,
not a hypothetical). Every tools.data_refresh import below is now LAZY
(deferred until a refresh route is actually called) specifically so that
an admin-only, optional feature can never again prevent the whole app
from starting.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402


def _runners():
    """Lazy import -- see module docstring. Raises ImportError (never
    silently swallowed) if tools.data_refresh's own Engine-script imports
    fail on this deployment; callers (the Gateway routes) turn that into a
    clean SERVICE_UNAVAILABLE response instead of a crash.

    Keyed by dataset_key (the Gateway route's own path segment) -> (module,
    run_fn, league label, real dataset_name stored in refresh_runs)."""
    from tools.data_refresh import (
        cfb_all_america_import, cfb_betting_lines_refresh, cfb_games_postseason_refresh, cfb_games_refresh,
        cfb_pbp_refresh, cfb_player_season_stats_refresh, cfb_rankings_refresh, cfb_refresh,
        cfb_standings_refresh, cfb_weather_refresh, nfl_contracts_refresh, nfl_draft_refresh, nfl_games_refresh,
        nfl_injuries_refresh, nfl_passer_rating_compute, nfl_pbp_refresh, nfl_player_game_stats_refresh,
        nfl_player_stats_refresh, nfl_refresh, nfl_team_game_stats_refresh,
    )

    return {
        "nfl": (nfl_refresh, nfl_refresh.run_nfl_refresh, "NFL", nfl_refresh.DATASET),
        "cfb": (cfb_refresh, cfb_refresh.run_cfb_refresh, "CFB", cfb_refresh.DATASET),
        "nfl_games": (nfl_games_refresh, nfl_games_refresh.run_nfl_games_refresh, "NFL", nfl_games_refresh.DATASET),
        "cfb_games": (cfb_games_refresh, cfb_games_refresh.run_cfb_games_refresh, "CFB", cfb_games_refresh.DATASET),
        # Historical Engine Enrichment operation: draft_facts had no
        # automatic refresh anywhere in this repo (confirmed by grep) and
        # was capped at 2024 -- this closes that gap using the same
        # already-approved NFLVERSE_DATA source.
        "nfl_draft": (nfl_draft_refresh, nfl_draft_refresh.run_nfl_draft_refresh, "NFL", nfl_draft_refresh.DATASET),
        # Historical Engine Enrichment operation, continuation:
        # player_season_stats was completely empty (0 rows) -- the hard
        # blocker on any real 17-0 candidate generation. Closes that gap.
        "nfl_player_stats": (nfl_player_stats_refresh, nfl_player_stats_refresh.run_nfl_player_stats_refresh,
                              "NFL", nfl_player_stats_refresh.DATASET),
        # Master Knowledge Blueprint (02_FIELD_MASTER "Player-Game Stats",
        # 14_CLAUDE_EXECUTION step 3's #1 priority): game-grain stats, real
        # canonical game_id linkage to the `games` table.
        "nfl_player_game_stats": (nfl_player_game_stats_refresh, nfl_player_game_stats_refresh.run_nfl_player_game_stats_refresh,
                                   "NFL", nfl_player_game_stats_refresh.DATASET),
        # Direct user request: a real boxscore for every game, for
        # in-depth specific-game questions. Team-level (not per-player)
        # totals, same real canonical game_id linkage.
        "nfl_team_game_stats": (nfl_team_game_stats_refresh, nfl_team_game_stats_refresh.run_nfl_team_game_stats_refresh,
                                 "NFL", nfl_team_game_stats_refresh.DATASET),
        # Football Knowledge Expansion operation: cfb_player_season_stats_real
        # only covered 2024-2025 and was flagged production_safe=0 pending
        # reconciliation -- this dataset key re-derives and extends it back
        # to 2014 from the same real, already-approved SPORTSDATAVERSE_CFB
        # source, keeping it current going forward too.
        "cfb_player_stats": (cfb_player_season_stats_refresh, cfb_player_season_stats_refresh.run_cfb_player_season_stats_refresh,
                              "CFB", cfb_player_season_stats_refresh.DATASET),
        # Engine-gap-audit operation: five new real domains had real,
        # verified import scripts but were never wired into this dispatcher
        # -- without this, none of them could ever run in production
        # (manually or on a schedule), regardless of `fly deploy`.
        "nfl_contracts": (nfl_contracts_refresh, nfl_contracts_refresh.run_nfl_contracts_refresh,
                           "NFL", nfl_contracts_refresh.DATASET),
        "nfl_injuries": (nfl_injuries_refresh, nfl_injuries_refresh.run_nfl_injuries_refresh,
                          "NFL", nfl_injuries_refresh.DATASET),
        "nfl_pbp": (nfl_pbp_refresh, nfl_pbp_refresh.run_nfl_pbp_refresh, "NFL", nfl_pbp_refresh.DATASET),
        # Derived-only (no external download) -- must run AFTER nfl_player_stats
        # so real pass_interceptions data is fresh before computing ratings
        # from it; scheduled to a later slot in netlify.toml for this reason.
        "nfl_passer_rating": (nfl_passer_rating_compute, nfl_passer_rating_compute.run_nfl_passer_rating_compute,
                               "NFL", nfl_passer_rating_compute.DATASET),
        "cfb_all_america": (cfb_all_america_import, cfb_all_america_import.run_cfb_all_america_import,
                             "CFB", cfb_all_america_import.DATASET),
        # Engine-gap-audit operation, continuation: five more real CFB
        # domains, all CFBD-key-dependent (tools/data_refresh/_cfbd_client.py).
        # Each of these defaults to a CURRENT-SEASON-ONLY refresh when called
        # with no arguments (see each script's own target_seasons comment) --
        # CFBD is a metered, paid API (free tier: 1000 calls/month), unlike
        # every nflverse/cfbfastR source elsewhere in this dispatcher, so a
        # scheduled no-args call must never re-sweep 2002-present on every
        # run. The real 2002-2025 historical backfill is already imported;
        # a further manual backfill is one explicit `seasons=` call away.
        "cfb_betting_lines": (cfb_betting_lines_refresh, cfb_betting_lines_refresh.run_cfb_betting_lines_refresh,
                               "CFB", cfb_betting_lines_refresh.DATASET),
        "cfb_games_postseason": (cfb_games_postseason_refresh, cfb_games_postseason_refresh.run_cfb_games_postseason_refresh,
                                  "CFB", cfb_games_postseason_refresh.DATASET),
        "cfb_pbp": (cfb_pbp_refresh, cfb_pbp_refresh.run_cfb_pbp_refresh, "CFB", cfb_pbp_refresh.DATASET),
        "cfb_rankings": (cfb_rankings_refresh, cfb_rankings_refresh.run_cfb_rankings_refresh,
                          "CFB", cfb_rankings_refresh.DATASET),
        "cfb_standings": (cfb_standings_refresh, cfb_standings_refresh.run_cfb_standings_refresh,
                           "CFB", cfb_standings_refresh.DATASET),
        # Sixth CFBD-dependent domain -- unblocked only after the user
        # upgraded their CFBD Patreon subscription to Tier 1+ AND
        # regenerated their API key (see cfb_weather_refresh.py's own module
        # docstring for the real, confirmed-live sequence this took).
        "cfb_weather": (cfb_weather_refresh, cfb_weather_refresh.run_cfb_weather_refresh,
                         "CFB", cfb_weather_refresh.DATASET),
    }


# Real incident, fixed here: a refresh's BackgroundTask runs inside the
# Gateway's own process, which a `fly deploy` kills and replaces mid-flight
# as a completely ordinary part of a rolling update -- confirmed happening
# in production (a real NFL roster refresh triggered at 01:12:38 UTC was
# still reporting RUNNING 10+ minutes later, right after a deploy, well
# past the ~130-200s that normally takes). Nothing ever calls finish_run()
# for a run killed that way, so without this, that one RUNNING row would
# block EVERY future refresh, forever, via the global guard below -- a
# real, live production bug, not a hypothetical. 30 minutes is comfortably
# above the worst real measured run time (~11m24s for nfl_games_refresh
# against the actual production volume).
STALE_RUNNING_THRESHOLD_MINUTES = 30


def _reclaim_stale_running_rows(c) -> None:
    """Marks any RUNNING row older than the threshold as FAILED_STALE (an
    honest, visible status -- never silently dropped) so the guard below
    can proceed. Self-healing: called at the top of every guard check, not
    a separate cron/admin action someone has to remember to run."""
    from datetime import datetime, timedelta, timezone

    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=STALE_RUNNING_THRESHOLD_MINUTES)).isoformat()
    stale = c.execute("SELECT run_id FROM refresh_runs WHERE status='RUNNING' AND started_at < ?", (cutoff,)).fetchall()
    if not stale:
        return
    now = datetime.now(timezone.utc).isoformat()
    log = '{"failure_reason": "run never reported finished -- reclaimed as stale (likely killed mid-flight by a deploy or machine restart)"}'
    for row in stale:
        c.execute("UPDATE refresh_runs SET status='FAILED_STALE', finished_at=?, log_json=? WHERE run_id=?",
                   (now, log, row["run_id"]))
    c.commit()


def _running_row(league: str | None, dataset: str | None) -> bool:
    """league=None/dataset=None means 'is ANYTHING running' (the global
    guard below) -- a bare SELECT with no WHERE-narrowing on those columns.
    Real, measured reason this exists as a GLOBAL guard, not just
    per-dataset: the Gateway machine is a single shared-CPU, 1GB-memory box
    (see gateway/fly.toml's own resource-sizing notes), and each refresh
    run's backup step copies the full ~1.6GB Engine DB. Four datasets
    refreshing concurrently (the real shape of the scheduled trigger, which
    fires one HTTP call per dataset in quick succession -- each returns
    immediately since the actual work is backgrounded, so nothing about
    that loop being 'sequential' from the caller's side serializes the
    underlying work) would mean up to ~6.4GB of simultaneous file-copy I/O
    and four concurrent Python processes' memory footprint on that same 1GB
    machine -- never measured as safe, so never allowed. One refresh at a
    time, full stop, regardless of dataset."""
    from tools.data_refresh import safety

    c = engine_bootstrap.connect()
    try:
        safety.ensure_refresh_tables(c)
        _reclaim_stale_running_rows(c)
        sql = "SELECT 1 FROM refresh_runs WHERE status='RUNNING'"
        params: tuple = ()
        if league is not None:
            sql += " AND league=? AND dataset_name=?"
            params = (league, dataset)
        row = c.execute(sql + " LIMIT 1", params).fetchone()
        return row is not None
    finally:
        c.close()


def check_can_start(dataset_key: str) -> dict:
    """dataset_key is one of 'nfl', 'cfb', 'nfl_games', 'cfb_games' (the
    Gateway route's own path segment, kept distinct from the real league
    label stored in refresh_runs). Pure status check -- does NOT start
    anything; the route handler schedules the actual background task
    itself (via run_fn_for) only when this returns status=OK, so this
    function never needs to hand back a raw callable inside a dict a
    caller might otherwise be tempted to serialize."""
    runners = _runners()
    if dataset_key not in runners:
        raise ValueError(f"unknown dataset_key: {dataset_key!r}")
    _, _, league, dataset = runners[dataset_key]
    if _running_row(None, None):  # global guard -- see _running_row's docstring
        return {"status": "ALREADY_RUNNING", "league": league, "dataset": dataset}
    return {"status": "OK", "league": league, "dataset": dataset}


def run_fn_for(dataset_key: str):
    """The real, synchronous, potentially multi-minute refresh function for
    this dataset -- callers pass this to FastAPI's BackgroundTasks, never
    call it inline inside a request handler (see module docstring)."""
    _, run_fn, _, _ = _runners()[dataset_key]
    return run_fn


def _safe_run_summary(run: Optional[dict]) -> Optional[dict]:
    """Never leaks a raw filesystem path (backup path, DB path) or the full
    log_json blob (which can legitimately contain an exception repr with
    internal detail) to a client -- admin-gated or not, this response can
    end up in a browser devtools panel, so the same "safe subset only"
    discipline as every other admin diagnostic route in this Gateway
    applies here too. The one exception is identity_bridge_status (NFL
    roster runs only) -- a short, pre-classified string (never a raw
    stderr blob), deliberately surfaced since a silently-failing identity
    bridge is exactly the kind of thing an admin freshness view exists to
    catch (see nfl_refresh.py's own module comment on the real, disclosed
    legacy-ID-collision failure mode)."""
    if not run:
        return None
    summary = {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "rows_downloaded": run.get("rows_downloaded"),
        "rows_imported": run.get("rows_imported"),
        "rows_rejected": run.get("rows_rejected"),
        "no_op": bool(run.get("no_op")),
    }
    import json as _json
    try:
        log = _json.loads(run.get("log_json") or "{}")
    except (TypeError, ValueError):
        log = {}
    if "identity_bridge_status" in log:
        summary["identity_bridge_status"] = log["identity_bridge_status"]
    return summary


def refresh_status() -> dict:
    runners = _runners()
    return {
        "nfl": {
            "rosters": _safe_run_summary(runners["nfl"][0].last_run_status()),
            "games": _safe_run_summary(runners["nfl_games"][0].last_run_status()),
            "draft": _safe_run_summary(runners["nfl_draft"][0].last_run_status()),
            "player_stats": _safe_run_summary(runners["nfl_player_stats"][0].last_run_status()),
            "player_game_stats": _safe_run_summary(runners["nfl_player_game_stats"][0].last_run_status()),
            "team_game_stats": _safe_run_summary(runners["nfl_team_game_stats"][0].last_run_status()),
            "contracts": _safe_run_summary(runners["nfl_contracts"][0].last_run_status()),
            "injuries": _safe_run_summary(runners["nfl_injuries"][0].last_run_status()),
            "pbp": _safe_run_summary(runners["nfl_pbp"][0].last_run_status()),
            "passer_rating": _safe_run_summary(runners["nfl_passer_rating"][0].last_run_status()),
        },
        "cfb": {
            "rosters": _safe_run_summary(runners["cfb"][0].last_run_status()),
            "games": _safe_run_summary(runners["cfb_games"][0].last_run_status()),
            "player_stats": _safe_run_summary(runners["cfb_player_stats"][0].last_run_status()),
            "all_america": _safe_run_summary(runners["cfb_all_america"][0].last_run_status()),
            "betting_lines": _safe_run_summary(runners["cfb_betting_lines"][0].last_run_status()),
            "games_postseason": _safe_run_summary(runners["cfb_games_postseason"][0].last_run_status()),
            "pbp": _safe_run_summary(runners["cfb_pbp"][0].last_run_status()),
            "rankings": _safe_run_summary(runners["cfb_rankings"][0].last_run_status()),
            "standings": _safe_run_summary(runners["cfb_standings"][0].last_run_status()),
            "weather": _safe_run_summary(runners["cfb_weather"][0].last_run_status()),
        },
    }
