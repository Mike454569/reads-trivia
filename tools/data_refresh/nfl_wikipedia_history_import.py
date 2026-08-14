"""One-time historical backfill: NFL Super Bowl championships + Super Bowl MVP
+ AP MVP/OPOY/DPOY/OROY/DROY awards, from Wikipedia structured tables.

Not a recurring scheduled refresh like the other tools/data_refresh/*.py
modules (Wikipedia's own historical tables don't change season-to-season
the way live stat feeds do) -- but it follows the exact same production
safety pattern as every other script that mutates this DB: verified backup
before writing, run-tracking via refresh_runs, post-write sanity checks,
automatic restore-from-backup on any failure.

Why Wikipedia at all, and why only as a SECONDARY source: this Engine's
championship history (season_standings.playoff_result) is NFLVERSE_DATA-
backed but only covers 2002+; the user explicitly asked for pre-1999
championship/award history and explicitly authorized Wikipedia as a
"secondary structured historical source, not the unquestioned source of
truth" -- meaning: never overwrite an existing NFLVERSE_DATA fact, always
log any disagreement instead, and keep full page/retrieval provenance on
every row so a stronger source can supersede it later.

Real, confirmed identity-coverage boundary (not a bug in this script's
matching logic -- checked directly against canonical_players.birth_date,
which bottoms out at 1960, and team_aliases/franchises, which only cover
seasons 2002+): resolution rate is consistently 85-96% for award seasons
>= 2000 and 30-60% for seasons before that, because canonical_players and
team_aliases are themselves NFLVERSE-sourced and NFLVERSE's own player/
roster identity data does not reach back further than roughly the 1999-2002
window. Older award winners (Jim Brown, Johnny Unitas, Bart Starr, etc.)
are simply not present anywhere in this Engine's identity system yet --
raw values are still recorded (source-backed, human-readable), just with
player_id/franchise_id left NULL rather than force-matched.

Two new raw/provenance tables (nfl_championship_events, nfl_season_awards)
hold EVERY scraped row, resolved or not. Only resolved rows -- meaning a
real canonical_players.player_id or franchises.franchise_id was found via
an unambiguous match -- get a corresponding row in the shared
`relationships` table, because that is the layer the Creator actually
queries; an unresolved raw fact sitting only in the provenance table is
honestly not yet Creator-usable, and is reported as such rather than
force-connected.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR

LEAGUE = "NFL"
DATASET = "nfl_wikipedia_history"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
RETRIEVED_AT = "2026-08-13"

SOURCE_PAGES = {
    "championships": "https://en.wikipedia.org/wiki/List_of_Super_Bowl_champions",
    "sb_mvp": "https://en.wikipedia.org/wiki/Super_Bowl_Most_Valuable_Player",
    "ap_mvp": "https://en.wikipedia.org/wiki/List_of_NFL_Most_Valuable_Player_awards",
    "opoy": "https://en.wikipedia.org/wiki/AP_NFL_Offensive_Player_of_the_Year",
    "dpoy": "https://en.wikipedia.org/wiki/AP_NFL_Defensive_Player_of_the_Year",
    "oroy": "https://en.wikipedia.org/wiki/AP_NFL_Rookie_of_the_Year#Offensive",
    "droy": "https://en.wikipedia.org/wiki/AP_NFL_Rookie_of_the_Year#Defensive",
}

AWARD_TYPE_MAP = {
    "sb_mvp": ("SB_MVP", "NFL"),
    "ap_mvp": ("AP_MVP", "AP"),
    "opoy": ("AP_OPOY", "AP"),
    "dpoy": ("AP_DPOY", "AP"),
    "oroy": ("AP_OROY", "AP"),
    "droy": ("AP_DROY", "AP"),
}

POSITION_FULL_TO_ABBR = {
    "quarterback": {"QB"}, "running back": {"RB", "FB"}, "fullback": {"FB"},
    "wide receiver": {"WR"}, "tight end": {"TE"},
    "offensive tackle": {"OT", "LT", "RT", "T"}, "offensive guard": {"OG", "LG", "RG", "G"},
    "center": {"C"}, "guard": {"LG", "RG", "G"}, "tackle": {"LT", "RT", "T"},
    "defensive end": {"DE", "LDE", "RDE"}, "defensive tackle": {"DT", "LDT", "RDT", "NT"},
    "nose tackle": {"NT"}, "linebacker": {"LB", "MLB", "OLB", "ILB", "LOLB", "ROLB", "LILB", "RILB"},
    "cornerback": {"CB", "LCB", "RCB"}, "safety": {"S", "SS", "FS"},
    "defensive back": {"DB", "CB", "S", "SS", "FS"},
    "punter": {"P"}, "kicker": {"K"}, "long snapper": {"LS"},
    "defensive lineman": {"DL", "DE", "DT", "NT"}, "offensive lineman": {"OL", "OT", "OG", "C", "T", "G"},
}


def _gen_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"


def _normalize_team(name: str) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.replace(".", "")).strip()


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_championship_events (
            event_id TEXT PRIMARY KEY,
            sb_number TEXT NOT NULL,
            sb_title TEXT,
            season INTEGER NOT NULL,
            game_date TEXT,
            winner_name_raw TEXT NOT NULL,
            winner_franchise_id TEXT,
            winner_team_code TEXT,
            loser_name_raw TEXT NOT NULL,
            loser_franchise_id TEXT,
            loser_team_code TEXT,
            winner_score INTEGER,
            loser_score INTEGER,
            overtime INTEGER,
            venue TEXT,
            city TEXT,
            resolution_method TEXT,
            conflict_flag INTEGER NOT NULL DEFAULT 0,
            conflict_note TEXT,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_season_awards (
            award_id TEXT PRIMARY KEY,
            award_type TEXT NOT NULL,
            awarding_body TEXT NOT NULL,
            season INTEGER NOT NULL,
            player_name_raw TEXT NOT NULL,
            player_id TEXT,
            team_name_raw TEXT,
            team_franchise_id TEXT,
            team_code TEXT,
            position_raw TEXT,
            college_raw TEXT,
            resolution_method TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL
        )
    """)
    c.commit()


