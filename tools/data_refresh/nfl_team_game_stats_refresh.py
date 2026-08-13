"""NFL production data refresh -- team-GAME boxscore statistics.

Historical Engine Enrichment operation, continuation. Direct user request:
a real boxscore for every game the Engine has, to support "in depth
questions about specific games" -- team-level (not per-player) totals:
yardage, turnovers, penalties, special teams.

Real source, confirmed live before writing any code: nflverse-data's
`stats_team` release, same family as `stats_player` (already the
approved NFLVERSE_DATA source), also published at weekly/per-game grain
-- one real row per team per game (so two rows per game, home + away).
Its `game_id` uses the exact same convention already confirmed for
`stats_player_week` and the real `games` table (e.g. `2024_01_BAL_KC`) --
spot-checked directly against a real, known result (2024 Week 1, KC beat
BAL; the fetched row's completions/pass yards/rush yards/kicking line
matches the real, publicly known box score for that game) before trusting
the mapping.

New table `team_game_stats` (game_id, team_code, season, week,
season_type, opponent_code, then real passing/rushing/turnover/penalty/
kicking/punting totals + a derived `total_yards` and `turnovers`) -- does
not already exist; created here. Same soft (not hard-FK) canonical
game_id linkage as player_game_stats, for the same reason (a constraint
that could abort an otherwise-good import over one historical edge case
is worse than a verified, disclosed best-effort join).

No player-identity resolution needed here (this is team-level, not
player-level) -- team_code is stored as-is; joining to a specific
franchise/season context (if ever needed) can reuse team_aliases exactly
like every other adapter in this codebase already does.

Same full-idempotent-republish pattern as the other refreshes.
"""
from __future__ import annotations

import csv
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
import import_data  # noqa: E402

LEAGUE = "NFL"
DATASET = "nfl_team_game_stats"
SOURCE_ID = "NFLVERSE_DATA"
STATS_URL_TMPL = "https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_week_{season}.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"
MIN_SEASON = 1999
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year + 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS team_game_stats (
    game_id TEXT NOT NULL,
    team_code TEXT NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER,
    season_type TEXT,
    opponent_code TEXT,
    pass_completions INTEGER,
    pass_attempts INTEGER,
    passing_yards INTEGER,
    passing_tds INTEGER,
    passing_interceptions INTEGER,
    sacks_suffered INTEGER,
    sack_yards_lost INTEGER,
    rush_attempts INTEGER,
    rushing_yards INTEGER,
    rushing_tds INTEGER,
    total_yards INTEGER,
    turnovers INTEGER,
    fumbles_lost INTEGER,
    penalties INTEGER,
    penalty_yards INTEGER,
    def_sacks INTEGER,
    def_interceptions INTEGER,
    def_tds INTEGER,
    fg_made INTEGER,
    fg_att INTEGER,
    pat_made INTEGER,
    pat_att INTEGER,
    punts INTEGER,
    punt_yards INTEGER,
    passing_first_downs INTEGER,
    rushing_first_downs INTEGER,
    verification_status TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
    source_id TEXT REFERENCES sources(source_id),
    PRIMARY KEY (game_id, team_code)
)
"""

_STAGE_SRC_COLS = [
    "completions", "attempts", "passing_yards", "passing_tds", "passing_interceptions",
    "sacks_suffered", "sack_yards_lost", "carries", "rushing_yards", "rushing_tds",
    "fumbles_lost_total", "penalties", "penalty_yards", "def_sacks", "def_interceptions",
    "def_tds", "fg_made", "fg_att", "pat_made", "pat_att", "pt_att", "pt_yards",
    "passing_first_downs", "rushing_first_downs",
]


def _ensure_schema(c) -> None:
    c.executescript(_SCHEMA_SQL)
    c.commit()


def _ensure_staging_table(c) -> None:
    cols_sql = ",\n            ".join(f"{col} TEXT" for col in _STAGE_SRC_COLS)
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS staging_nfl_team_game_stats (
            batch_id TEXT NOT NULL REFERENCES import_batches(batch_id),
            source_row INTEGER NOT NULL,
            season TEXT, week TEXT, season_type TEXT, game_id TEXT, team TEXT, opponent_team TEXT,
            {cols_sql},
            PRIMARY KEY (batch_id, source_row)
        )
    """)
    existing_cols = {r["name"] for r in c.execute("PRAGMA table_info(staging_nfl_team_game_stats)").fetchall()}
    for col in _STAGE_SRC_COLS + ["season", "week", "season_type", "game_id", "team", "opponent_team"]:
        if col not in existing_cols:
            c.execute(f"ALTER TABLE staging_nfl_team_game_stats ADD COLUMN {col} TEXT")
    c.commit()


