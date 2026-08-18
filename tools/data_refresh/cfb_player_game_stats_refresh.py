"""CFB production data refresh -- player-GAME statistics (Knowledge
Expansion Batch 3), aggregated from the same real per-play source as
`cfb_player_season_stats_refresh.py` (SPORTSDATAVERSE_CFB / cfbfastR-data
`player_stats_{season}.csv`), keyed additionally by `game_id` and `week`
instead of collapsing straight to a season total.

This is a NEW table (`cfb_player_game_stats_real`), not a duplicate of
`cfb_player_season_stats_real` -- game-level rows cannot fit that table's
`(season, school_id, cfb_player_id)` primary key. The aggregation logic,
identity resolution, school resolution, and the real touchdown-field-swap
correction are copied verbatim from the season module (same source, same
confirmed quirks) -- see that module's docstring for the full validation
evidence (Jalen Milroe/Ty Simpson/Jayden Daniels box-score cross-checks).
Re-derived independently here at game granularity, not read back from the
season table, so this table's own numbers can be summed and cross-checked
against the season table as a real internal consistency check.

--- REAL SOURCE GAPS, DISCLOSED NOT FABRICATED ---
This CSV has no tackle field (solo/assisted/for-loss) and no dedicated
extra-point-made field anywhere in its 66 columns (confirmed by reading
the real header). `tackles`, `tackles_for_loss`, and `extra_points_made`
are real schema columns here, but are always NULL this batch -- not
zero, not guessed. `pass_attempts` IS derivable (completions +
incompletions, using the source's own `incompletion_player_id` field,
which the season-level script did not use) and is included here.

--- SEASON SCOPE ---
2014-2025 (matching the season table's own real range), reusing the
2014-2023 CSVs already cached in `imports/` and freshly downloading
2024-2025 (confirmed available from the same GitHub source at run time).
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
DATASET = "cfb_player_game_stats"
SOURCE_ID = "SPORTSDATAVERSE_CFB"
STATS_URL_TMPL = "https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/player_stats/csv/player_stats_{season}.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"
MIN_SEASON = 2014
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year + 1
RETRIEVED_AT = "2026-08-18"


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


def _aggregate_one_season(path: Path) -> dict[tuple[str, str], dict]:
    """Returns {(game_id, source_player_id): {stat_field: value, ...}} --
    same real per-row logic as the season module's `_aggregate_one_season`,
    keyed one level finer. Pure function of one season's real CSV."""
    stats: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "pass_attempts": 0, "completions": 0, "passing_yards": 0, "passing_tds": 0, "interceptions_thrown": 0,
        "rush_attempts": 0, "rushing_yards": 0, "rushing_tds": 0,
        "receptions": 0, "receiving_yards": 0, "receiving_tds": 0,
        "defensive_interceptions": 0, "sacks": 0.0, "forced_fumbles": 0, "fumble_recoveries": 0,
        "pass_breakups": 0, "field_goals_attempted": 0, "field_goals_made": 0,
        "player_name": "", "team": "", "conference": "", "week": None, "opponent": "",
    })

    def touch(game_id: str, pid: str, name: str, team: str, conf: str, week, opponent: str) -> dict:
        s = stats[(game_id, pid)]
        s["player_name"] = name
        s["team"] = team
        s["conference"] = conf
        s["week"] = week
        s["opponent"] = opponent
        return s

    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            game_id = row.get("game_id")
            if not game_id:
                continue
            team = row.get("team", "")
            conf = row.get("conference", "")
            week = _i(row.get("week"))
            opponent = row.get("opponent", "")

            comp_id, comp_name = row.get("completion_player_id"), row.get("completion_player")
            recv_id, recv_name = row.get("reception_player_id"), row.get("reception_player")
            incomp_id, incomp_name = row.get("incompletion_player_id"), row.get("incompletion_player")
            td_id = row.get("touchdown_player_id")

            if comp_id not in (None, "", "NA") and recv_id not in (None, "", "NA"):
                yds = _i(row.get("completion_yds") or row.get("reception_yds")) or 0
                passer_id, passer_name = comp_id, comp_name
                receiver_id, receiver_name = recv_id, recv_name
                # Real, confirmed source quirk (see cfb_player_season_stats_refresh.py
                # docstring): fields swap specifically on the touchdown-scoring play.
                if td_id not in (None, "", "NA") and td_id == recv_id:
                    passer_id, passer_name = recv_id, recv_name
                    receiver_id, receiver_name = comp_id, comp_name
                p = touch(game_id, passer_id, passer_name, team, conf, week, opponent)
                p["pass_attempts"] += 1
                p["completions"] += 1
                p["passing_yards"] += yds
                r = touch(game_id, receiver_id, receiver_name, team, conf, week, opponent)
                r["receptions"] += 1
                r["receiving_yards"] += yds
                if td_id not in (None, "", "NA"):
                    p["passing_tds"] += 1
                    r["receiving_tds"] += 1

            if incomp_id not in (None, "", "NA"):
                touch(game_id, incomp_id, incomp_name, team, conf, week, opponent)["pass_attempts"] += 1

            intth_id = row.get("interception_thrown_player_id")
            if intth_id not in (None, "", "NA"):
                p = touch(game_id, intth_id, row.get("interception_thrown_player", ""), team, conf, week, opponent)
                p["pass_attempts"] += 1
                p["interceptions_thrown"] += 1

            rush_id = row.get("rush_player_id")
            if rush_id not in (None, "", "NA"):
                rp = touch(game_id, rush_id, row.get("rush_player", ""), team, conf, week, opponent)
                rp["rush_attempts"] += 1
                rp["rushing_yards"] += _i(row.get("rush_yds")) or 0
                if td_id not in (None, "", "NA") and td_id == rush_id:
                    rp["rushing_tds"] += 1

            int_id = row.get("interception_player_id")
            if int_id not in (None, "", "NA"):
                touch(game_id, int_id, row.get("interception_player", ""), team, conf, week, opponent)["defensive_interceptions"] += 1

            sack_id = row.get("sack_player_id")
            if sack_id not in (None, "", "NA"):
                touch(game_id, sack_id, row.get("sack_player", ""), team, conf, week, opponent)["sacks"] += _f(row.get("sack_stat")) or 1.0

            ff_id = row.get("fumble_forced_player_id")
            if ff_id not in (None, "", "NA"):
                touch(game_id, ff_id, row.get("fumble_forced_player", ""), team, conf, week, opponent)["forced_fumbles"] += 1

            fr_id = row.get("fumble_recovered_player_id")
            if fr_id not in (None, "", "NA"):
                touch(game_id, fr_id, row.get("fumble_recovered_player", ""), team, conf, week, opponent)["fumble_recoveries"] += 1

            pbu_id = row.get("pass_breakup_player_id")
            if pbu_id not in (None, "", "NA"):
                touch(game_id, pbu_id, row.get("pass_breakup_player", ""), team, conf, week, opponent)["pass_breakups"] += 1

            fga_id = row.get("field_goal_attempt_player_id")
            if fga_id not in (None, "", "NA"):
                touch(game_id, fga_id, row.get("field_goal_attempt_player", ""), team, conf, week, opponent)["field_goals_attempted"] += 1
            fgm_id = row.get("field_goal_made_player_id")
            if fgm_id not in (None, "", "NA"):
                touch(game_id, fgm_id, row.get("field_goal_made_player", ""), team, conf, week, opponent)["field_goals_made"] += 1

    return stats


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_player_game_stats_real (
            game_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            week INTEGER,
            school_id TEXT NOT NULL,
            cfb_player_id TEXT NOT NULL,
            player_name TEXT,
            opponent_raw TEXT,
            conference TEXT,
            pass_attempts INTEGER,
            completions INTEGER,
            passing_yards INTEGER,
            passing_tds INTEGER,
            interceptions_thrown INTEGER,
            rush_attempts INTEGER,
            rushing_yards INTEGER,
            rushing_tds INTEGER,
            receptions INTEGER,
            receiving_yards INTEGER,
            receiving_tds INTEGER,
            defensive_interceptions INTEGER,
            sacks REAL,
            forced_fumbles INTEGER,
            fumble_recoveries INTEGER,
            pass_breakups INTEGER,
            tackles INTEGER,
            tackles_for_loss INTEGER,
            field_goals_attempted INTEGER,
            field_goals_made INTEGER,
            extra_points_made INTEGER,
            source_id TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            PRIMARY KEY (game_id, cfb_player_id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_cfb_pgs_player ON cfb_player_game_stats_real(cfb_player_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cfb_pgs_school_season_week ON cfb_player_game_stats_real(school_id, season, week)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cfb_pgs_game ON cfb_player_game_stats_real(game_id)")
    c.commit()


def run_cfb_player_game_stats_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_player_game_stats_real").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    total_downloaded = total_published = total_unresolved_school = total_unresolved_identity = 0
    total_unresolved_game = 0
    seasons_imported: list[int] = []
    seasons_not_published: list[int] = []

    try:
        c = engine_bootstrap.connect()
        _ensure_schema(c)
        school_cache: dict[str, str | None] = {}
        known_cfb_players = {
            r["cfb_player_id"] for r in c.execute("SELECT cfb_player_id FROM canonical_cfb_players")
        }
        known_games = {
            r["game_id"] for r in c.execute("SELECT game_id FROM cfb_games_canonical")
        }

        for season in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1):
            path = IMPORTS_DIR / f"cfbfastr_player_stats_{season}.csv"
            if not path.exists():
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

            game_stats = _aggregate_one_season(path)
            for (game_id, pid), s in game_stats.items():
                team = s["team"]
                if team not in school_cache:
                    school_cache[team] = _resolve_school(c, team)
                school_id = school_cache[team]
                if not school_id:
                    total_unresolved_school += 1
                    continue
                cfb_player_id = f"ESPN_CFB:{pid}"
                if cfb_player_id not in known_cfb_players:
                    total_unresolved_identity += 1
                    continue
                if game_id not in known_games:
                    total_unresolved_game += 1
                    continue
                c.execute(
                    """INSERT INTO cfb_player_game_stats_real
                        (game_id, season, week, school_id, cfb_player_id, player_name, opponent_raw, conference,
                         pass_attempts, completions, passing_yards, passing_tds, interceptions_thrown,
                         rush_attempts, rushing_yards, rushing_tds,
                         receptions, receiving_yards, receiving_tds,
                         defensive_interceptions, sacks, forced_fumbles, fumble_recoveries,
                         pass_breakups, tackles, tackles_for_loss,
                         field_goals_attempted, field_goals_made, extra_points_made,
                         source_id, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,NULL,?,?,NULL,?,?,?)
                       ON CONFLICT(game_id, cfb_player_id) DO NOTHING""",
                    (game_id, season, s["week"], school_id, cfb_player_id, s["player_name"], s["opponent"], s["conference"],
                     s["pass_attempts"], s["completions"], s["passing_yards"], s["passing_tds"], s["interceptions_thrown"],
                     s["rush_attempts"], s["rushing_yards"], s["rushing_tds"],
                     s["receptions"], s["receiving_yards"], s["receiving_tds"],
                     s["defensive_interceptions"], s["sacks"], s["forced_fumbles"], s["fumble_recoveries"],
                     s["pass_breakups"],
                     s["field_goals_attempted"], s["field_goals_made"],
                     SOURCE_ID, RETRIEVED_AT, "SOURCE_BACKED_DERIVED"),
                )
                total_published += 1
            seasons_imported.append(season)
            c.commit()

        total_rejected = total_unresolved_school + total_unresolved_identity + total_unresolved_game
        safety.run_post_refresh_sanity_checks(
            c, table="cfb_player_game_stats_real", rows_published=total_published,
            rows_rejected=total_rejected, rows_read=total_published + total_rejected,
            min_row_count_floor=baseline_count,
        )

        no_op = total_published == 0
        detail = {
            "seasons_imported": seasons_imported, "seasons_not_yet_published": seasons_not_published,
            "rows_unresolved_school": total_unresolved_school,
            "rows_unresolved_identity": total_unresolved_identity,
            "rows_unresolved_game": total_unresolved_game,
        }
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=total_downloaded, rows_imported=total_published,
            rows_rejected=total_rejected, no_op=no_op, detail=detail,
        )
        c.close()
        return {"status": "SUCCESS", "run_id": run_id, "no_op": no_op, "rows_published": total_published,
                "backup_id": backup["backup_id"], **detail}
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


if __name__ == "__main__":
    import json
    print(json.dumps(run_cfb_player_game_stats_refresh(), indent=2, default=str))
