"""MASTER WORKBOOK ingestion -- 2026 CFB current-season roster facts.

--- WHY THIS EXISTS ---
The user's Reads Football MASTER Knowledge Feed workbook
(`Reads_Football_MASTER_Knowledge_Feed_Combined_20260908.xlsx`,
`MASTER_RELATIONSHIPS` sheet) contains 758 real, Tier-1-official-sourced
CFB player-roster rows (ROSTERED_BY + PLAYS_POSITION + WEARS_JERSEY_NUMBER
+ ACADEMIC_YEAR/CLASS_YEAR_NORMALIZED + HEIGHT/HEIGHT_INCHES + WEIGHT_LB +
FROM_HOMETOWN + ATTENDED_HIGH_SCHOOL + PREVIOUS_COLLEGE) for the 2026
season across 8 real teams (Alabama, Auburn, Georgia Tech, Kansas, Oregon,
Texas, UCLA, USC), scraped directly from each school's own official
athletics site.

Verified directly against the live Engine before writing any code: the
existing automated `cfb_refresh.py` pipeline (SPORTSDATAVERSE_CFB) has
NEVER ingested a 2026 season for CFB -- `cfb_roster_seasons_real`'s real,
measured season ceiling is 2025 (confirmed via `SELECT season, COUNT(*)
... GROUP BY season`). This is genuinely new season-level knowledge, not
a duplicate of anything the automated feed already covers -- it exists
because CFB roster files for a not-yet-played season aren't published by
cfbfastR-data until the season is already underway, exactly the same
"source hasn't published yet" gap `cfb_refresh.py`'s own 404 handling
already documents.

--- ENTITY RESOLUTION (the real point of this module, not just row-copying) ---
The workbook stores players as plain display names, not stable IDs. Every
name is resolved against the EXISTING `canonical_cfb_players` identity
table (109,221 real rows) before ever minting a new one:
  - Exact, globally-unique display_name match -> reuse that cfb_player_id.
  - Exact name shared by multiple canonical players -> disambiguate by
    checking which of them has a real 2024/2025 `cfb_roster_seasons_real`
    row at the SAME school (i.e. the same person, one season earlier).
  - Still ambiguous after that check -> NOT auto-resolved. Logged as a
    real `qa_issues` WARN row for human review, never guessed.
  - No canonical match at all (freshmen/transfers ESPN's feed hasn't
    picked up yet) -> a genuinely new player, minted a new
    `cfb_player_id` in the `WORKBOOK_CFB:` namespace -- deliberately
    never `ESPN_CFB:`, so it can never collide with a real ESPN athlete
    ID if the automated feed catches up to this same player later
    (identity_bridge-style reconciliation, if ever needed, is a real,
    disclosed follow-up, not attempted here).

Resolved-existing players' PRIOR-season `canonical_cfb_players` bio row
(height/weight/hometown from SPORTSDATAVERSE_CFB) is never overwritten by
this import -- a player's listed weight legitimately changes year to
year, and the two sources' 2025-vs-2026 numbers disagreeing is not a
"conflict" to resolve, just two real, different-season facts, both kept
via `cfb_roster_seasons_real`'s own per-season rows.

Source registration: `READS_MASTER_KNOWLEDGE_FEED_2026_09` in `sources`,
matching the exact existing "user-provided workbook" precedent already
used for `READS_CFB_MASTER`/`CFB_RIVALRY_PACK_V1`/
`READS_GOLD_STANDARD_BLUEPRINT_V1` -- never invented as a new pattern.

Follows `cfb_refresh.py`'s exact real production-safety sequence
(safety.start_run -> create_verified_backup_or_finish_failed -> staged
publish inside one transaction -> run_post_refresh_sanity_checks ->
safety.finish_run, with safe_restore_from_backup on any failure) rather
than a bespoke one-off script.
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
import import_data  # noqa: E402  Engine's own generic batch/staging helpers, reused as-is

LEAGUE = "CFB"
DATASET = "cfb_2026_roster_workbook"
SOURCE_ID = "READS_MASTER_KNOWLEDGE_FEED_2026_09"
SEASON = 2026
DEFAULT_WORKBOOK_PATH = ENGINE_DIR / "Reads_Football_MASTER_Knowledge_Feed_Combined_20260908.xlsx"

_CLASS_YEAR_NORM_MAP = {
    "FRESHMAN": "1", "SOPHOMORE": "2", "JUNIOR": "3", "SENIOR": "4", "POST_SENIOR_OR_GRAD": "5",
}

# Real bug caught in testing: preferring POSITION_GROUP_NORMALIZED produced
# ugly concatenated strings ("WIDERECEIVER", "OFFENSIVELINE") in generated
# questions -- that relationship's value is a grouping KEY, not a display
# label. Normalize the raw PLAYS_POSITION text (which varies per school
# between a short code and a spelled-out name) to the exact short-code
# vocabulary cfb_roster_seasons_real.position already uses everywhere else
# (QB/RB/WR/OL/DL/LB/DB/CB/DT/S/DE/C/EDGE/NT/FB/OT/G/ATH/PR/KR/ILB/OLB/P/LS/PK).
_POSITION_TEXT_MAP = {
    "OFFENSIVE LINE": "OL", "DEFENSIVE BACK": "DB", "WIDE RECEIVER": "WR", "DEFENSIVE LINE": "DL",
    "TIGHT END": "TE", "LINEBACKER": "LB", "RUNNING BACK": "RB", "QUARTERBACK": "QB",
    "SAFETY": "S", "CORNERBACK": "CB", "DEFENSIVE END": "DE", "PUNTER": "P", "KICKER": "PK",
    "LONG SNAPPER": "LS", "OUTSIDE LINEBACKER": "OLB", "EDGE": "EDGE", "K": "PK", "SN": "LS", "DS": "LS",
}


def _normalize_position(position_raw) -> str | None:
    if not position_raw:
        return None
    raw = str(position_raw).strip()
    upper = raw.upper()
    if upper in _POSITION_TEXT_MAP:
        return _POSITION_TEXT_MAP[upper]
    if "/" in raw:  # composite listing (e.g. "EDGE/LB", "RB/WR") -- use the first real position
        return _normalize_position(raw.split("/")[0])
    return upper


def _map_class_year(academic_year_raw, class_year_norm) -> str | None:
    raw = (str(academic_year_raw) if academic_year_raw is not None else "").strip()
    if raw.startswith("6"):
        return "6"
    if raw.startswith("5"):
        return "5"
    if re.search(r"\bfr\b|freshman", raw, re.IGNORECASE):
        return "1"
    if re.search(r"\bso\b|sophomore", raw, re.IGNORECASE):
        return "2"
    if re.search(r"\bjr\b|junior", raw, re.IGNORECASE):
        return "3"
    if re.search(r"\bsr\b|senior", raw, re.IGNORECASE):
        return "4"
    return _CLASS_YEAR_NORM_MAP.get(class_year_norm)


def _parse_height_in(height_raw) -> int | None:
    if height_raw is None:
        return None
    s = str(height_raw)
    m = re.match(r"(\d+)[' ’-]+(\d+)", s)
    if m:
        return int(m.group(1)) * 12 + int(m.group(2))
    return None


def _register_source(c) -> None:
    c.execute(
        """INSERT INTO sources(source_id, source_name, source_url, license_note, attribution_required,
           approved_for_import, notes) VALUES (?,?,?,?,0,1,?)
           ON CONFLICT(source_id) DO NOTHING""",
        (SOURCE_ID, "Reads Football MASTER Knowledge Feed workbook", "user-provided workbook",
         "Project/user source.",
         "Row-level CFB 2026 roster facts (roster/jersey/position/class/height/weight/hometown/high school/"
         "transfer history), scraped by the user directly from each school's own official athletics site and "
         "consolidated into MASTER_RELATIONSHIPS. See tools/data_refresh/cfb_2026_roster_workbook_import.py."),
    )


def _read_master_relationships(workbook_path: Path) -> tuple[list[str], list[tuple]]:
    import openpyxl

    wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    ws = wb["MASTER_RELATIONSHIPS"]
    rows = list(ws.iter_rows(values_only=True))
    header = list(rows[0])
    return header, rows[1:]


_FIELD_RELATIONSHIPS = {
    "PLAYS_POSITION": "position_raw", "POSITION_GROUP_NORMALIZED": "position_group",
    "WEARS_JERSEY_NUMBER": "jersey", "ACADEMIC_YEAR": "academic_year_raw",
    "CLASS_YEAR_NORMALIZED": "class_year_norm", "HEIGHT": "height_raw",
    "HEIGHT_INCHES": "height_in", "WEIGHT_LB": "weight_lb",
    "FROM_HOMETOWN": "hometown", "HOME_STATE": "home_state",
    "ATTENDED_HIGH_SCHOOL": "high_school", "PREVIOUS_COLLEGE": "previous_college",
}


def consolidate_2026_roster_rows(workbook_path: Path = DEFAULT_WORKBOOK_PATH) -> list[dict]:
    """Real, from-source consolidation: one dict per (player, team) built
    from every real MASTER_RELATIONSHIPS row that describes that player,
    never a pre-baked intermediate file (so a fresh workbook re-run picks
    up real changes)."""
    header, data = _read_master_relationships(workbook_path)
    idx = {h: i for i, h in enumerate(header)}

    players: dict[tuple, dict] = {}
    for r in data:
        if not r or r[idx["relationship_type"]] != "ROSTERED_BY":
            continue
        if r[idx["season"]] != SEASON:
            continue
        key = (r[idx["entity_1"]], r[idx["entity_2"]])
        players[key] = {
            "name": r[idx["entity_1"]], "team": r[idx["entity_2"]],
            "source_url": r[idx["source_url"]], "source_name": r[idx["source_name"]],
        }

    name_to_teams: dict[str, set] = {}
    for (name, team) in players:
        name_to_teams.setdefault(name, set()).add(team)

    for r in data:
        if not r:
            continue
        rel = r[idx["relationship_type"]]
        if rel not in _FIELD_RELATIONSHIPS:
            continue
        name = r[idx["entity_1"]]
        if name not in name_to_teams:
            continue
        for team in name_to_teams[name]:
            key = (name, team)
            if key in players:
                players[key][_FIELD_RELATIONSHIPS[rel]] = r[idx["value_stat"]]

    return list(players.values())


def resolve_player_id(c, name: str, school_id: str) -> tuple[str | None, str]:
    """Returns (cfb_player_id_or_None, resolution) where resolution is one
    of RESOLVED_UNIQUE / RESOLVED_DISAMBIGUATED / AMBIGUOUS_UNRESOLVED /
    NEW_PLAYER. Never guesses on a real ambiguous case."""
    matches = c.execute(
        "SELECT cfb_player_id FROM canonical_cfb_players WHERE display_name=?", (name,)
    ).fetchall()
    if not matches:
        return None, "NEW_PLAYER"
    if len(matches) == 1:
        return matches[0]["cfb_player_id"], "RESOLVED_UNIQUE"
    for m in matches:
        pid = m["cfb_player_id"]
        hit = c.execute(
            "SELECT 1 FROM cfb_roster_seasons_real WHERE cfb_player_id=? AND school_id=? AND season IN (2024,2025)",
            (pid, school_id),
        ).fetchone()
        if hit:
            return pid, "RESOLVED_DISAMBIGUATED"
    return None, "AMBIGUOUS_UNRESOLVED"


def _new_player_id(name: str, team: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", f"{name}_{team}").strip("_").upper()
    return f"WORKBOOK_CFB:{slug}"


def _publish(c, bid: str, records: list[dict]) -> dict:
    counts = {"published_existing": 0, "published_new": 0, "ambiguous_skipped": 0, "unmapped_school": 0}
    for rec in records:
        school_id = import_data.resolve_school(c, rec["team"])
        if not school_id:
            c.execute(
                "INSERT INTO qa_issues(severity,entity_type,entity_id,field_name,issue_type,detail) "
                "VALUES('WARN','cfb_2026_roster_workbook_row',?,'school_id','UNMAPPED_SCHOOL',?)",
                (rec["name"], f"Could not map workbook team '{rec['team']}' to a known school"),
            )
            counts["unmapped_school"] += 1
            continue

        pid, resolution = resolve_player_id(c, rec["name"], school_id)
        if resolution == "AMBIGUOUS_UNRESOLVED":
            c.execute(
                "INSERT INTO qa_issues(severity,entity_type,entity_id,field_name,issue_type,detail) "
                "VALUES('WARN','cfb_2026_roster_workbook_row',?,'cfb_player_id','AMBIGUOUS_NAME_MATCH',?)",
                (rec["name"], f"'{rec['name']}' matches multiple canonical_cfb_players and none has a real "
                              f"2024/2025 roster row at {rec['team']} -- not auto-resolved."),
            )
            counts["ambiguous_skipped"] += 1
            continue

        height_in = rec.get("height_in") if isinstance(rec.get("height_in"), int) else _parse_height_in(rec.get("height_raw"))
        weight_lb = rec.get("weight_lb") if isinstance(rec.get("weight_lb"), int) else None
        position = _normalize_position(rec.get("position_raw")) or rec.get("position_group")
        class_year = _map_class_year(rec.get("academic_year_raw"), rec.get("class_year_norm"))
        jersey = rec.get("jersey") if isinstance(rec.get("jersey"), int) else None

        if resolution == "NEW_PLAYER":
            pid = _new_player_id(rec["name"], rec["team"])
            hometown_city, hometown_state = None, rec.get("home_state")
            if rec.get("hometown") and "," in str(rec["hometown"]):
                hometown_city = str(rec["hometown"]).split(",")[0].strip()
            c.execute(
                """INSERT INTO canonical_cfb_players(cfb_player_id, espn_athlete_id, display_name, first_name,
                   last_name, height_in, weight_lb, hometown_city, hometown_state, hometown_country,
                   verification_status, source_id)
                   VALUES (?,NULL,?,?,?,?,?,?,?,'USA','SOURCE_BACKED',?)
                   ON CONFLICT(cfb_player_id) DO NOTHING""",
                (pid, rec["name"], rec["name"].split(" ")[0], rec["name"].split(" ")[-1],
                 height_in, weight_lb, hometown_city, hometown_state, SOURCE_ID),
            )
            counts["published_new"] += 1
        else:
            counts["published_existing"] += 1

        c.execute(
            """INSERT INTO cfb_roster_seasons_real(season, school_id, cfb_player_id, jersey_number, class_year,
               position, height_in, weight_lb, verification_status, source_id)
               VALUES (?,?,?,?,?,?,?,?,'SOURCE_BACKED',?)
               ON CONFLICT(season, school_id, cfb_player_id) DO UPDATE SET
                 jersey_number=excluded.jersey_number, class_year=excluded.class_year,
                 position=excluded.position, height_in=COALESCE(excluded.height_in, cfb_roster_seasons_real.height_in),
                 weight_lb=COALESCE(excluded.weight_lb, cfb_roster_seasons_real.weight_lb),
                 verification_status='SOURCE_BACKED', source_id=?""",
            (SEASON, school_id, pid, jersey, class_year, position, height_in, weight_lb, SOURCE_ID, SOURCE_ID),
        )
    return counts


def run_cfb_2026_roster_workbook_import(workbook_path: Path = DEFAULT_WORKBOOK_PATH) -> dict:
    if not Path(workbook_path).is_file():
        return {"status": "BLOCKED_WORKBOOK_NOT_FOUND", "workbook_path": str(workbook_path)}

    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    baseline_players = c.execute("SELECT COUNT(*) FROM canonical_cfb_players").fetchone()[0]
    baseline_rosters = c.execute(
        "SELECT COUNT(*) FROM cfb_roster_seasons_real WHERE season=?", (SEASON,)
    ).fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup_or_finish_failed(run_id)

    try:
        records = consolidate_2026_roster_rows(workbook_path)

        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        _register_source(c)  # must precede import_batches insert -- source_id is a real FK
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
            counts = _publish(c, bid, records)
            published = counts["published_existing"] + counts["published_new"]
            rejected = counts["ambiguous_skipped"] + counts["unmapped_school"]
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
            c.close()  # release the file lock before the outer handler restores/reopens it
            raise

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="cfb_roster_seasons_real", rows_published=published,
                rows_rejected=rejected, rows_read=len(records), min_row_count_floor=baseline_rosters,
            )
            player_count_after = c.execute("SELECT COUNT(*) FROM canonical_cfb_players").fetchone()[0]
            if player_count_after < baseline_players:
                raise safety.SanityCheckFailure(
                    f"canonical_cfb_players dropped from {baseline_players} to {player_count_after} -- refusing"
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
    print(json.dumps(run_cfb_2026_roster_workbook_import(), indent=2, default=str))