def _resolve_team(c, name_raw: str, season: int):
    name = _normalize_team(name_raw)
    row = c.execute(
        "SELECT franchise_id, team_code FROM team_aliases "
        "WHERE REPLACE(full_name,'.','')=? AND ? BETWEEN season_start AND season_end",
        (name, season),
    ).fetchone()
    if row:
        return row[0], row[1], "TEAM_ALIASES_EXACT_SEASON_MATCH"
    return None, None, "NO_ALIAS_COVERAGE_FOR_SEASON"


def _resolve_player(c, name_raw: str, position_raw: str | None):
    name = name_raw.strip()
    rows = c.execute(
        "SELECT player_id, primary_position FROM canonical_players WHERE display_name=?", (name,)
    ).fetchall()
    if len(rows) == 1:
        return rows[0][0], "UNIQUE_NAME"
    if len(rows) == 0:
        drow = c.execute(
            "SELECT DISTINCT pfr_id FROM nfl_players_draft WHERE player_name=? AND pfr_id IS NOT NULL", (name,)
        ).fetchall()
        if len(drow) == 1:
            crow = c.execute("SELECT player_id FROM canonical_players WHERE pfr_id=?", (drow[0][0],)).fetchone()
            if crow:
                return crow[0], "UNIQUE_NAME_VIA_DRAFT_TABLE"
        return None, "NO_NAME_MATCH"
    pos_key = (position_raw or "").strip().lower()
    allowed = POSITION_FULL_TO_ABBR.get(pos_key)
    if allowed:
        narrowed = [r for r in rows if r[1] in allowed]
        if len(narrowed) == 1:
            return narrowed[0][0], "NAME+POSITION"
    return None, f"AMBIGUOUS_NAME_{len(rows)}_CANDIDATES"


