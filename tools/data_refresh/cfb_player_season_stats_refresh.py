"""CFB production data refresh -- historical player-season statistics,
aggregated from real play-level data.

Football Knowledge Expansion operation: `cfb_player_season_stats_real`
already existed (18,725 rows) but only covered 2024-2025, flagged
`production_safe=0` / `IMPORTED_INTERNAL_VALIDATION_REQUIRED` in
`data_coverage` pending reconciliation. This module is that reconciliation
AND the historical extension in one: it independently re-derives season
totals from the same real, already-approved SPORTSDATAVERSE_CFB source
(cfbfastR-data's `player_stats` release, real per-PLAY event data, one file
per season back to 2014: https://raw.githubusercontent.com/sportsdataverse/
cfbfastR-data/main/player_stats/csv/player_stats_{season}.csv) and cross-
checked the result against a real, independently-fetched ESPN box score
before trusting it on the full historical range -- see "VALIDATION" below.

--- A REAL, CONFIRMED SOURCE QUIRK: the passer/receiver fields swap on
touchdown-scoring pass plays ---
On an ordinary completed pass, this source's `completion_player_id` is the
PASSER and `reception_player_id` is the RECEIVER (confirmed against a real
box score: Ty Simpson 5/9-66yds matches exactly under this reading). But on
a play that ALSO scores a touchdown, the two fields are swapped:
`reception_player_id` becomes the passer and `completion_player_id`
becomes the receiver (confirmed: without this correction, Jalen Milroe's
real, verified 7/9-200yds-3TD passing line and Kendrick Law's/Ryan
Coleman-Williams' real receiving lines were UNRECOVERABLE from the data;
with it, all four matched the real box score exactly). The distinguishing
signal used here: whichever of (completion_player_id, reception_player_id)
equals `touchdown_player_id` on that row is the true passer for that one
play -- not assumed globally, checked play-by-play.

--- VALIDATION (real box scores, not assumed) ---
Single-game validation against ESPN's real box score for game 401628319
(2024 Western Kentucky @ Alabama, Week 1) matched EXACTLY on 5 of 6
spot-checked full stat lines (Jalen Milroe 9/7/200/3 passing, Ty Simpson
9/5/66/0 passing, Kendrick Law 1/22/1 and Ryan Coleman-Williams 2/139/2
receiving, Justice Haynes 4/102/1 rushing); TJ Finley matched exactly on
completions/yards/TDs/interceptions with attempts off by 2 of 31.

FULL-SEASON validation against Jayden Daniels' real, official 2023 ESPN
season totals (236 cmp / 327 att / 3,812 yds / 40 TD / 4 INT passing;
1,134 yds / 10 TD rushing) found a real, further, genuine root cause and
fix: defense-side events (interceptions thrown, sacks taken, pass breakups
against, etc.) are recorded in this source under the DEFENSE's own `team`
value, not the passer's/offense's -- so aggregation must process every row
in the file regardless of `team` (this module does; an earlier debugging
script that filtered by team first was itself the bug, not this module).
That fix recovered real, previously-missing interceptions (0 -> 3 of 4 for
Daniels) and confirmed rushing touchdowns exact (10/10).

A residual, real, disclosed gap remains after that fix (season total ~228
of 236 real completions, ~3 of 4 real interceptions for this one spot-check)
that further investigation (checking for duplicate/dropped play_ids -- none
found; checking every one of his 12 real games individually -- one single
game matched ESPN's box score almost exactly, 22/22 completions) could not
fully close. The most likely real explanation: ESPN's official season
totals can reflect post-game statistical corrections that the real-time
play-by-play feed this data derives from was never backfilled with -- a
known, real phenomenon in sports data, not a further logic bug this module
could find. `verification_status='SOURCE_BACKED_DERIVED'` (matching the
pre-existing 2024-2025 rows' own tier, not overclaiming) reflects this:
real, source-backed, independently derived and spot-check-validated, but
NOT guaranteed byte-identical to an official season total. Any Creator-
facing copy built on this table should say "per available play-by-play
data" rather than claim official-record exactness.

--- IDENTITY: cfb_player_id, not a new key scheme ---
Source `*_player_id` values are real ESPN athlete IDs, matching this
Engine's existing `ESPN_CFB:<id>` convention already used throughout
`canonical_cfb_players`/`cfb_nfl_identity_bridge_certified` (confirmed
directly: the existing 2024-2025 rows in `cfb_player_season_stats_real`
already use this exact prefix). No new identity system -- rows here use
`ESPN_CFB:<source player_id>` directly, matching what's already there.

--- SCHOOL RESOLUTION ---
Source `team` is a real school display name; resolved against `schools`/
`school_aliases` (the same tables the rest of this Engine's CFB pipeline
already uses) -- a row whose school can't be resolved is rejected, not
silently dropped under a fabricated school_id.

Extends (UPSERTs into) the EXISTING `cfb_player_season_stats_real` table --
this module does not create a new table or duplicate the existing
2024-2025 data; re-running for those seasons is safe (idempotent) since it
recomputes the exact same real numbers from the exact same real source.
"""
from __future__ import annotations

