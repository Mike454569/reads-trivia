"""One-time historical backfill: Pro Football Hall of Fame inductees
(Knowledge Expansion Batch 2), from Wikipedia's real, structured
"List of Pro Football Hall of Fame inductees" table.

Not a recurring scheduled refresh (the HOF class list only grows by ~5-8
new names a year, at a known August date) -- follows the same production
safety pattern as every other tools/data_refresh/*.py module: verified
backup before writing, run-tracking via refresh_runs, post-write sanity
checks, automatic restore-from-backup on any failure. Modeled directly on
nfl_wikipedia_history_import.py's already-approved use of Wikipedia as a
secondary structured historical source.

--- PLAYER VS NON-PLAYER INDUCTEES (real, disclosed scope decision) ---
The source table's `Position` column includes real non-player roles
(Coach, Founder, General manager, Team owner, NFL commissioner, Scout,
Supervisor of officials, etc. -- 33 distinct non-player position strings
confirmed by direct inspection). Per instruction, these are NOT forced
into the PLAYER relationship: this module classifies every inductee's raw
position and routes PLAYER-position rows into `nfl_hof_inductees` with a
real `canonical_players` identity join attempt, while NON-PLAYER rows are
recorded in the same raw table (full provenance kept) but explicitly
flagged `is_player=0` and never identity-resolved against
`canonical_players` or connected via a PLAYER relationship.

--- MULTI-TEAM ROWS (rowspan continuation) ---
An inductee who played for multiple teams gets one primary row (name,
class, position, first team, years) followed by 0+ continuation rows
(team, years only, via HTML rowspan) -- detected here by real cell count
(5 cells = new inductee, 2 cells = continuation team row for the most
recently seen inductee), not by any heuristic on the text itself.
"""
from __future__ import annotations

import hashlib
import re
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.data_refresh.nfl_wikipedia_history_import import (  # noqa: E402
    _resolve_player, POSITION_FULL_TO_ABBR,
)

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "NFL"
DATASET = "nfl_hof_wikipedia"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
SOURCE_PAGE = "https://en.wikipedia.org/wiki/List_of_Pro_Football_Hall_of_Fame_inductees"
RETRIEVED_AT = "2026-08-18"
USER_AGENT = "ReadsFootballResearch/1.0 (educational trivia project; contact via repo)"

# Real, non-player role keywords confirmed by direct inspection of the
# source table's 88 distinct Position strings. A position is NON_PLAYER
# if its FIRST role token matches one of these -- e.g. "Coach/general
# manager" -> non-player, but "Halfback/coach" -> player (halfback is the
# primary/first-listed role), matching how the source itself orders roles.
NON_PLAYER_FIRST_TOKENS = {
    "coach", "founder", "general manager", "nfl commissioner", "nfl co-organizer",
    "scout", "supervisor of officials", "team administrator", "team owner",
    "technical advisor on rules, supervisor of officials", "director of player personnel",
    "personnel administrator", "vp of player personnel", "afl co-founder",
    "nfl films co-founder",
}

FOOTNOTE_RE = re.compile(r"[\*\^†§\[\]0-9]+$")


def _clean_name(raw: str) -> str:
    """Strips trailing Wikipedia footnote markers (**, ^, †, §, [3]) --
    these are real citation markers on the source page, not part of the
    person's actual name."""
    name = raw.strip()
    name = re.sub(r"\s*\[\d+\]\s*$", "", name)
    name = re.sub(r"[\*\^†§]+\s*$", "", name)
    return name.strip()


def _classify(position_raw: str) -> str:
    first_token = re.split(r"[/,]", position_raw)[0].strip().lower()
    if first_token in NON_PLAYER_FIRST_TOKENS:
        return "NON_PLAYER"
    return "PLAYER"


def _gen_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"


