"""One-time backfill: real CFB offensive/defensive coordinators for a
disclosed sample of major programs (Knowledge Expansion Batch 2), from
each program's own "SEASON School_Name football team" Wikipedia page,
which carries a real per-season coaching-staff table (Name / Position /
tenure).

--- REAL, DISCLOSED SCOPE: A NAMED 20-PROGRAM SAMPLE, NOT ALL FBS ---
There are ~134 real FBS programs; no consolidated Wikipedia page lists
CFB coordinators across all of them the way the NFL's two "List of
current..." pages do. Fetching a school-season page per program does not
scale to FBS-wide coverage in this batch, so PROGRAMS below is an
explicit, hand-picked list of well-known programs (real `schools` rows,
verified to resolve before this module was written) -- this is a real,
usable sample, disclosed as a sample, never presented as FBS-wide.

--- CO-COORDINATOR / RAW TITLE PRESERVATION ---
The source table's Position column is real, sometimes-combined free text
(e.g. "Offensive coordinator / Quarterbacks coach", "Co-Defensive
coordinator / Safeties coach"). `title_raw` keeps the exact string;
`normalized_role` is only ever OFFENSIVE_COORDINATOR / CO_OFFENSIVE_
COORDINATOR / DEFENSIVE_COORDINATOR / CO_DEFENSIVE_COORDINATOR /
SPECIAL_TEAMS_COORDINATOR / HEAD_COACH -- assigned by real substring
matches on the raw title, never collapsing a co-coordinator into a sole
coordinator or dropping the "co-" distinction.
"""
from __future__ import annotations

import hashlib
import re
import sys
import time
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "CFB"
DATASET = "cfb_coordinators_wikipedia"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
RETRIEVED_AT = "2026-08-18"
USER_AGENT = "ReadsFootballResearch/1.0 (educational trivia project; contact via repo)"
SEASON = 2025  # most recently completed real CFB season as of retrieval

# school_name (must match `schools.school_name` exactly) -> Wikipedia
# "Season_Nickname_football_team" title. Verified to resolve in `schools`
# before this list was finalized.
PROGRAMS = {
    "Georgia": "2025_Georgia_Bulldogs_football_team",
    "Alabama": "2025_Alabama_Crimson_Tide_football_team",
    "Ohio State": "2025_Ohio_State_Buckeyes_football_team",
    "Michigan": "2025_Michigan_Wolverines_football_team",
    "Texas": "2025_Texas_Longhorns_football_team",
    "Oklahoma": "2025_Oklahoma_Sooners_football_team",
    "Oregon": "2025_Oregon_Ducks_football_team",
    "Penn State": "2025_Penn_State_Nittany_Lions_football_team",
    "LSU": "2025_LSU_Tigers_football_team",
    "Clemson": "2025_Clemson_Tigers_football_team",
    "Notre Dame": "2025_Notre_Dame_Fighting_Irish_football_team",
    "Florida State": "2025_Florida_State_Seminoles_football_team",
    "USC": "2025_USC_Trojans_football_team",
    "Miami": "2025_Miami_Hurricanes_football_team",
    "Tennessee": "2025_Tennessee_Volunteers_football_team",
    "Texas A&M": "2025_Texas_A%26M_Aggies_football_team",
    "Auburn": "2025_Auburn_Tigers_football_team",
    "Wisconsin": "2025_Wisconsin_Badgers_football_team",
    "Florida": "2025_Florida_Gators_football_team",
    "Oklahoma State": "2025_Oklahoma_State_Cowboys_football_team",
}

ROLE_PATTERNS = [
    (re.compile(r"co-?\s*offensive coordinator", re.I), "CO_OFFENSIVE_COORDINATOR"),
    (re.compile(r"offensive coordinator", re.I), "OFFENSIVE_COORDINATOR"),
    (re.compile(r"co-?\s*defensive coordinator", re.I), "CO_DEFENSIVE_COORDINATOR"),
    (re.compile(r"defensive coordinator", re.I), "DEFENSIVE_COORDINATOR"),
    (re.compile(r"special teams coordinator", re.I), "SPECIAL_TEAMS_COORDINATOR"),
    (re.compile(r"head coach", re.I), "HEAD_COACH"),
]


def _gen_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"


def _cfb_coach_id_for_name(name: str) -> str:
    slug = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")
    return f"CFB_COACH_{slug}"


def _classify_role(title_raw: str) -> str | None:
    for pattern, role in ROLE_PATTERNS:
        if pattern.search(title_raw):
            return role
    return None


def _fetch_soup(title: str) -> BeautifulSoup:
    req = urllib.request.Request(f"https://en.wikipedia.org/wiki/{title}", headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=30).read()
    soup = BeautifulSoup(html, "html.parser")
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    return soup


