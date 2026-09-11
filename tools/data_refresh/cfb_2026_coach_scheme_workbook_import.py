"""Power 4 Coverage Closeout workbook ingestion -- real 2026 CFB head
coach + offensive/defensive scheme facts.

--- WHY THIS EXISTS ---
The user's `Reads_Football_Power4_Coverage_Closeout_2026-09-09.xlsx`
workbook's `RELATIONSHIPS` sheet (1,675 rows) is almost entirely internal
project-tracking rows -- `HAS_CURRENT_ROSTER_SNAPSHOT` / `*_COVERAGE` /
`PLAYER_BIO_FIELD_COVERAGE` relationship types whose real value_stat is
just the literal string "AVAILABLE" (verified directly: every one of the
469 PLAYER_BIO_FIELD_COVERAGE rows says nothing more specific than "Roster
contains <field> field") -- honest coverage bookkeeping, never a football
fact to surface to a player. Only three relationship types in that sheet
are real, structured football facts: HEAD_COACH (67 rows, one per real
Power 4 team), OFFENSIVE_SCHEME, and DEFENSIVE_SCHEME (67 each). This
module ingests exactly those 201 rows and nothing else -- CURRENT_OVERALL_
RECORD (67 more real rows, e.g. "0-1") is deliberately NOT ingested here:
it's a real fact but a same-day snapshot with no stable home in this
Engine's season-END-shaped standings tables, and it goes stale within
days -- a real, disclosed scope cut, not an oversight.

--- WHY A NEW TABLE, NOT cfb_coach_school_links ---
`cfb_coach_school_links` has PRIMARY KEY(cfb_coach_id, school_id) --
verified directly before writing this -- so it can hold only ONE row per
(coach, school) pair, and existing rows already use `context` for rich,
multi-source historical labels (e.g. Dabo Swinney's real existing row:
context="Championship_Coaches_By_School | National Champion |
Top_Coaches_By_School", first_year=2016, last_year=2018 -- his real
championship-era stint, not his current tenure). Writing a "2026 current
coach" fact into that same row would either silently overwrite real
historical provenance or be blocked by the primary key for a coach who
never left his school (exactly Dabo's real case). `cfb_team_2026_coaching_profile`
is a new, narrow, one-row-per-team table for this one real, coherent,
closeout-workbook-sourced dataset -- not a duplicate of anything that
already exists, matching this Engine's own established pattern of small
purpose-built tables (cfb_transfer_summary, cfb_rivalry_pack_index) for a
real dataset that doesn't fit an existing shape.

Coach IDENTITY is still resolved through the EXISTING `cfb_coaches` table
(exact slug-ID match against its real `CFB_COACH_<NAME>` convention,
confirmed directly against real existing rows like CFB_COACH_DABO_SWINNEY
before writing this) -- a coach already known to the Engine is reused,
never duplicated under a second identity; only a genuinely new name gets
a new row.

Follows the same production-safety sequence as
cfb_2026_roster_workbook_import.py (backup -> stage -> publish ->
sanity-check, safe_restore_from_backup on any failure).
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
import uuid
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import import_data  # noqa: E402

LEAGUE = "CFB"
DATASET = "cfb_2026_coach_scheme_workbook"
SOURCE_ID = "READS_POWER4_CLOSEOUT_2026_09_09"
SEASON = 2026
DEFAULT_WORKBOOK_PATH = ENGINE_DIR / "Reads_Football_Power4_Coverage_Closeout_2026-09-09.xlsx"


def _register_source(c) -> None:
    c.execute(
        """INSERT INTO sources(source_id, source_name, source_url, license_note, attribution_required,
           approved_for_import, notes) VALUES (?,?,?,?,0,1,?)
           ON CONFLICT(source_id) DO NOTHING""",
        (SOURCE_ID, "Reads Football Power 4 Coverage Closeout workbook", "user-provided workbook",
         "Project/user source.",
         "Real 2026 head coach + offensive/defensive scheme facts for all 67 real Power 4 teams, "
         "sourced from Ourlads (Tier-2 trusted database) depth-chart pages. See "
         "tools/data_refresh/cfb_2026_coach_scheme_workbook_import.py."),
    )


def _ensure_profile_table(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_team_2026_coaching_profile (
            school_id TEXT PRIMARY KEY REFERENCES schools(school_id),
            cfb_coach_id TEXT REFERENCES cfb_coaches(cfb_coach_id),
            head_coach_name TEXT,
            offensive_scheme TEXT,
            defensive_scheme TEXT,
            verification_status TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
            source_id TEXT NOT NULL
        )
    """)


def _slug_coach_id(name: str) -> str:
    return "CFB_COACH_" + re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")


def _read_relationships(workbook_path: Path) -> tuple[list[str], list[tuple]]:
    import openpyxl

    wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    ws = wb["RELATIONSHIPS"]
    rows = list(ws.iter_rows(values_only=True))
    return list(rows[0]), rows[1:]


def consolidate_team_profiles(workbook_path: Path = DEFAULT_WORKBOOK_PATH) -> list[dict]:
    header, data = _read_relationships(workbook_path)
    idx = {h: i for i, h in enumerate(header)}

    profiles: dict[str, dict] = {}
    field_map = {"HEAD_COACH": "head_coach_name", "OFFENSIVE_SCHEME": "offensive_scheme",
                 "DEFENSIVE_SCHEME": "defensive_scheme"}
    for r in data:
        if not r or r[idx["season"]] != SEASON:
            continue
        rel = r[idx["relationship_type"]]
        if rel not in field_map:
            continue
        team = r[idx["entity_1"]]
        profiles.setdefault(team, {"team": team})[field_map[rel]] = r[idx["value_stat"]]

    return list(profiles.values())