def _college_for_player(c, player_id: str | None) -> str | None:
    if not player_id:
        return None
    row = c.execute(
        "SELECT college FROM nfl_players_draft WHERE pfr_id=(SELECT pfr_id FROM canonical_players WHERE player_id=?) "
        "AND college IS NOT NULL LIMIT 1",
        (player_id,),
    ).fetchone()
    return row[0] if row else None


def _ensure_source_registered(c) -> None:
    c.execute(
        """INSERT INTO sources(source_id, source_name, source_url, license_note, attribution_required,
           approved_for_import, notes)
           VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(source_id) DO NOTHING""",
        (
            SOURCE_ID,
            "Wikipedia (structured tables)",
            "https://en.wikipedia.org",
            "CC BY-SA 4.0; used only as a secondary structured historical source per explicit user "
            "instruction -- never overwrites a stronger existing source-backed fact.",
            1, 1,
            "Pages used: " + json.dumps(SOURCE_PAGES) + f"; retrieved {RETRIEVED_AT}; parsed with "
            "BeautifulSoup against the real rendered HTML table structure (rowspan-aware), not "
            "AI-summarized, specifically to avoid transcription risk on large fact-dense tables.",
        ),
    )


def run_import(dry_run: bool = False) -> dict:
    data = json.load(open(Path(__file__).resolve().parent / "_wikipedia_history_source.json"))

    conn_path = str(ENGINE_DIR / "reads_football_v4.0.sqlite")
    import sqlite3
    c = sqlite3.connect(conn_path)
    c.execute("PRAGMA foreign_keys=ON")

    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    backup = safety.create_verified_backup()

    try:
        _ensure_schema(c)
        _ensure_source_registered(c)

        report = {
            "championships": {"total": 0, "winner_resolved": 0, "loser_resolved": 0, "conflicts": []},
            "awards": {},
        }

        # ---- championships ----
        for row in data["championships"]:
            report["championships"]["total"] += 1
            wid, wcode, wmethod = _resolve_team(c, row["winner_name"], row["season"])
            lid, lcode, lmethod = _resolve_team(c, row["loser_name"], row["season"])
            if wid:
                report["championships"]["winner_resolved"] += 1
            if lid:
                report["championships"]["loser_resolved"] += 1

            conflict_flag = 0
            conflict_note = None
            if wcode:
                existing = c.execute(
                    "SELECT playoff_result FROM season_standings WHERE season=? AND team_code=?",
                    (row["season"], wcode),
                ).fetchone()
                if existing and existing[0] != "WonSB":
                    conflict_flag = 1
                    conflict_note = (
                        f"season_standings.playoff_result for {wcode}/{row['season']} = "
                        f"{existing[0]!r}, expected WonSB per Wikipedia -- NOT overwritten, logged only"
                    )

            event_id = _gen_id("CHAMP", row["sb_number"], str(row["season"]))
            c.execute(
                """INSERT INTO nfl_championship_events(
                    event_id, sb_number, sb_title, season, game_date,
                    winner_name_raw, winner_franchise_id, winner_team_code,
                    loser_name_raw, loser_franchise_id, loser_team_code,
                    winner_score, loser_score, overtime, venue, city,
                    resolution_method, conflict_flag, conflict_note,
                    source_id, source_page, retrieved_at, verification_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(event_id) DO NOTHING""",
                (
                    event_id, row["sb_number"], row["sb_title"], row["season"], row["date"],
                    row["winner_name"], wid, wcode,
                    row["loser_name"], lid, lcode,
                    row["winner_score"], row["loser_score"], int(row["overtime"]), row["venue"], row["city"],
                    f"winner={wmethod};loser={lmethod}", conflict_flag, conflict_note,
                    SOURCE_ID, SOURCE_PAGES["championships"], RETRIEVED_AT, "WIKIPEDIA_STRUCTURED_SECONDARY",
                ),
            )
            if conflict_flag:
                report["championships"]["conflicts"].append(conflict_note)

            if wid and wcode:
                for predicate in ("WON_CHAMPIONSHIP", "PLAYED_IN_CHAMPIONSHIP"):
                    c.execute(
                        """INSERT INTO relationships(subject_type, subject_id, predicate,
                           object_type, object_id, season_start, season_end, source_id, verification_status)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                           DO NOTHING""",
                        (
                            "team", wcode, predicate, "nfl_championship_event", event_id,
                            row["season"], row["season"], SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY",
                        ),
                    )
            if lid and lcode:
                for predicate in ("LOST_CHAMPIONSHIP", "PLAYED_IN_CHAMPIONSHIP"):
                    c.execute(
                        """INSERT INTO relationships(subject_type, subject_id, predicate,
                           object_type, object_id, season_start, season_end, source_id, verification_status)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                           DO NOTHING""",
                        (
                            "team", lcode, predicate, "nfl_championship_event", event_id,
                            row["season"], row["season"], SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY",
                        ),
                    )

        # ---- awards ----
        award_field_map = {
            "sb_mvp": ("player_name", "position", "team", "college"),
            "ap_mvp": ("player_name", None, None, None),
            "opoy": ("player_name", "position", "team", None),
            "dpoy": ("player_name", "position", "team", None),
            "oroy": ("player_name", "position", "team", None),
            "droy": ("player_name", "position", "team", None),
        }
        for award_key, (name_f, pos_f, team_f, college_f) in award_field_map.items():
            award_type, awarding_body = AWARD_TYPE_MAP[award_key]
            stats = {"total": 0, "resolved": 0}
            for row in data[award_key]:
                stats["total"] += 1
                pos_raw = row.get(pos_f) if pos_f else None
                team_raw = row.get(team_f) if team_f else None
                college_raw = row.get(college_f) if college_f else None
                pid, pmethod = _resolve_player(c, row[name_f], pos_raw)
                if pid:
                    stats["resolved"] += 1
                    if not college_raw:
                        college_raw = _college_for_player(c, pid)

                tid = tcode = None
                if team_raw:
                    tid, tcode, _tm = _resolve_team(c, team_raw, row["season"])

                award_id = _gen_id("AWARD", award_type, str(row["season"]), row[name_f])
                c.execute(
                    """INSERT INTO nfl_season_awards(
                        award_id, award_type, awarding_body, season, player_name_raw, player_id,
                        team_name_raw, team_franchise_id, team_code, position_raw, college_raw,
                        resolution_method, source_id, source_page, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(award_id) DO NOTHING""",
                    (award_id, award_type, awarding_body, row["season"], row[name_f], pid,
                     team_raw, tid, tcode, pos_raw, college_raw,
                     pmethod, SOURCE_ID, SOURCE_PAGES[award_key], RETRIEVED_AT, "WIKIPEDIA_STRUCTURED_SECONDARY"),
                )

                if pid:
                    predicate = "WON_SUPER_BOWL_MVP" if award_key == "sb_mvp" else "WON_AWARD"
                    c.execute(
                        """INSERT INTO relationships(subject_type, subject_id, predicate,
                           object_type, object_id, season_start, season_end, source_id, verification_status)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                           DO NOTHING""",
                        (
                            "nfl_player", pid, predicate, "nfl_award", award_id,
                            row["season"], row["season"], SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY",
                        ),
                    )
            report["awards"][award_key] = stats

        c.commit()

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_championship_events", rows_published=report["championships"]["total"],
            rows_rejected=0, rows_read=report["championships"]["total"], min_row_count_floor=50,
        )

        total_rows = report["championships"]["total"] + sum(a["total"] for a in report["awards"].values())
        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=total_rows, rows_imported=total_rows, rows_rejected=0,
            detail=report,
        )
        c.close()
        return {"status": "SUCCESS", "run_id": run_id, "backup_id": backup["backup_id"], **report}
    except Exception as exc:
        try:
            c.rollback()
            c.close()
        except Exception:
            pass
        restore_info = safety.restore_from_backup(backup["path"])
        c2 = sqlite3.connect(conn_path)
        safety.finish_run(c2, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                           failure_reason=repr(exc), detail={"restore": restore_info})
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(exc), "backup": backup}


if __name__ == "__main__":
    result = run_import()
    print(json.dumps(result, indent=2, default=str))
