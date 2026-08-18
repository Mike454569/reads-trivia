"""NFL defensive play-by-play identity + real drive-level data (Knowledge
Expansion Batch 4), sourced from nflverse's OWN full play-by-play release
(https://github.com/nflverse/nflverse-data/releases/tag/pbp) -- the exact
same NFLVERSE_DATA source `nfl_plays` already uses, just a wider column
set than the reduced subset originally imported into that table. No new
source, no new identity system -- this batch simply pulls more columns
out of the same real upstream release.

--- WHY nfl_plays ITSELF WASN'T RE-IMPORTED ---
`nfl_plays` (1,279,628 rows) already has real, structured, working offense-
side identity and core fields. Re-importing it wholesale would duplicate
data for no reason. Instead this module adds two NEW, narrow, indexed
tables keyed back to the exact same `(game_id, play_id)` pair `nfl_plays`
already uses, holding only the columns that were missing: defensive-event
identity and drive summaries.

--- KNOWN, HARMLESS DATA-HYGIENE NOTE ---
`csv.DictReader` returns `''` (not `None`) for an empty CSV cell, so the
raw `*_gsis`/`*_name_raw` provenance-tracking columns hold `''` rather
than SQL NULL on a row where that specific sub-event (e.g. a row that has
an interception but no sack) didn't occur. This does NOT affect the
resolved `*_player_id` relationship columns actually used by
tools/quiz_export/nfl_defense_drive_facts.py (`_res()` below explicitly
treats `''` as falsy before the canonical_players lookup) -- callers
reading the raw tracking columns directly should check
`col IS NOT NULL AND col != ''`, which `defensive_identity_coverage()`
already does.

--- DEFENSIVE IDENTITY: REAL GSIS IDS, NOT NAME-PARSING ---
`sack_player_id`, `interception_player_id`, `forced_fumble_player_1/2_
player_id`, `fumble_recovery_1/2_player_id`, `kicker_player_id`,
`punt_returner_player_id`, `kickoff_returner_player_id` are real GSIS IDs
(format "00-00xxxxx") straight from the source -- resolved here against
`canonical_players.gsis_id` (a column that already exists on that table
and was simply unused by the passer/rusher/receiver-key columns, which
are PFR-keyed instead). A GSIS ID with no `canonical_players` match is
recorded with `player_id=NULL` and disclosed, never dropped or guessed.

--- DRIVES: REAL, STRUCTURED, REPEATED-PER-PLAY SUMMARY FIELDS ---
Every real play within a drive carries the SAME drive-summary values
(`fixed_drive`, `fixed_drive_result`, `drive_play_count`,
`drive_start_yard_line`, `drive_end_yard_line`, `drive_play_id_started/
ended`, `drive_time_of_possession`, `drive_ended_with_score`) -- confirmed
by direct inspection (every real play in a sample drive after the game-
opening placeholder row repeats the identical summary). One drive row is
built per real `(game_id, fixed_drive)` pair from the last real play seen
in that group; the handful of placeholder rows with empty drive fields
(kickoff-of-game markers) are skipped, not treated as their own drive.
"""
from __future__ import annotations

import csv
import gzip
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "NFL"
DATASET = "nfl_pbp_defense_drive_ext"
SOURCE_ID = "NFLVERSE_DATA"
STATS_URL_TMPL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz"
IMPORTS_DIR = ENGINE_DIR / "imports"
MIN_SEASON = 1999
MAX_SEASON = 2025
RETRIEVED_AT = "2026-08-18"

DEF_FIELDS = [
    "sack_player_id", "sack_player_name",
    "half_sack_1_player_id", "half_sack_1_player_name",
    "half_sack_2_player_id", "half_sack_2_player_name",
    "interception_player_id", "interception_player_name",
    "forced_fumble_player_1_player_id", "forced_fumble_player_1_player_name",
    "forced_fumble_player_2_player_id", "forced_fumble_player_2_player_name",
    "fumble_recovery_1_player_id", "fumble_recovery_1_player_name",
    "fumble_recovery_2_player_id", "fumble_recovery_2_player_name",
    "kicker_player_id", "kicker_player_name",
    "punt_returner_player_id", "punt_returner_player_name",
    "kickoff_returner_player_id", "kickoff_returner_player_name",
]
DRIVE_FIELDS = [
    "fixed_drive", "fixed_drive_result", "drive_play_count", "drive_time_of_possession",
    "drive_first_downs", "drive_inside20", "drive_ended_with_score", "drive_yards_penalized",
    "drive_start_yard_line", "drive_end_yard_line", "drive_play_id_started", "drive_play_id_ended",
]


