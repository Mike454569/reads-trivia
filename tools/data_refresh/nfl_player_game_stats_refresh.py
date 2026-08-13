"""NFL production data refresh -- player-GAME-level statistics.

Historical Engine Enrichment operation, continuation. Master Knowledge
Blueprint (02_FIELD_MASTER, "Player-Game Stats" domain) marks this High
priority, and 14_CLAUDE_EXECUTION's step 3 names it the first gap to
close, ahead of "CFB season-stat certification / identity coverage /
historical postseason / aliases" -- this module closes it for NFL.

Real source, confirmed live before writing any code: nflverse-data's
`stats_player` release also publishes one real file per season at WEEKLY
(i.e. per-game) grain --
https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv
-- same approved NFLVERSE_DATA source as the season-level table this
mirrors. Its own `game_id` column uses the exact same convention as the
real `games` table already in this database (confirmed directly:
`2024_01_BAL_KC` in the stats file, `1999_01_MIN_ATL` as the format
already live in `games`) -- this is what makes real canonical
game-linkage possible (Field Master row 50, "game_id: Canonical game
foreign key") rather than a synthetic key. No hard SQL foreign key is
declared, though: a real check run before committing to this design found
the two sources don't guarantee byte-identical IDs in every historical
edge case (bye weeks, an old postseason relabeling) -- game_id is
populated and real, but treated as a soft/best-effort join key, not a
constraint that could abort an otherwise-good import over one row.

New table `player_game_stats` (season, week, season_type, game_id,
player_key, team_code, opponent_code, then real per-game passing/rushing/
receiving/defense/kicking counts + nflverse's own fantasy_points_ppr) --
does not already exist; created here. Same canonical identity resolution
as nfl_player_stats_refresh.py (gsis_id -> canonical_players.player_id,
draft fallback) -- deliberately reused via import, not re-implemented.

Same full-idempotent-republish pattern as the other refreshes. Real
scale check before implementing: ~19,000 rows for a single season
(2024) x 27 seasons is a real but entirely manageable volume for SQLite
(smaller per-row than play-by-play; this project's `cfb_games_canonical`
alone already holds 36,231 rows without issue).
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
DATASET = "nfl_player_game_stats"
SOURCE_ID = "NFLVERSE_DATA"
STATS_URL_TMPL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"
MIN_SEASON = 1999
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year + 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS player_game_stats (
    game_id TEXT NOT NULL,
    player_key TEXT NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER,
    season_type TEXT,
    team_code TEXT,
    opponent_code TEXT,
    pass_completions INTEGER,
    pass_attempts INTEGER,
    pass_yards INTEGER,
    pass_td INTEGER,
    interceptions_thrown INTEGER,
    rush_attempts INTEGER,
    rush_yards INTEGER,
    rush_td INTEGER,
    targets INTEGER,
    receptions INTEGER,
    rec_yards INTEGER,
    rec_td INTEGER,
    sacks REAL,
    def_interceptions REAL,
    tackles REAL,
    fg_made INTEGER,
    fg_att INTEGER,
    fantasy_points_ppr REAL,
    verification_status TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
    source_id TEXT REFERENCES sources(source_id),
    PRIMARY KEY (game_id, player_key)
)
"""


def _ensure_schema(c) -> None:
    c.executescript(_SCHEMA_SQL)
    c.commit()


