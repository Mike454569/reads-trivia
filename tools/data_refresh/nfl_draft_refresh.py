"""NFL production data refresh -- draft picks (nfl_players_draft + draft_facts).

Historical Engine Enrichment operation, Part 14: `draft_facts` was found
capped at draft_season=2024 with no automatic refresh anywhere in this repo
(confirmed by grep) -- the real, live NFL Draft Guess mode and every Grid/
Blitz cross-reference this project has built so far quietly loses accuracy
every year this stays stale. Real source, confirmed live before writing any
code: nflverse-data's GitHub Release tagged `draft_picks`
(https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv),
already `approved_for_import=1` in the `sources` table as NFLVERSE_DATA.
Confirmed by direct download and inspection: real data through the 2026
draft class (514 rows for 2025+2026 combined), and its columns map cleanly
onto both `nfl_players_draft` and `draft_facts` -- the same two tables a
now-gone import process originally populated (12,253 rows each, matching
row-for-row).

Two tables, not one: `draft_facts.player_key` has a real FK to
`nfl_players_draft(player_key)` -- a new draft pick needs an identity row
inserted into the parent table before (or in the same transaction as) the
facts row.

Deliberately ADD-ONLY, not a full idempotent re-publish (unlike
nfl_games_refresh.py's approach for `games`): draft_facts/nfl_players_draft
have no single obviously-stable natural key documented anywhere in this
codebase for re-deriving every historical row's exact `player_key`
formatting (three real, distinct id_quality conventions already coexist in
the table -- PFR_UNIQUE, PFR_COLLISION_DISAMBIGUATED with a
`|DRAFT:{season}:{pick}` suffix, and SYNTHETIC_DRAFT_ID for undrafted-PFR-id
players -- and the original importer that made those exact choices no
longer exists here, same as games' history). Blindly re-deriving keys for
all 12,253 existing rows risks silently creating duplicate rows for players
who already exist under a different key convention. Instead: `(season,
pick)` is used as the real, always-unique-within-a-season existence check
-- any CSV row whose (season, pick) already has a matching row is left
completely untouched (not even re-UPSERTed), and only genuinely new picks
(each future season's draft, as it's published) are inserted, using the
same PFR_UNIQUE / collision-disambiguated key convention observed in the
existing data (confirmed by checking for real pfr_id collisions between the
new rows and the existing table before writing this).
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
DATASET = "nfl_draft"
SOURCE_ID = "NFLVERSE_DATA"
DRAFT_URL = "https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv"
IMPORTS_DIR = ENGINE_DIR / "imports"


def _ensure_schema(c) -> None:
    """Real gap found after this module first shipped: the source CSV
    (draft_picks.csv) has always had a real `college` column -- it was
    downloaded and inspected before writing this module's very first
    version, but never mapped. Added additively (safe on a live table);
    backfilled for every existing row, not just new picks going forward --
    see `_backfill_college()`."""
    for table in ("nfl_players_draft", "draft_facts"):
        cols = {r["name"] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
        if "college" not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN college TEXT")
    c.commit()


def _ensure_staging_table(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS staging_nfl_draft (
            batch_id TEXT NOT NULL REFERENCES import_batches(batch_id),
            source_row INTEGER NOT NULL,
            season TEXT, round TEXT, pick TEXT, team TEXT, gsis_id TEXT,
            pfr_player_id TEXT, pfr_player_name TEXT, position TEXT, college TEXT,
            PRIMARY KEY (batch_id, source_row)
        )
    """)
    # A staging table from before `college` existed persists across runs
    # (CREATE TABLE IF NOT EXISTS doesn't migrate an existing one) -- real
    # failure hit in testing, fixed here rather than dropping/recreating
    # the table (which would lose nothing real, but this is the same
    # additive-migration pattern used everywhere else in this module).
    cols = {r["name"] for r in c.execute("PRAGMA table_info(staging_nfl_draft)").fetchall()}
    if "college" not in cols:
        c.execute("ALTER TABLE staging_nfl_draft ADD COLUMN college TEXT")
    c.commit()


def _stage(c, bid: str, path: Path) -> tuple[int, int, int]:
    read = staged = rejected = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            read += 1
            season = import_data.col(row, "season")
            pick = import_data.col(row, "pick")
            name = import_data.col(row, "pfr_player_name")
            if not season or not pick or not name:
                import_data.reject(c, bid, i, "MISSING_DRAFT_KEY", "draft row needs season/pick/player name", row)
                rejected += 1
                continue
            c.execute(
                "INSERT INTO staging_nfl_draft(season, round, pick, team, gsis_id, pfr_player_id, "
                "pfr_player_name, position, college, batch_id, source_row) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (season, import_data.col(row, "round"), pick, import_data.col(row, "team"),
                 import_data.col(row, "gsis_id"), import_data.col(row, "pfr_player_id"),
                 name, import_data.col(row, "position"), import_data.col(row, "college"), bid, i),
            )
            staged += 1
    return read, staged, rejected