def _stage_one_season(c, bid: str, season: int, path: Path) -> tuple[int, int, int]:
    read = staged = rejected = 0
    dest_cols = ["season", "week", "season_type", "game_id", "team", "opponent_team"] + _STAGE_SRC_COLS
    placeholders = ",".join("?" for _ in dest_cols) + ",?,?"
    with open(path, newline="", encoding="utf-8-sig") as f:
        for local_i, row in enumerate(csv.DictReader(f), start=2):
            i = season * 100000 + local_i
            read += 1
            game_id = import_data.col(row, "game_id")
            team = import_data.col(row, "team")
            if not game_id or not team:
                import_data.reject(c, bid, i, "MISSING_KEY", "team-game row needs game_id/team", row)
                rejected += 1
                continue
            values = [str(season), import_data.col(row, "week"), import_data.col(row, "season_type"),
                      game_id, team, import_data.col(row, "opponent_team")]
            values += [import_data.col(row, src) for src in _STAGE_SRC_COLS]
            c.execute(
                f"INSERT INTO staging_nfl_team_game_stats({','.join(dest_cols)}, batch_id, source_row) "
                f"VALUES ({placeholders})",
                (*values, bid, i),
            )
            staged += 1
    return read, staged, rejected


def _publish(c, bid: str) -> tuple[int, int]:
    real_game_ids = {r["game_id"] for r in c.execute("SELECT game_id FROM games").fetchall()}

    published = 0
    game_id_misses = 0
    dest_cols = ["season", "week", "season_type", "game_id", "team", "opponent_team"] + _STAGE_SRC_COLS
    for row in c.execute(f"SELECT {','.join(dest_cols)} FROM staging_nfl_team_game_stats WHERE batch_id=?", (bid,)):
        rec = dict(zip(dest_cols, row))
        if rec["game_id"] not in real_game_ids:
            game_id_misses += 1  # still imported -- soft join key, see module docstring

        def pint(key):
            return import_data.parse_int(rec.get(key))

        passing_yards = pint("passing_yards") or 0
        rushing_yards = pint("rushing_yards") or 0
        interceptions = pint("passing_interceptions") or 0
        fumbles_lost = pint("fumbles_lost_total") or 0

        out = {
            "game_id": rec["game_id"],
            "team_code": rec["team"],
            "season": import_data.parse_int(rec["season"]),
            "week": pint("week"),
            "season_type": rec["season_type"],
            "opponent_code": rec["opponent_team"],
            "pass_completions": pint("completions"),
            "pass_attempts": pint("attempts"),
            "passing_yards": pint("passing_yards"),
            "passing_tds": pint("passing_tds"),
            "passing_interceptions": pint("passing_interceptions"),
            "sacks_suffered": pint("sacks_suffered"),
            "sack_yards_lost": pint("sack_yards_lost"),
            "rush_attempts": pint("carries"),
            "rushing_yards": pint("rushing_yards"),
            "rushing_tds": pint("rushing_tds"),
            "total_yards": passing_yards + rushing_yards,
            "turnovers": interceptions + fumbles_lost,
            "fumbles_lost": pint("fumbles_lost_total"),
            "penalties": pint("penalties"),
            "penalty_yards": pint("penalty_yards"),
            "def_sacks": pint("def_sacks"),
            "def_interceptions": pint("def_interceptions"),
            "def_tds": pint("def_tds"),
            "fg_made": pint("fg_made"),
            "fg_att": pint("fg_att"),
            "pat_made": pint("pat_made"),
            "pat_att": pint("pat_att"),
            "punts": pint("pt_att"),
            "punt_yards": pint("pt_yards"),
            "passing_first_downs": pint("passing_first_downs"),
            "rushing_first_downs": pint("rushing_first_downs"),
            "verification_status": "SOURCE_BACKED",
            "source_id": SOURCE_ID,
        }
        cols = list(out.keys())
        c.execute(
            f"""INSERT INTO team_game_stats({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})
                ON CONFLICT(game_id, team_code) DO UPDATE SET
                {','.join(f"{k}=excluded.{k}" for k in cols if k not in ('game_id', 'team_code'))}""",
            [out[k] for k in cols],
        )
        published += 1
    return published, game_id_misses


