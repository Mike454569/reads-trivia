"""One-time backfill: real, CURRENT-SEASON NFL offensive/defensive
coordinators (Knowledge Expansion Batch 2), from Wikipedia's two
consolidated "List of current National Football League ... coordinators"
pages -- the only reliable, single-page, all-32-team source found for
this domain (see module docstring in the Batch 2 completion report for
why deeper history was not attempted).

--- REAL, DISCLOSED SCOPE: CURRENT SEASON ONLY, NOT MULTI-YEAR HISTORY ---
No consolidated historical (multi-season) NFL coordinator source was
found on Wikipedia -- OC/DC assignments before the current season would
require one page fetch per team per season with no consistent structure,
which was ruled out as unreliable at scale (same reasoning as the Pro
Bowl 1951-1971 gap). CURRENT_SEASON below is fixed at ingestion time from
the source pages' own "Since" year data (the modal/most recent year seen
across all 32 teams), not guessed.

--- NO SPECIAL-TEAMS COORDINATOR SOURCE FOUND ---
Wikipedia has no equivalent "List of current ... special teams
coordinators" page (confirmed 404). Not fabricated -- special-teams
coordinator rows simply do not exist in this batch's data, and
`role_counts` in the run report will show zero for that role.

--- COACH IDENTITY REUSE, NOT A NEW IDENTITY SPACE ---
The existing `coaches` table (177 real NFLVERSE-sourced rows, `COACH:` ID
scheme) is reused directly: a coordinator name is matched against it by
exact `coach_name`; if absent, a new `COACH:` row is added using the exact
same ID-generation pattern nflverse itself uses (lowercased,
underscore-joined name) so this stays one identity space, not two
competing ones, with `source_id`/`verification_status` honestly marking
it as Wikipedia-sourced rather than NFLVERSE_DATA.
"""
from __future__ import annotations

import hashlib
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.data_refresh.nfl_wikipedia_history_import import _resolve_team  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "NFL"
DATASET = "nfl_coordinators_wikipedia"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
RETRIEVED_AT = "2026-08-18"
USER_AGENT = "ReadsFootballResearch/1.0 (educational trivia project; contact via repo)"

SOURCE_PAGES = {
    "OFFENSIVE_COORDINATOR": "List_of_current_National_Football_League_offensive_coordinators",
    "DEFENSIVE_COORDINATOR": "List_of_current_National_Football_League_defensive_coordinators",
}


def _gen_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"


def _coach_id_for_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"COACH:{slug}"


def _fetch_soup(title: str) -> BeautifulSoup:
    req = urllib.request.Request(f"https://en.wikipedia.org/wiki/{title}", headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=30).read()
    soup = BeautifulSoup(html, "html.parser")
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    return soup


def _parse_role(soup: BeautifulSoup) -> list[dict]:
    out = []
    for t in soup.find_all("table", class_="wikitable"):
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        if "Team" not in headers or "Coordinator" not in headers:
            continue
        for r in t.find_all("tr"):
            cells = r.find_all("td")
            if len(cells) != 4:
                continue  # skips real conference-divider rows (1 cell) -- not a data row
            team_raw = cells[0].get_text(" ", strip=True)
            coach_name = cells[1].get_text(" ", strip=True)
            since_raw = cells[2].get_text(" ", strip=True)
            prev_raw = cells[3].get_text(" ", strip=True)
            if not team_raw or not coach_name:
                continue
            since_match = re.search(r"\d{4}", since_raw)
            out.append({
                "team_name_raw": team_raw, "coach_name": coach_name,
                "since_year": int(since_match.group()) if since_match else None,
                "previous_position_raw": prev_raw,
            })
    return out


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_coordinators (
            coordinator_id TEXT PRIMARY KEY,
            season INTEGER NOT NULL,
            team_name_raw TEXT NOT NULL,
            team_franchise_id TEXT,
            team_code TEXT,
            role TEXT NOT NULL,
            coach_id TEXT NOT NULL,
            coach_name_raw TEXT NOT NULL,
            since_year INTEGER,
            previous_position_raw TEXT,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            UNIQUE(season, team_code, role)
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
            "Pages used: " + ", ".join(SOURCE_PAGES.values()) + f"; retrieved {RETRIEVED_AT}. "
            "Current-season snapshot only -- see module docstring for the disclosed historical-depth gap.",
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

        all_rows = {}
        for role, title in SOURCE_PAGES.items():
            soup = _fetch_soup(title)
            all_rows[role] = _parse_role(soup)

        since_years = [row["since_year"] for rows in all_rows.values() for row in rows if row["since_year"]]
        current_season = Counter(since_years).most_common(1)[0][0] if since_years else None

        report = {
            "current_season": current_season, "role_counts": {}, "team_resolved": 0,
            "total_rows": 0, "new_coach_identities_created": 0,
        }

        for role, rows in all_rows.items():
            report["role_counts"][role] = len(rows)
            for row in rows:
                tid, tcode, _tm = _resolve_team(c, row["team_name_raw"], current_season)
                if tcode:
                    report["team_resolved"] += 1

                coach_id = _coach_id_for_name(row["coach_name"])
                existing = c.execute("SELECT coach_id FROM coaches WHERE coach_id=?", (coach_id,)).fetchone()
                if not existing:
                    c.execute(
                        "INSERT INTO coaches(coach_id, coach_name, source_id, verification_status) VALUES (?,?,?,?)",
                        (coach_id, row["coach_name"], SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY"),
                    )
                    report["new_coach_identities_created"] += 1

                coordinator_id = _gen_id("COORD", str(current_season), row["team_name_raw"], role)
                c.execute(
                    """INSERT INTO nfl_coordinators(
                        coordinator_id, season, team_name_raw, team_franchise_id, team_code, role,
                        coach_id, coach_name_raw, since_year, previous_position_raw,
                        source_id, source_page, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(season, team_code, role) DO NOTHING""",
                    (coordinator_id, current_season, row["team_name_raw"], tid, tcode, role,
                     coach_id, row["coach_name"], row["since_year"], row["previous_position_raw"],
                     SOURCE_ID, f"https://en.wikipedia.org/wiki/{SOURCE_PAGES[role]}", RETRIEVED_AT,
                     "WIKIPEDIA_STRUCTURED_SECONDARY"),
                )
                report["total_rows"] += 1

                if tcode:
                    predicate = "SERVED_AS_" + role
                    c.execute(
                        """INSERT INTO relationships(subject_type, subject_id, predicate,
                           object_type, object_id, season_start, season_end, source_id, verification_status)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                           DO NOTHING""",
                        ("coach", coach_id, predicate, "team", tcode, current_season, current_season,
                         SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY"),
                    )

        c.commit()

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_coordinators", rows_published=report["total_rows"],
            rows_rejected=0, rows_read=report["total_rows"], min_row_count_floor=40,
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
