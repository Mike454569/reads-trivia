"""NFL player contracts -- Engine-gap-audit operation.

Real source, confirmed live before writing any code: nflverse-data's GitHub
Release tagged `contracts`
(https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv.gz),
a single ~1.1MB file mirroring OverTheCap's historical contract database --
already `approved_for_import=1` in the `sources` table as NFLVERSE_DATA (the
same umbrella source already used for games/draft/rosters/player_stats).

Identity resolution, the real hard problem here: this file carries NO gsis_id
or pfr_id at all -- only OverTheCap's own `otc_id` (a per-PLAYER id, confirmed
by checking for duplicates: 9,732 distinct otc_id values across 31,893 rows,
average ~3.3 contracts/player -- a player signs multiple contracts over a
career). The one real, structural join path available is the draft record:
`draft_year` + `draft_round` + `draft_overall` together identify a UNIQUE real
draft slot (no two players share a draft slot in the same year), so this
module resolves identity via that triple against `draft_facts`
(draft_season, draft_round, draft_pick_overall) -- never a blind join on
display name alone. Confirmed by direct testing before building: 13,913 of
14,100 rows with a real draft triple resolve this way; the ~180 where the
triple matched but the raw name string differed were spot-checked and are
real matches with nickname/suffix formatting differences (Matt Stafford vs.
Matthew Stafford, Mitchell vs. Mitch Trubisky, Buck vs. Javorius Allen) --
the draft slot itself is what proves identity here, not a fuzzy name match,
so those are accepted too. The other 17,793 rows have no draft_year at all
(real undrafted free agents) -- honestly left UNRESOLVED, never guessed at
via name-only matching; this is a real, disclosed ~44% ceiling on this
source, not a defect in this importer.

Team resolution: the source's `team` column is a bare nickname ("Packers"),
sometimes a real multi-team career string ("ARI/BAL/CAR" -- an already-coded
history of every team a multi-stop player has been under contract with), and
in a small number of rows a clear parsing artifact (values like "CB"/"LB"/
"WR" -- a position code, not a team, apparently shifted into the wrong
column upstream). Only an unambiguous single-team nickname resolves to a
real team_code (matched against team_aliases' own current full_name); a
multi-team string or an unrecognized value is left team_code=NULL rather
than guessed at -- this project's `Nulls` rule (unsupported stays NULL,
never zero/guessed).

No per-contract id exists in the source. First attempt used `(otc_id,
year_signed)` as a composite key, assuming a player never signs two distinct
contracts in one calendar year -- checked directly against the real
published table (not just the source file) after the first run and found
this false: 3,565 rows collapsed under that key that shouldn't have (e.g.
Austin Davis/Browns/2015 has two real, different contracts on record that
year -- years=3/apy=2086765 and years=1/apy=660000, not a duplicate).
`(otc_id, year_signed, team)` was tried next and still collided (4,060
triples), so this table uses a surrogate autoincrement `contract_id` instead
and a full delete-and-republish per run (DELETE all `source_id=NFLVERSE_DATA`
rows, then re-insert) -- correct because this is one single source file
downloaded fresh every run, not an incremental multi-file dataset; no natural
key is being forced to do work it can't honestly do.
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
DATASET = "nfl_player_contracts"
SOURCE_ID = "NFLVERSE_DATA"
CONTRACTS_URL = "https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv.gz"
IMPORTS_DIR = ENGINE_DIR / "imports"


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_player_contracts (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            otc_id TEXT NOT NULL,
            year_signed INTEGER NOT NULL,
            player_key TEXT NOT NULL,
            team_code TEXT,
            position TEXT,
            is_active INTEGER,
            contract_years INTEGER,
            value REAL,
            apy REAL,
            guaranteed REAL,
            draft_season INTEGER,
            draft_round INTEGER,
            draft_pick_overall INTEGER,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS staging_nfl_player_contracts (
            batch_id TEXT NOT NULL REFERENCES import_batches(batch_id),
            source_row INTEGER NOT NULL,
            player TEXT, position TEXT, team TEXT, is_active TEXT,
            year_signed TEXT, years TEXT, value TEXT, apy TEXT, guaranteed TEXT,
            otc_id TEXT, draft_year TEXT, draft_round TEXT, draft_overall TEXT,
            PRIMARY KEY (batch_id, source_row)
        )
    """)
    c.commit()


def _nickname_to_team_code(c) -> dict[str, str]:
    rows = c.execute(
        "SELECT DISTINCT team_code, full_name FROM team_aliases WHERE season_end IS NULL OR season_end >= 2024"
    ).fetchall()
    return {r["full_name"].split()[-1]: r["team_code"] for r in rows}


def _resolve_team_code(team_field: str, nickname_map: dict[str, str]) -> str | None:
    if not team_field or "/" in team_field:
        return None  # multi-team career string -- no single "the team", never guessed
    return nickname_map.get(team_field)