def run_nfl_team_game_stats_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    _ensure_staging_table(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM team_game_stats").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    import urllib.error
    import urllib.request
    import time

    total_read = total_staged = total_rejected = total_published = total_game_id_misses = 0
    seasons_imported: list[int] = []
    seasons_not_published: list[int] = []

    try:
        manifest_path = IMPORTS_DIR / "nflverse_team_game_stats_manifest.txt"
        manifest_path.write_text(
            "\n".join(STATS_URL_TMPL.format(season=s) for s in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1))
        )

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, manifest_path)
        c.execute("BEGIN")
        try:
            for season in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1):
                path = IMPORTS_DIR / f"nflverse_stats_team_week_{season}.csv"
                url = STATS_URL_TMPL.format(season=season)
                req = urllib.request.Request(url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
                last_err: Exception | None = None
                for attempt in range(2):
                    try:
                        with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
                            while True:
                                chunk = resp.read(1024 * 1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        last_err = None
                        break
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            last_err = None
                            seasons_not_published.append(season)
                            break
                        last_err = e
                    except Exception as e:
                        last_err = e
                    time.sleep(2)
                if last_err is not None:
                    raise last_err
                if season in seasons_not_published:
                    continue

                read, staged, rejected = _stage_one_season(c, bid, season, path)
                total_read += read
                total_staged += staged
                total_rejected += rejected
                seasons_imported.append(season)
                time.sleep(0.3)

            published, game_id_misses = _publish(c, bid)
            total_published += published
            total_game_id_misses += game_id_misses

            qa_count = c.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
            c.execute(
                "UPDATE import_batches SET finished_at=?, status='PUBLISHED', rows_read=?, rows_staged=?, "
                "rows_published=?, rows_rejected=?, qa_issue_count=? WHERE batch_id=?",
                (_dt.datetime.now(_dt.timezone.utc).isoformat(), total_read, total_staged,
                 total_published, total_rejected, qa_count, bid),
            )
            c.commit()
        except Exception:
            c.rollback()
            c.execute("UPDATE import_batches SET finished_at=?, status='ROLLED_BACK' WHERE batch_id=?",
                       (_dt.datetime.now(_dt.timezone.utc).isoformat(), bid))
            c.commit()
            raise

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="team_game_stats", rows_published=total_published, rows_rejected=total_rejected,
                rows_read=total_read, min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=total_read, rows_imported=total_published, rows_rejected=total_rejected,
                failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = total_published == 0 and total_rejected == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=total_read, rows_imported=total_published, rows_rejected=total_rejected, no_op=no_op,
            detail={"batch_id": bid, "seasons_imported": seasons_imported,
                    "seasons_not_yet_published": seasons_not_published, "rows_game_id_soft_miss": total_game_id_misses},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "rows_downloaded": total_read, "rows_imported": total_published, "rows_rejected": total_rejected,
            "rows_game_id_soft_miss": total_game_id_misses, "seasons_imported": seasons_imported,
            "seasons_not_yet_published": seasons_not_published, "backup_id": backup["backup_id"],
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