def _fetch(season: int) -> Path | None:
    path = IMPORTS_DIR / f"nflverse_pbp_full_{season}.csv.gz"
    if path.exists():
        return path
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
            return None
        raise
    return path


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_plays_defense_ext (
            game_id TEXT NOT NULL,
            play_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            posteam TEXT,
            defteam TEXT,
            sack_player_id TEXT, sack_player_gsis TEXT, sack_player_name_raw TEXT,
            half_sack_1_player_id TEXT, half_sack_1_player_name_raw TEXT,
            half_sack_2_player_id TEXT, half_sack_2_player_name_raw TEXT,
            interception_player_id TEXT, interception_player_gsis TEXT, interception_player_name_raw TEXT,
            forced_fumble_player_1_id TEXT, forced_fumble_player_1_name_raw TEXT,
            forced_fumble_player_2_id TEXT, forced_fumble_player_2_name_raw TEXT,
            fumble_recovery_1_player_id TEXT, fumble_recovery_1_player_name_raw TEXT,
            fumble_recovery_2_player_id TEXT, fumble_recovery_2_player_name_raw TEXT,
            kicker_player_id TEXT, kicker_player_name_raw TEXT,
            punt_returner_player_id TEXT, punt_returner_player_name_raw TEXT,
            kickoff_returner_player_id TEXT, kickoff_returner_player_name_raw TEXT,
            source_id TEXT NOT NULL, retrieved_at TEXT NOT NULL, verification_status TEXT NOT NULL,
            PRIMARY KEY (game_id, play_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_drives_real (
            game_id TEXT NOT NULL,
            drive_number INTEGER NOT NULL,
            season INTEGER NOT NULL,
            offense_team TEXT,
            result_raw TEXT,
            play_count INTEGER,
            time_of_possession TEXT,
            first_downs INTEGER,
            reached_red_zone INTEGER,
            ended_with_score INTEGER,
            yards_penalized INTEGER,
            start_yard_line_raw TEXT,
            end_yard_line_raw TEXT,
            first_play_id TEXT,
            last_play_id TEXT,
            source_id TEXT NOT NULL, retrieved_at TEXT NOT NULL, verification_status TEXT NOT NULL,
            PRIMARY KEY (game_id, drive_number)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_nfl_def_ext_sack ON nfl_plays_defense_ext(sack_player_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_nfl_def_ext_int ON nfl_plays_defense_ext(interception_player_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_nfl_drives_offense ON nfl_drives_real(offense_team, season)")
    c.commit()


def _ensure_source_registered(c) -> None:
    c.execute(
        """INSERT INTO sources(source_id, source_name, source_url, license_note, attribution_required,
           approved_for_import, notes) VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(source_id) DO NOTHING""",
        (SOURCE_ID, "nflverse (nflfastR play-by-play)", "https://github.com/nflverse/nflverse-data",
         "Same already-approved NFLVERSE_DATA source as nfl_plays; MIT-licensed.", 0, 1,
         "Batch 4: pulled the full 372-column release (vs. the reduced subset in nfl_plays) for real "
         "defensive-event GSIS identity and drive-summary fields."),
    )


def run_import() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()
    backup = safety.create_verified_backup()

    report = {
        "seasons_imported": [], "seasons_not_published": [],
        "defense_rows": 0, "defense_identity_resolved": 0, "defense_identity_unresolved": 0,
        "drive_rows": 0,
    }
    try:
        c = engine_bootstrap.connect()
        _ensure_schema(c)
        gsis_to_player = {r["gsis_id"]: r["player_id"] for r in c.execute(
            "SELECT gsis_id, player_id FROM canonical_players WHERE gsis_id IS NOT NULL")}

        for season in range(MIN_SEASON, MAX_SEASON + 1):
            path = _fetch(season)
            if path is None:
                report["seasons_not_published"].append(season)
                continue

            drives_this_season: dict[tuple, dict] = {}
            with gzip.open(path, "rt", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    game_id, play_id = row.get("game_id"), row.get("play_id")
                    if not game_id or not play_id:
                        continue

                    if any(row.get(fld) for fld in DEF_FIELDS if fld.endswith("_id")):
                        def _res(gsis):
                            gsis = gsis or None
                            return gsis_to_player.get(gsis) if gsis else None

                        c.execute(
                            """INSERT INTO nfl_plays_defense_ext(
                                game_id, play_id, season, posteam, defteam,
                                sack_player_id, sack_player_gsis, sack_player_name_raw,
                                half_sack_1_player_id, half_sack_1_player_name_raw,
                                half_sack_2_player_id, half_sack_2_player_name_raw,
                                interception_player_id, interception_player_gsis, interception_player_name_raw,
                                forced_fumble_player_1_id, forced_fumble_player_1_name_raw,
                                forced_fumble_player_2_id, forced_fumble_player_2_name_raw,
                                fumble_recovery_1_player_id, fumble_recovery_1_player_name_raw,
                                fumble_recovery_2_player_id, fumble_recovery_2_player_name_raw,
                                kicker_player_id, kicker_player_name_raw,
                                punt_returner_player_id, punt_returner_player_name_raw,
                                kickoff_returner_player_id, kickoff_returner_player_name_raw,
                                source_id, retrieved_at, verification_status)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(game_id, play_id) DO NOTHING""",
                            (game_id, play_id, season, row.get("posteam"), row.get("defteam"),
                             _res(row.get("sack_player_id")), row.get("sack_player_id"), row.get("sack_player_name"),
                             _res(row.get("half_sack_1_player_id")), row.get("half_sack_1_player_name"),
                             _res(row.get("half_sack_2_player_id")), row.get("half_sack_2_player_name"),
                             _res(row.get("interception_player_id")), row.get("interception_player_id"),
                             row.get("interception_player_name"),
                             _res(row.get("forced_fumble_player_1_player_id")), row.get("forced_fumble_player_1_player_name"),
                             _res(row.get("forced_fumble_player_2_player_id")), row.get("forced_fumble_player_2_player_name"),
                             _res(row.get("fumble_recovery_1_player_id")), row.get("fumble_recovery_1_player_name"),
                             _res(row.get("fumble_recovery_2_player_id")), row.get("fumble_recovery_2_player_name"),
                             _res(row.get("kicker_player_id")), row.get("kicker_player_name"),
                             _res(row.get("punt_returner_player_id")), row.get("punt_returner_player_name"),
                             _res(row.get("kickoff_returner_player_id")), row.get("kickoff_returner_player_name"),
                             SOURCE_ID, RETRIEVED_AT, "SOURCE_BACKED"),
                        )
                        report["defense_rows"] += 1
                        for fld in ("sack_player_id", "interception_player_id",
                                    "forced_fumble_player_1_player_id", "fumble_recovery_1_player_id"):
                            gsis = row.get(fld)
                            if gsis:
                                if gsis in gsis_to_player:
                                    report["defense_identity_resolved"] += 1
                                else:
                                    report["defense_identity_unresolved"] += 1

                    if row.get("drive_play_count"):
                        key = (game_id, row.get("fixed_drive"))
                        drives_this_season[key] = row

            for (game_id, fixed_drive), row in drives_this_season.items():
                if not fixed_drive:
                    continue
                c.execute(
                    """INSERT INTO nfl_drives_real(
                        game_id, drive_number, season, offense_team, result_raw, play_count,
                        time_of_possession, first_downs, reached_red_zone, ended_with_score,
                        yards_penalized, start_yard_line_raw, end_yard_line_raw, first_play_id, last_play_id,
                        source_id, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(game_id, drive_number) DO NOTHING""",
                    (game_id, int(fixed_drive), season, row.get("posteam"), row.get("fixed_drive_result"),
                     int(row["drive_play_count"]) if row.get("drive_play_count") else None,
                     row.get("drive_time_of_possession"),
                     int(row["drive_first_downs"]) if row.get("drive_first_downs") else None,
                     1 if row.get("drive_inside20") == "1" else 0,
                     1 if row.get("drive_ended_with_score") == "1" else 0,
                     int(row["drive_yards_penalized"]) if row.get("drive_yards_penalized") else None,
                     row.get("drive_start_yard_line"), row.get("drive_end_yard_line"),
                     row.get("drive_play_id_started"), row.get("drive_play_id_ended"),
                     SOURCE_ID, RETRIEVED_AT, "SOURCE_BACKED"),
                )
                report["drive_rows"] += 1

            c.commit()
            report["seasons_imported"].append(season)

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_plays_defense_ext", rows_published=report["defense_rows"],
            rows_rejected=report["defense_identity_unresolved"], rows_read=report["defense_rows"],
            min_row_count_floor=5000,
        )
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=report["defense_rows"] + report["drive_rows"],
            rows_imported=report["defense_rows"] + report["drive_rows"],
            rows_rejected=report["defense_identity_unresolved"], detail=report,
        )
        c.close()
        return {"status": "SUCCESS", "run_id": run_id, "backup_id": backup["backup_id"], **report}
    except Exception as e:
        try:
            c.close()
        except Exception:
            pass
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                           failure_reason=repr(e), detail={"restore": restore_info})
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(e), "backup": backup}


if __name__ == "__main__":
    import json
    print(json.dumps(run_import(), indent=2, default=str))