def _ensure_staging_table(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS staging_nfl_player_game_stats (
            batch_id TEXT NOT NULL REFERENCES import_batches(batch_id),
            source_row INTEGER NOT NULL,
            season TEXT, week TEXT, season_type TEXT, game_id TEXT, player_id TEXT,
            team TEXT, opponent_team TEXT,
            completions TEXT, attempts TEXT, passing_yards TEXT, passing_tds TEXT,
            passing_interceptions TEXT, carries TEXT, rushing_yards TEXT, rushing_tds TEXT,
            targets TEXT, receptions TEXT, receiving_yards TEXT, receiving_tds TEXT,
            def_sacks TEXT, def_interceptions TEXT, def_tackles_solo TEXT,
            def_tackles_with_assist TEXT, fg_made TEXT, fg_att TEXT, fantasy_points_ppr TEXT,
            PRIMARY KEY (batch_id, source_row)
        )
    """)
    c.commit()


def _stage_one_season(c, bid: str, season: int, path: Path) -> tuple[int, int, int]:
    read = staged = rejected = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for local_i, row in enumerate(csv.DictReader(f), start=2):
            i = season * 1000000 + local_i
            read += 1
            player_id = import_data.col(row, "player_id")
            game_id = import_data.col(row, "game_id")
            if not player_id or not game_id:
                import_data.reject(c, bid, i, "MISSING_KEY", "player-game row needs player_id/game_id", row)
                rejected += 1
                continue
            c.execute(
                "INSERT INTO staging_nfl_player_game_stats(season, week, season_type, game_id, player_id, "
                "team, opponent_team, completions, attempts, passing_yards, passing_tds, "
                "passing_interceptions, carries, rushing_yards, rushing_tds, targets, receptions, "
                "receiving_yards, receiving_tds, def_sacks, def_interceptions, def_tackles_solo, "
                "def_tackles_with_assist, fg_made, fg_att, fantasy_points_ppr, batch_id, source_row) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (str(season), import_data.col(row, "week"), import_data.col(row, "season_type"), game_id,
                 player_id, import_data.col(row, "team"), import_data.col(row, "opponent_team"),
                 import_data.col(row, "completions"), import_data.col(row, "attempts"),
                 import_data.col(row, "passing_yards"), import_data.col(row, "passing_tds"),
                 import_data.col(row, "passing_interceptions"), import_data.col(row, "carries"),
                 import_data.col(row, "rushing_yards"), import_data.col(row, "rushing_tds"),
                 import_data.col(row, "targets"), import_data.col(row, "receptions"),
                 import_data.col(row, "receiving_yards"), import_data.col(row, "receiving_tds"),
                 import_data.col(row, "def_sacks"), import_data.col(row, "def_interceptions"),
                 import_data.col(row, "def_tackles_solo"), import_data.col(row, "def_tackles_with_assist"),
                 import_data.col(row, "fg_made"), import_data.col(row, "fg_att"),
                 import_data.col(row, "fantasy_points_ppr"), bid, i),
            )
            staged += 1
    return read, staged, rejected


def _publish(c, bid: str) -> tuple[int, int, int]:
    canon = {r["gsis_id"]: r["player_id"] for r in
             c.execute("SELECT gsis_id, player_id FROM canonical_players WHERE gsis_id IS NOT NULL").fetchall()}
    draft_fallback = {r["nflverse_player_id"]: r["player_key"] for r in
                       c.execute("SELECT nflverse_player_id, player_key FROM nfl_players_draft "
                                 "WHERE nflverse_player_id IS NOT NULL").fetchall()}
    real_game_ids = {r["game_id"] for r in c.execute("SELECT game_id FROM games").fetchall()}

    published = 0
    unresolved = 0
    game_id_misses = 0
    for row in c.execute(
        "SELECT season, week, season_type, game_id, player_id, team, opponent_team, completions, attempts, "
        "passing_yards, passing_tds, passing_interceptions, carries, rushing_yards, rushing_tds, targets, "
        "receptions, receiving_yards, receiving_tds, def_sacks, def_interceptions, def_tackles_solo, "
        "def_tackles_with_assist, fg_made, fg_att, fantasy_points_ppr FROM staging_nfl_player_game_stats "
        "WHERE batch_id=?", (bid,)
    ):
        gsis_id = row["player_id"]
        player_key = canon.get(gsis_id) or draft_fallback.get(gsis_id)
        if not player_key:
            unresolved += 1
            continue
        if row["game_id"] not in real_game_ids:
            game_id_misses += 1  # still imported -- game_id is a soft join key, see module docstring

        tackles = None
        solo = import_data.parse_int(row["def_tackles_solo"])
        assist = import_data.parse_int(row["def_tackles_with_assist"])
        if solo is not None or assist is not None:
            tackles = (solo or 0) + (assist or 0)

        rec = {
            "game_id": row["game_id"],
            "player_key": player_key,
            "season": import_data.parse_int(row["season"]),
            "week": import_data.parse_int(row["week"]),
            "season_type": row["season_type"],
            "team_code": row["team"],
            "opponent_code": row["opponent_team"],
            "pass_completions": import_data.parse_int(row["completions"]),
            "pass_attempts": import_data.parse_int(row["attempts"]),
            "pass_yards": import_data.parse_int(row["passing_yards"]),
            "pass_td": import_data.parse_int(row["passing_tds"]),
            "interceptions_thrown": import_data.parse_int(row["passing_interceptions"]),
            "rush_attempts": import_data.parse_int(row["carries"]),
            "rush_yards": import_data.parse_int(row["rushing_yards"]),
            "rush_td": import_data.parse_int(row["rushing_tds"]),
            "targets": import_data.parse_int(row["targets"]),
            "receptions": import_data.parse_int(row["receptions"]),
            "rec_yards": import_data.parse_int(row["receiving_yards"]),
            "rec_td": import_data.parse_int(row["receiving_tds"]),
            "sacks": float(row["def_sacks"]) if row["def_sacks"] not in (None, "") else None,
            "def_interceptions": float(row["def_interceptions"]) if row["def_interceptions"] not in (None, "") else None,
            "tackles": float(tackles) if tackles is not None else None,
            "fg_made": import_data.parse_int(row["fg_made"]),
            "fg_att": import_data.parse_int(row["fg_att"]),
            "fantasy_points_ppr": float(row["fantasy_points_ppr"]) if row["fantasy_points_ppr"] not in (None, "") else None,
            "verification_status": "SOURCE_BACKED",
            "source_id": SOURCE_ID,
        }
        cols = list(rec.keys())
        c.execute(
            f"""INSERT INTO player_game_stats({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})
                ON CONFLICT(game_id, player_key) DO UPDATE SET
                {','.join(f"{k}=excluded.{k}" for k in cols if k not in ('game_id', 'player_key'))}""",
            [rec[k] for k in cols],
        )
        published += 1
    return published, unresolved, game_id_misses


def run_nfl_player_game_stats_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    _ensure_staging_table(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM player_game_stats").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    import urllib.error
    import urllib.request
    import time

    total_read = total_staged = total_rejected = total_published = total_unresolved = total_game_id_misses = 0
    seasons_imported: list[int] = []
    seasons_not_published: list[int] = []

    try:
        manifest_path = IMPORTS_DIR / "nflverse_player_game_stats_manifest.txt"
        manifest_path.write_text(
            "\n".join(STATS_URL_TMPL.format(season=s) for s in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1))
        )

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, manifest_path)
        c.execute("BEGIN")
        try:
            for season in range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1):
                path = IMPORTS_DIR / f"nflverse_stats_player_week_{season}.csv"
                url = STATS_URL_TMPL.format(season=season)
                req = urllib.request.Request(url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
                last_err: Exception | None = None
                for attempt in range(2):
                    try:
                        with urllib.request.urlopen(req, timeout=90) as resp, open(path, "wb") as f:
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

            published, unresolved, game_id_misses = _publish(c, bid)
            total_published += published
            total_unresolved += unresolved
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
                c, table="player_game_stats", rows_published=total_published, rows_rejected=total_rejected,
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
                    "seasons_not_yet_published": seasons_not_published,
                    "rows_unresolved_identity": total_unresolved, "rows_game_id_soft_miss": total_game_id_misses},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "rows_downloaded": total_read, "rows_imported": total_published, "rows_rejected": total_rejected,
            "rows_unresolved_identity": total_unresolved, "rows_game_id_soft_miss": total_game_id_misses,
            "seasons_imported": seasons_imported, "seasons_not_yet_published": seasons_not_published,
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