def _publish(c, records: list[dict]) -> dict:
    counts = {"published": 0, "coach_existing": 0, "coach_new": 0, "unmapped_school": 0}
    for rec in records:
        school_id = import_data.resolve_school(c, rec["team"])
        if not school_id:
            c.execute(
                "INSERT INTO qa_issues(severity,entity_type,entity_id,field_name,issue_type,detail) "
                "VALUES('WARN','cfb_2026_coach_scheme_workbook_row',?,'school_id','UNMAPPED_SCHOOL',?)",
                (rec["team"], f"Could not map workbook team '{rec['team']}' to a known school"),
            )
            counts["unmapped_school"] += 1
            continue

        coach_id = None
        coach_name = rec.get("head_coach_name")
        if coach_name:
            coach_id = _slug_coach_id(coach_name)
            existing = c.execute("SELECT 1 FROM cfb_coaches WHERE cfb_coach_id=?", (coach_id,)).fetchone()
            if existing:
                counts["coach_existing"] += 1
            else:
                c.execute(
                    """INSERT INTO cfb_coaches(cfb_coach_id, coach_name, school_context, source_contexts, status)
                       VALUES (?,?,?,?,'SOURCE_BACKED')""",
                    (coach_id, coach_name, rec["team"], SOURCE_ID),
                )
                counts["coach_new"] += 1

        c.execute(
            """INSERT INTO cfb_team_2026_coaching_profile(school_id, cfb_coach_id, head_coach_name,
               offensive_scheme, defensive_scheme, verification_status, source_id)
               VALUES (?,?,?,?,?,'SOURCE_BACKED',?)
               ON CONFLICT(school_id) DO UPDATE SET
                 cfb_coach_id=excluded.cfb_coach_id, head_coach_name=excluded.head_coach_name,
                 offensive_scheme=excluded.offensive_scheme, defensive_scheme=excluded.defensive_scheme,
                 verification_status='SOURCE_BACKED', source_id=?""",
            (school_id, coach_id, coach_name, rec.get("offensive_scheme"), rec.get("defensive_scheme"),
             SOURCE_ID, SOURCE_ID),
        )
        counts["published"] += 1
    return counts


def run_cfb_2026_coach_scheme_workbook_import(workbook_path: Path = DEFAULT_WORKBOOK_PATH) -> dict:
    if not Path(workbook_path).is_file():
        return {"status": "BLOCKED_WORKBOOK_NOT_FOUND", "workbook_path": str(workbook_path)}

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    baseline = c.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='cfb_team_2026_coaching_profile'"
    ).fetchone()[0]
    baseline_rows = 0
    if baseline:
        baseline_rows = c.execute("SELECT COUNT(*) FROM cfb_team_2026_coaching_profile").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup_or_finish_failed(run_id)

    try:
        records = consolidate_team_profiles(workbook_path)

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        _register_source(c)
        _ensure_profile_table(c)
        c.commit()
        bid = "BATCH:" + uuid.uuid4().hex[:20]
        c.execute(
            """INSERT INTO import_batches(batch_id,dataset_name,source_id,source_file,source_sha256,status,
               transform_version) VALUES (?,?,?,?,?,'STAGING','reads-import-v0.9')""",
            (bid, DATASET, SOURCE_ID, str(workbook_path), import_data.sha256(workbook_path)),
        )
        c.commit()
        c.execute("BEGIN")
        try:
            counts = _publish(c, records)
            published = counts["published"]
            rejected = counts["unmapped_school"]
            qa_count = c.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
            c.execute(
                "UPDATE import_batches SET finished_at=?, status='PUBLISHED', rows_read=?, rows_staged=?, "
                "rows_published=?, rows_rejected=?, qa_issue_count=? WHERE batch_id=?",
                (_dt.datetime.now(_dt.timezone.utc).isoformat(), len(records), len(records),
                 published, rejected, qa_count, bid),
            )
            c.commit()
        except Exception:
            c.rollback()
            c.execute("UPDATE import_batches SET finished_at=?, status='ROLLED_BACK' WHERE batch_id=?",
                       (_dt.datetime.now(_dt.timezone.utc).isoformat(), bid))
            c.commit()
            c.close()
            raise

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="cfb_team_2026_coaching_profile", rows_published=published,
                rows_rejected=rejected, rows_read=len(records), min_row_count_floor=baseline_rows,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.safe_restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        no_op = published == 0 and rejected == 0
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=len(records), rows_imported=published, rows_rejected=rejected,
            no_op=no_op, detail={"batch_id": bid, **counts},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "no_op": no_op, "season": SEASON,
            "rows_read": len(records), "rows_published": published, "rows_rejected": rejected,
            "backup_id": backup["backup_id"], **counts,
        }
    except Exception as e:
        restore_info = safety.safe_restore_from_backup(backup["path"])
        c2 = engine_bootstrap.connect()
        safety.finish_run(
            c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
            failure_reason=repr(e), detail={"restore": restore_info},
        )
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(e), "backup": backup}


if __name__ == "__main__":
    import json
    print(json.dumps(run_cfb_2026_coach_scheme_workbook_import(), indent=2, default=str))