def _parse_staff_table(soup: BeautifulSoup) -> list[dict]:
    """A team-season page can carry SEVERAL tables sharing the exact
    'Name | Position | ...' header shape (roster, injury report,
    portal-out, portal-in, real coaching staff) -- real, confirmed by
    direct inspection (Alabama's page alone has 4 such tables). Rather
    than trusting the first match, every candidate is scored by how many
    rows contain a real "coach" mention, and the highest-scoring table
    wins -- the real staff table always has many (Georgia: 13, Alabama:
    18), while a roster/portal table sharing the header shape has at most
    an incidental 0-1."""
    best_rows: list[dict] = []
    best_score = 0
    for t in soup.find_all("table", class_="wikitable"):
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        if not headers or headers[0] != "Name" or "Position" not in headers:
            continue
        rows = t.find_all("tr")
        out = []
        for r in rows[1:]:
            cells = r.find_all("td")
            if len(cells) < 2:
                continue
            name = cells[0].get_text(" ", strip=True)
            title_raw = cells[1].get_text(" ", strip=True)
            if not name or not title_raw:
                continue
            out.append({"coach_name": name, "title_raw": title_raw})
        if not out:
            continue
        coach_like = sum(1 for row in out if "coach" in row["title_raw"].lower())
        if coach_like > best_score:
            best_score, best_rows = coach_like, out
    if best_score < 3:
        return []  # no table looked like a real coaching staff -- honestly report a miss, don't guess
    return best_rows


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_coordinators (
            coordinator_id TEXT PRIMARY KEY,
            season INTEGER NOT NULL,
            school_id TEXT NOT NULL,
            normalized_role TEXT NOT NULL,
            title_raw TEXT NOT NULL,
            coach_id TEXT NOT NULL,
            coach_name_raw TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            UNIQUE(season, school_id, normalized_role, coach_name_raw)
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
            "CC BY-SA 4.0; secondary structured source, same approval basis as other "
            "tools/data_refresh Wikipedia modules.",
            1, 1,
            f"Pages used: one 'SEASON School football team' page per program in PROGRAMS "
            f"(20-program disclosed sample, not FBS-wide); retrieved {RETRIEVED_AT}.",
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

        report = {
            "programs_attempted": 0, "programs_succeeded": 0, "skipped_programs": {},
            "total_rows": 0, "role_counts": {}, "new_coach_identities_created": 0,
        }

        for school_name, title in PROGRAMS.items():
            report["programs_attempted"] += 1
            school_row = c.execute("SELECT school_id FROM schools WHERE school_name=?", (school_name,)).fetchone()
            if not school_row:
                report["skipped_programs"][school_name] = "SCHOOL_NOT_FOUND_IN_CANONICAL_SCHOOLS"
                continue
            school_id = school_row["school_id"]

            try:
                soup = _fetch_soup(title)
            except Exception as exc:
                report["skipped_programs"][school_name] = f"FETCH_FAILED: {exc!r}"
                continue

            staff = _parse_staff_table(soup)
            if not staff:
                report["skipped_programs"][school_name] = "NO_RECOGNIZED_STAFF_TABLE"
                continue

            report["programs_succeeded"] += 1
            for row in staff:
                role = _classify_role(row["title_raw"])
                if role is None or role == "HEAD_COACH":
                    continue  # HEAD_COACH already covered by existing cfb_coaches infra; skip non-coordinator staff
                coach_id = _cfb_coach_id_for_name(row["coach_name"])
                existing = c.execute("SELECT cfb_coach_id FROM cfb_coaches WHERE cfb_coach_id=?", (coach_id,)).fetchone()
                if not existing:
                    c.execute(
                        "INSERT INTO cfb_coaches(cfb_coach_id, coach_name, school_context, source_contexts, status) "
                        "VALUES (?,?,?,?,?)",
                        (coach_id, row["coach_name"], school_name, "Wikipedia_Coordinators_Batch2", "WIKIPEDIA_STRUCTURED_SECONDARY"),
                    )
                    report["new_coach_identities_created"] += 1

                coordinator_id = _gen_id("CFBCOORD", str(SEASON), school_id, role, row["coach_name"])
                c.execute(
                    """INSERT INTO cfb_coordinators(
                        coordinator_id, season, school_id, normalized_role, title_raw,
                        coach_id, coach_name_raw, source_id, source_page, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(season, school_id, normalized_role, coach_name_raw) DO NOTHING""",
                    (coordinator_id, SEASON, school_id, role, row["title_raw"], coach_id, row["coach_name"],
                     SOURCE_ID, f"https://en.wikipedia.org/wiki/{title}", RETRIEVED_AT,
                     "WIKIPEDIA_STRUCTURED_SECONDARY"),
                )
                report["total_rows"] += 1
                report["role_counts"][role] = report["role_counts"].get(role, 0) + 1

                c.execute(
                    """INSERT INTO relationships(subject_type, subject_id, predicate,
                       object_type, object_id, season_start, season_end, source_id, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                       DO NOTHING""",
                    ("cfb_coach", coach_id, "SERVED_AS_" + role, "cfb_school", school_id,
                     SEASON, SEASON, SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY"),
                )
            time.sleep(0.2)

        c.commit()

        safety.run_post_refresh_sanity_checks(
            c, table="cfb_coordinators", rows_published=report["total_rows"],
            rows_rejected=0, rows_read=report["total_rows"], min_row_count_floor=15,
        )

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=report["total_rows"], rows_imported=report["total_rows"],
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