def _stage(c, bid: str, path: Path) -> tuple[int, int, int]:
    read = staged = rejected = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            read += 1
            player = import_data.col(row, "player")
            otc_id = import_data.col(row, "otc_id")
            if not player or not otc_id:
                import_data.reject(c, bid, i, "MISSING_KEY_FIELD", "contract row needs player + otc_id", row)
                rejected += 1
                continue
            c.execute(
                "INSERT INTO staging_nfl_player_contracts(player, position, team, is_active, year_signed, "
                "years, value, apy, guaranteed, otc_id, draft_year, draft_round, draft_overall, "
                "batch_id, source_row) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (player, import_data.col(row, "position"), import_data.col(row, "team"),
                 import_data.col(row, "is_active"), import_data.col(row, "year_signed"),
                 import_data.col(row, "years"), import_data.col(row, "value"), import_data.col(row, "apy"),
                 import_data.col(row, "guaranteed"), otc_id, import_data.col(row, "draft_year"),
                 import_data.col(row, "draft_round"), import_data.col(row, "draft_overall"), bid, i),
            )
            staged += 1
    return read, staged, rejected


def _publish(c, bid: str) -> tuple[int, int]:
    draft_map: dict[tuple[int, int, int], str] = {}
    for r in c.execute("SELECT draft_season, draft_round, draft_pick_overall, player_key FROM draft_facts"):
        if r["draft_season"] is not None and r["draft_round"] is not None and r["draft_pick_overall"] is not None:
            draft_map[(r["draft_season"], r["draft_round"], r["draft_pick_overall"])] = r["player_key"]
    nickname_map = _nickname_to_team_code(c)

    # Full delete-and-republish for this run's source scope -- see module
    # docstring: no natural per-contract key exists in this source, so a
    # surrogate `contract_id` is used and the whole prior NFLVERSE_DATA set
    # is replaced fresh each run rather than UPSERTed on a key that would
    # silently collapse real distinct rows.
    c.execute("DELETE FROM nfl_player_contracts WHERE source_id=?", (SOURCE_ID,))

    published = unresolved = 0
    for row in c.execute(
        "SELECT player, position, team, is_active, year_signed, years, value, apy, guaranteed, "
        "otc_id, draft_year, draft_round, draft_overall FROM staging_nfl_player_contracts WHERE batch_id=?", (bid,)
    ):
        dy = import_data.parse_int(row["draft_year"])
        dr = import_data.parse_int(row["draft_round"])
        do = import_data.parse_int(row["draft_overall"])
        player_key = draft_map.get((dy, dr, do)) if (dy and dr and do) else None
        if not player_key:
            unresolved += 1
            continue

        year_signed = import_data.parse_int(row["year_signed"])
        if year_signed is None:
            unresolved += 1
            continue

        rec = {
            "otc_id": row["otc_id"],
            "year_signed": year_signed,
            "player_key": player_key,
            "team_code": _resolve_team_code(row["team"], nickname_map),
            "position": row["position"],
            "is_active": 1 if (row["is_active"] or "").upper() == "TRUE" else (0 if row["is_active"] else None),
            "contract_years": import_data.parse_int(row["years"]),
            "value": float(row["value"]) if row["value"] not in (None, "", "NA") else None,
            "apy": float(row["apy"]) if row["apy"] not in (None, "", "NA") else None,
            "guaranteed": float(row["guaranteed"]) if row["guaranteed"] not in (None, "", "NA") else None,
            "draft_season": dy, "draft_round": dr, "draft_pick_overall": do,
            "verification_status": "SOURCE_BACKED",
            "source_id": SOURCE_ID,
        }
        cols = list(rec.keys())
        c.execute(
            f"INSERT INTO nfl_player_contracts({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
            [rec[k] for k in cols],
        )
        published += 1
    return published, unresolved


def run_nfl_contracts_refresh() -> dict:
    IMPORTS_DIR.mkdir(exist_ok=True)

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM nfl_player_contracts").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    import gzip
    import shutil
    import urllib.request

    try:
        gz_path = IMPORTS_DIR / "nflverse_historical_contracts.csv.gz"
        csv_path = IMPORTS_DIR / "nflverse_historical_contracts.csv"
        req = urllib.request.Request(CONTRACTS_URL, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(gz_path, "wb") as f:
            shutil.copyfileobj(resp, f)
        with gzip.open(gz_path, "rb") as gz_f, open(csv_path, "wb") as out_f:
            shutil.copyfileobj(gz_f, out_f)

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        bid = import_data.begin_batch(c, DATASET, SOURCE_ID, csv_path)
        c.execute("BEGIN")
        try:
            read, staged, rejected = _stage(c, bid, csv_path)
            published, unresolved = _publish(c, bid)

            qa_count = c.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
            c.execute(
                "UPDATE import_batches SET finished_at=?, status='PUBLISHED', rows_read=?, rows_staged=?, "
                "rows_published=?, rows_rejected=?, qa_issue_count=? WHERE batch_id=?",
                (_dt.datetime.now(_dt.timezone.utc).isoformat(), read, staged, published, rejected, qa_count, bid),
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
                c, table="nfl_player_contracts", rows_published=published, rows_rejected=rejected,
                rows_read=read, min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_downloaded=read, rows_imported=published, rows_rejected=rejected,
                failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=read, rows_imported=published, rows_rejected=rejected,
            no_op=(published == 0 and rejected == 0),
            detail={"batch_id": bid, "rows_unresolved_identity": unresolved},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "rows_downloaded": read, "rows_imported": published,
            "rows_rejected": rejected, "rows_unresolved_identity": unresolved, "backup_id": backup["backup_id"],
        }
    except Exception as e:
        # Closing the live connection before an atomic backup-restore
        # (os.replace over the live DB file) avoids a real, observed
        # cascading "database is locked" on the very next connection.
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