def _backfill_college(c, bid: str) -> int:
    """Fills `college` for every existing row (not just new picks this
    run) that doesn't have one yet, matched on the real, stable (season,
    pick) key -- never overwrites a value already present."""
    by_season_pick: dict[tuple[int | None, int | None], str] = {}
    for row in c.execute("SELECT season, pick, college FROM staging_nfl_draft WHERE batch_id=?", (bid,)).fetchall():
        college = row["college"]
        if not college:
            continue
        key = (import_data.parse_int(row["season"]), import_data.parse_int(row["pick"]))
        by_season_pick[key] = college

    updated = 0
    for target in ("nfl_players_draft", "draft_facts"):
        rows = c.execute(
            f"SELECT draft_season, draft_pick_overall FROM {target} WHERE college IS NULL"
        ).fetchall()
        for r in rows:
            key = (r["draft_season"], r["draft_pick_overall"])
            college = by_season_pick.get(key)
            if not college:
                continue
            c.execute(
                f"UPDATE {target} SET college=? WHERE draft_season=? AND draft_pick_overall=? AND college IS NULL",
                (college, r["draft_season"], r["draft_pick_overall"]),
            )
            if target == "nfl_players_draft":
                updated += 1
    return updated


def _publish(c, bid: str) -> tuple[int, int]:
    """Returns (new_picks_inserted, already_present_skipped)."""
    existing_season_picks = {
        (r["draft_season"], r["draft_pick_overall"])
        for r in c.execute("SELECT draft_season, draft_pick_overall FROM nfl_players_draft").fetchall()
    }
    existing_pfr_ids = {
        r["pfr_id"] for r in c.execute("SELECT pfr_id FROM nfl_players_draft WHERE pfr_id IS NOT NULL").fetchall()
    }

    inserted = 0
    skipped = 0
    for row in c.execute(
        "SELECT season, round, pick, team, gsis_id, pfr_player_id, pfr_player_name, position, college "
        "FROM staging_nfl_draft WHERE batch_id=?", (bid,)
    ):
        season = import_data.parse_int(row["season"])
        pick_overall = import_data.parse_int(row["pick"])
        if (season, pick_overall) in existing_season_picks:
            skipped += 1
            continue

        pfr_id = row["pfr_player_id"] or None
        name = row["pfr_player_name"]
        round_ = import_data.parse_int(row["round"])
        team = row["team"]
        position = row["position"]
        gsis_id = row["gsis_id"] or None
        college = row["college"] or None

        if pfr_id:
            key = f"PFR:{pfr_id}"
            if pfr_id in existing_pfr_ids:
                # Real collision with an unrelated existing player sharing this
                # pfr_id (confirmed this pattern already exists in the table --
                # see module docstring) -- disambiguate the same way.
                key = f"PFR:{pfr_id}|DRAFT:{season}:{pick_overall}"
                id_quality = "PFR_COLLISION_DISAMBIGUATED"
            else:
                id_quality = "PFR_UNIQUE"
        else:
            safe_name = (name or "UNKNOWN").upper().replace(" ", "_")
            key = f"DRAFT:{season}:{pick_overall}:{safe_name}"
            id_quality = "SYNTHETIC_DRAFT_ID"

        c.execute(
            "INSERT INTO nfl_players_draft(player_key, draft_season, draft_team, draft_round, "
            "draft_pick_overall, pfr_id, player_name, nflverse_player_id, side, category, position, "
            "id_quality, source_id, college) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (key, season, team, round_, pick_overall, pfr_id, name, gsis_id, None, None, position,
             id_quality, SOURCE_ID, college),
        )
        c.execute(
            "INSERT INTO draft_facts(player_key, player_name, draft_season, draft_team, draft_round, "
            "draft_pick_overall, position, source_id, verification_status, college) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (key, name, season, team, round_, pick_overall, position, SOURCE_ID, "SOURCE_BACKED", college),
        )
        existing_season_picks.add((season, pick_overall))
        if pfr_id:
            existing_pfr_ids.add(pfr_id)
        inserted += 1
    return inserted, skipped


def run_nfl_draft_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    _ensure_staging_table(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM draft_facts").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    try:
        import urllib.error
        import urllib.request

        path = IMPORTS_DIR / "nflverse_draft_picks.csv"
        req = urllib.request.Request(DRAFT_URL, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, path)
        c.execute("BEGIN")
        try:
            read, staged, rejected = _stage(c, bid, path)
            inserted, skipped = _publish(c, bid)
            college_backfilled = _backfill_college(c, bid)
            qa_count = c.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
            c.execute(
                "UPDATE import_batches SET finished_at=?, status='PUBLISHED', rows_read=?, rows_staged=?, "
                "rows_published=?, rows_rejected=?, qa_issue_count=? WHERE batch_id=?",
                (_dt.datetime.now(_dt.timezone.utc).isoformat(), read, staged, inserted, rejected, qa_count, bid),
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
                c, table="draft_facts", rows_published=inserted, rows_rejected=rejected, rows_read=read,
                min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=read, rows_imported=inserted, rows_rejected=rejected,
                failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = inserted == 0 and rejected == 0 and college_backfilled == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=read, rows_imported=inserted, rows_rejected=rejected, no_op=no_op,
            detail={"batch_id": bid, "rows_already_present_skipped": skipped, "college_backfilled": college_backfilled},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op,
            "rows_downloaded": read, "rows_imported": inserted, "rows_rejected": rejected,
            "college_backfilled": college_backfilled,
            "rows_already_present_skipped": skipped, "backup_id": backup["backup_id"],
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            c = engine_bootstrap.connect()
            safety.finish_run(c, run_id, status="SOURCE_NOT_YET_PUBLISHED", backup_id=backup["backup_id"],
                               detail={"source_url": DRAFT_URL})
            c.close()
            return {"status": "SOURCE_NOT_YET_PUBLISHED", "run_id": run_id,
                    "reason": f"{DRAFT_URL} returned 404"}
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                           failure_reason=repr(e), detail={"restore": restore_info})
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(e), "backup": backup}
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