def _fetch_soup(url: str) -> BeautifulSoup:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=30).read()
    return BeautifulSoup(html, "html.parser")


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_hof_inductees (
            hof_id TEXT PRIMARY KEY,
            inductee_name_raw TEXT NOT NULL,
            class_year INTEGER NOT NULL,
            position_raw TEXT NOT NULL,
            is_player INTEGER NOT NULL,
            player_id TEXT,
            resolution_method TEXT NOT NULL,
            primary_team_raw TEXT,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            UNIQUE(inductee_name_raw, class_year)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_hof_inductee_teams (
            hof_id TEXT NOT NULL,
            team_name_raw TEXT NOT NULL,
            years_raw TEXT,
            team_order INTEGER NOT NULL,
            FOREIGN KEY(hof_id) REFERENCES nfl_hof_inductees(hof_id)
        )
    """)
    c.commit()


def _ensure_source_registered(c) -> None:
    c.execute(
        """INSERT INTO sources(source_id, source_name, source_url, license_note, attribution_required,
           approved_for_import, notes)
           VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(source_id) DO NOTHING""",
        (
            SOURCE_ID, "Wikipedia (structured tables)", "https://en.wikipedia.org",
            "CC BY-SA 4.0; secondary structured historical source, same approval basis as "
            "nfl_wikipedia_history_import.py.",
            1, 1,
            f"Page used: {SOURCE_PAGE}; retrieved {RETRIEVED_AT}; parsed with BeautifulSoup against "
            "the real rendered HTML table (rowspan-aware via cell-count detection), not AI-summarized.",
        ),
    )


def run_import() -> dict:
    conn_path = str(ENGINE_DIR / "reads_football_v4.0.sqlite")
    import sqlite3
    c = sqlite3.connect(conn_path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")

    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    backup = safety.create_verified_backup()

    try:
        _ensure_schema(c)
        _ensure_source_registered(c)

        soup = _fetch_soup(SOURCE_PAGE)
        tables = soup.find_all("table", class_="wikitable")
        main_table = tables[1]  # verified: index 1 is the primary "Inductees" table (784 real <tr>, 387 inductees)

        report = {
            "total_inductee_rows": 0, "player_rows": 0, "non_player_rows": 0,
            "player_identity_resolved": 0, "player_identity_unresolved": 0,
            "class_year_range": [None, None], "unresolved_sample": [],
        }

        current_hof_id = None
        current_order = 0
        years_seen = []

        for r in main_table.find_all("tr")[1:]:
            cells = r.find_all(["td", "th"])
            if len(cells) >= 5:
                name_raw = cells[0].get_text(" ", strip=True)
                name = _clean_name(name_raw)
                if not name:
                    continue
                class_year = int(re.sub(r"\D", "", cells[1].get_text(strip=True))[:4])
                position_raw = cells[2].get_text(" ", strip=True)
                team_raw = cells[3].get_text(" ", strip=True)
                years_raw = cells[4].get_text(" ", strip=True)

                role = _classify(position_raw)
                hof_id = _gen_id("HOF", name, str(class_year))

                pid = None
                method = "NOT_ATTEMPTED_NON_PLAYER"
                if role == "PLAYER":
                    pos_key = re.split(r"[/,]", position_raw)[0].replace(
                        "Pre-Modern Era: Two-Way Performer", "").strip().lower()
                    pid, method = _resolve_player(c, name, pos_key)

                c.execute(
                    """INSERT INTO nfl_hof_inductees(
                        hof_id, inductee_name_raw, class_year, position_raw, is_player,
                        player_id, resolution_method, primary_team_raw,
                        source_id, source_page, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(inductee_name_raw, class_year) DO NOTHING""",
                    (hof_id, name, class_year, position_raw, 1 if role == "PLAYER" else 0,
                     pid, method, team_raw, SOURCE_ID, SOURCE_PAGE, RETRIEVED_AT,
                     "WIKIPEDIA_STRUCTURED_SECONDARY"),
                )
                current_hof_id = hof_id
                current_order = 0
                years_seen.append(class_year)

                c.execute(
                    "INSERT INTO nfl_hof_inductee_teams(hof_id, team_name_raw, years_raw, team_order) VALUES (?,?,?,?)",
                    (hof_id, team_raw, years_raw, current_order),
                )
                current_order += 1

                report["total_inductee_rows"] += 1
                if role == "PLAYER":
                    report["player_rows"] += 1
                    if pid:
                        report["player_identity_resolved"] += 1
                        c.execute(
                            """INSERT INTO relationships(subject_type, subject_id, predicate,
                               object_type, object_id, season_start, season_end, source_id, verification_status)
                               VALUES (?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                               DO NOTHING""",
                            ("nfl_player", pid, "HALL_OF_FAME_INDUCTEE", "nfl_hof_class", str(class_year),
                             class_year, class_year, SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY"),
                        )
                    else:
                        report["player_identity_unresolved"] += 1
                        if len(report["unresolved_sample"]) < 8:
                            report["unresolved_sample"].append({"name": name, "class_year": class_year, "reason": method})
                else:
                    report["non_player_rows"] += 1
            elif len(cells) == 2 and current_hof_id:
                team_raw = cells[0].get_text(" ", strip=True)
                years_raw = cells[1].get_text(" ", strip=True)
                c.execute(
                    "INSERT INTO nfl_hof_inductee_teams(hof_id, team_name_raw, years_raw, team_order) VALUES (?,?,?,?)",
                    (current_hof_id, team_raw, years_raw, current_order),
                )
                current_order += 1

        c.commit()
        if years_seen:
            report["class_year_range"] = [min(years_seen), max(years_seen)]

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_hof_inductees", rows_published=report["total_inductee_rows"],
            rows_rejected=0, rows_read=report["total_inductee_rows"], min_row_count_floor=300,
        )

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=report["total_inductee_rows"], rows_imported=report["total_inductee_rows"],
            rows_rejected=0, detail=report,
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
    import json
    result = run_import()
    print(json.dumps(result, indent=2, default=str))