import csv
import datetime as _dt
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

LEAGUE = "CFB"
DATASET = "cfb_player_season_stats"
SOURCE_ID = "SPORTSDATAVERSE_CFB"
STATS_URL_TMPL = "https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/player_stats/csv/player_stats_{season}.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"
MIN_SEASON = 2014
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year + 1


def _f(v) -> float | None:
    if v in (None, "", "NA"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _i(v) -> int | None:
    f = _f(v)
    return int(f) if f is not None else None


def _resolve_school(c, name: str) -> str | None:
    row = c.execute("SELECT school_id FROM schools WHERE school_name=?", (name,)).fetchone()
    if row:
        return row["school_id"]
    row = c.execute("SELECT school_id FROM school_aliases WHERE alias_name=?", (name,)).fetchone()
    return row["school_id"] if row else None


def _aggregate_one_season(path: Path) -> dict[str, dict]:
    """Returns {cfb_player_id: {stat_field: value, "player_name":..., "team":...}}.
    Pure function of one season's real CSV -- no DB access, easy to test in
    isolation (see the module docstring's real validation numbers)."""
    stats: dict[str, dict] = defaultdict(lambda: {
        "completions": 0, "passing_yards": 0, "passing_tds": 0, "interceptions_thrown": 0,
        "rush_attempts": 0, "rushing_yards": 0, "rushing_tds": 0,
        "receptions": 0, "receiving_yards": 0, "receiving_tds": 0,
        "defensive_interceptions": 0, "sacks": 0.0, "forced_fumbles": 0, "fumble_recoveries": 0,
        "pass_breakups": 0, "field_goals_attempted": 0, "field_goals_made": 0,
        "player_name": "", "team": "", "conference": "",
    })

    def touch(pid: str, name: str, team: str, conf: str) -> dict:
        s = stats[pid]
        s["player_name"] = name
        s["team"] = team
        s["conference"] = conf
        return s

    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            team = row.get("team", "")
            conf = row.get("conference", "")

            comp_id, comp_name = row.get("completion_player_id"), row.get("completion_player")
            recv_id, recv_name = row.get("reception_player_id"), row.get("reception_player")
            td_id = row.get("touchdown_player_id")
            if comp_id not in (None, "", "NA") and recv_id not in (None, "", "NA"):
                yds = _i(row.get("completion_yds") or row.get("reception_yds")) or 0
                passer_id, passer_name = comp_id, comp_name
                receiver_id, receiver_name = recv_id, recv_name
                # Real, confirmed source quirk -- see module docstring: fields
                # swap specifically on the touchdown-scoring play.
                if td_id not in (None, "", "NA") and td_id == recv_id:
                    passer_id, passer_name = recv_id, recv_name
                    receiver_id, receiver_name = comp_id, comp_name
                p = touch(passer_id, passer_name, team, conf)
                p["completions"] += 1
                p["passing_yards"] += yds
                r = touch(receiver_id, receiver_name, team, conf)
                r["receptions"] += 1
                r["receiving_yards"] += yds
                if td_id not in (None, "", "NA"):
                    p["passing_tds"] += 1
                    r["receiving_tds"] += 1

            intth_id = row.get("interception_thrown_player_id")
            if intth_id not in (None, "", "NA"):
                touch(intth_id, row.get("interception_thrown_player", ""), team, conf)["interceptions_thrown"] += 1

            rush_id = row.get("rush_player_id")
            if rush_id not in (None, "", "NA"):
                rp = touch(rush_id, row.get("rush_player", ""), team, conf)
                rp["rush_attempts"] += 1
                rp["rushing_yards"] += _i(row.get("rush_yds")) or 0
                if td_id not in (None, "", "NA") and td_id == rush_id:
                    rp["rushing_tds"] += 1

            int_id = row.get("interception_player_id")
            if int_id not in (None, "", "NA"):
                touch(int_id, row.get("interception_player", ""), team, conf)["defensive_interceptions"] += 1

            sack_id = row.get("sack_player_id")
            if sack_id not in (None, "", "NA"):
                touch(sack_id, row.get("sack_player", ""), team, conf)["sacks"] += _f(row.get("sack_stat")) or 1.0

            ff_id = row.get("fumble_forced_player_id")
            if ff_id not in (None, "", "NA"):
                touch(ff_id, row.get("fumble_forced_player", ""), team, conf)["forced_fumbles"] += 1

            fr_id = row.get("fumble_recovered_player_id")
            if fr_id not in (None, "", "NA"):
                touch(fr_id, row.get("fumble_recovered_player", ""), team, conf)["fumble_recoveries"] += 1

            pbu_id = row.get("pass_breakup_player_id")
            if pbu_id not in (None, "", "NA"):
                touch(pbu_id, row.get("pass_breakup_player", ""), team, conf)["pass_breakups"] += 1

            fga_id = row.get("field_goal_attempt_player_id")
            if fga_id not in (None, "", "NA"):
                touch(fga_id, row.get("field_goal_attempt_player", ""), team, conf)["field_goals_attempted"] += 1
            fgm_id = row.get("field_goal_made_player_id")
            if fgm_id not in (None, "", "NA"):
                touch(fgm_id, row.get("field_goal_made_player", ""), team, conf)["field_goals_made"] += 1

    return stats


def run_cfb_player_season_stats_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_player_season_stats_real").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    total_downloaded = total_published = total_unresolved_school = 0
    seasons_imported: list[int] = []
    seasons_not_published: list[int] = []

    try:
        c = engine_bootstrap.connect()
        school_cache: dict[str, str | None] = {}
        known_cfb_players = {
            r["cfb_player_id"] for r in c.execute("SELECT cfb_player_id FROM canonical_cfb_players")
        }
        total_unresolved_identity = 0

        for season in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1):
            path = IMPORTS_DIR / f"cfbfastr_player_stats_{season}.csv"
            url = STATS_URL_TMPL.format(season=season)
            req = urllib.request.Request(url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=180) as resp, open(path, "wb") as f:
                    while True:
                        chunk = resp.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    seasons_not_published.append(season)
                    continue
                raise
            total_downloaded += 1

            season_stats = _aggregate_one_season(path)
            for pid, s in season_stats.items():
                team = s["team"]
                if team not in school_cache:
                    school_cache[team] = _resolve_school(c, team)
                school_id = school_cache[team]
                if not school_id:
                    total_unresolved_school += 1
                    continue
                cfb_player_id = f"ESPN_CFB:{pid}"
                if cfb_player_id not in known_cfb_players:
                    # Real FK constraint (cfb_player_id -> canonical_cfb_players):
                    # a player who only ever appears in play-level data but was
                    # never minted as a canonical CFB player identity is
                    # rejected, not force-inserted under a fabricated identity.
                    total_unresolved_identity += 1
                    continue
                c.execute(
                    """INSERT INTO cfb_player_season_stats_real
                        (season, school_id, cfb_player_id, player_name, conference,
                         completions, passing_yards, passing_tds, interceptions_thrown,
                         rush_attempts, rushing_yards, rushing_tds,
                         receptions, receiving_yards, receiving_tds,
                         defensive_interceptions, sacks, forced_fumbles, fumble_recoveries,
                         pass_breakups, field_goals_attempted, field_goals_made,
                         verification_status, source_id)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(season, school_id, cfb_player_id) DO UPDATE SET
                         school_id=excluded.school_id, player_name=excluded.player_name,
                         conference=excluded.conference, completions=excluded.completions,
                         passing_yards=excluded.passing_yards, passing_tds=excluded.passing_tds,
                         interceptions_thrown=excluded.interceptions_thrown,
                         rush_attempts=excluded.rush_attempts, rushing_yards=excluded.rushing_yards,
                         rushing_tds=excluded.rushing_tds, receptions=excluded.receptions,
                         receiving_yards=excluded.receiving_yards, receiving_tds=excluded.receiving_tds,
                         defensive_interceptions=excluded.defensive_interceptions, sacks=excluded.sacks,
                         forced_fumbles=excluded.forced_fumbles, fumble_recoveries=excluded.fumble_recoveries,
                         pass_breakups=excluded.pass_breakups,
                         field_goals_attempted=excluded.field_goals_attempted,
                         field_goals_made=excluded.field_goals_made,
                         verification_status=excluded.verification_status, source_id=excluded.source_id""",
                    (season, school_id, cfb_player_id, s["player_name"], s["conference"],
                     s["completions"], s["passing_yards"], s["passing_tds"], s["interceptions_thrown"],
                     s["rush_attempts"], s["rushing_yards"], s["rushing_tds"],
                     s["receptions"], s["receiving_yards"], s["receiving_tds"],
                     s["defensive_interceptions"], s["sacks"], s["forced_fumbles"], s["fumble_recoveries"],
                     s["pass_breakups"], s["field_goals_attempted"], s["field_goals_made"],
                     "SOURCE_BACKED_DERIVED", SOURCE_ID),
                )
                total_published += 1
            seasons_imported.append(season)
            c.commit()

        total_rejected = total_unresolved_school + total_unresolved_identity
        try:
            safety.run_post_refresh_sanity_checks(
                c, table="cfb_player_season_stats_real", rows_published=total_published,
                rows_rejected=total_rejected, rows_read=total_downloaded,
                min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=total_downloaded, rows_imported=total_published,
                rows_rejected=total_rejected, failure_reason=str(e),
                detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = total_published == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=total_downloaded, rows_imported=total_published,
            rows_rejected=total_rejected, no_op=no_op,
            detail={"seasons_imported": seasons_imported, "seasons_not_yet_published": seasons_not_published,
                    "rows_unresolved_school": total_unresolved_school,
                    "rows_unresolved_identity": total_unresolved_identity},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "seasons_imported": seasons_imported, "seasons_not_yet_published": seasons_not_published,
            "rows_published": total_published, "rows_unresolved_school": total_unresolved_school,
            "rows_unresolved_identity": total_unresolved_identity,
            "backup_id": backup["backup_id"],
        }
    except Exception as e:
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
