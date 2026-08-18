"""One-time historical backfill: NFL AP All-Pro selections (Knowledge
Expansion Batch 2), from Wikipedia's real, per-season "YYYY All-Pro Team"
pages. Same production safety pattern as every other tools/data_refresh
module (verified backup, run-tracking, sanity checks, restore-on-failure);
same Wikipedia-as-secondary-source basis as nfl_wikipedia_history_import.py
and nfl_hof_import.py.

--- REAL, CONFIRMED PAGE-FORMAT FRAGMENTATION ACROSS ERAS ---
Direct inspection of a sample across 1932-2025 found THREE real, distinct
Wikipedia table layouts for this exact data, not one:
  * MODERN (season >= 1969): three tables (Offense/Defense/Special teams),
    each row "Position | First team | Second team", each cell holding one
    or more "Player, Team (SEL1, SEL2, ...)" entries separated by <br>.
    Honor level (FIRST_TEAM/SECOND_TEAM) comes from which real column the
    entry is in; selector provenance (AP, PFWA, TSN, ...) comes from the
    parenthetical, never invented.
  * CLASSIC (1932 <= season <= 1962): one flat table "Position | Player |
    Team | Selector(s)", one row per player-position appearance. Honor
    level comes from a real "-1"/"-2" (optionally trailing "t" for a tie)
    suffix on each selector abbreviation, e.g. "AP-1" vs "AP-2" -- the
    tier is per-selector, not per-row, so this module reads the AP-
    specific tag specifically rather than assuming the whole row is one
    tier.
  * TRANSITIONAL (1963-1968): single "Players" column with no reliable
    first/second-team split in the rendered table. NOT ingested this
    batch -- explicitly skipped and reported, never guessed.
A handful of individual years also 404/error outright (format anomalies
Wikipedia itself has not standardized); these are caught per-year and
reported in `skipped_years`, never silently dropped.

--- CANONICAL DISTINCTION: AP FIRST-TEAM, NOT A MERGED "ALL-PRO" ---
Every selection row keeps its FULL raw selector list (never merged across
AP/PFWA/TSN/UPI/NEA/etc.) but only rows where a real AP-specific tag is
present (`is_ap=1`) get the canonical `AP_FIRST_TEAM_ALL_PRO` /
`AP_SECOND_TEAM_ALL_PRO` relationship, per instruction to prefer AP as the
canonical selector while retaining the rest as raw provenance. A row with
selectors but no AP tag (a PFWA-only or TSN-only pick) is real, kept, but
`is_ap=0` and produces no canonical relationship -- disclosed, not forced.
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
from tools.data_refresh.nfl_wikipedia_history_import import (  # noqa: E402
    _resolve_player, _resolve_team,
)

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "NFL"
DATASET = "nfl_all_pro_wikipedia"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
RETRIEVED_AT = "2026-08-18"
USER_AGENT = "ReadsFootballResearch/1.0 (educational trivia project; contact via repo)"

MODERN_YEARS = range(1969, 2026)
CLASSIC_YEARS = range(1932, 1963)
SKIPPED_TRANSITIONAL_YEARS = list(range(1963, 1969))  # real, disclosed gap -- see module docstring

FRAGMENT_RE = re.compile(r"^(?P<name>[^,]+),\s*(?P<team>[^()]+?)\s*(?:\((?P<sel>[^)]*)\))?\s*$")
CLASSIC_SEL_TAG_RE = re.compile(r"\bAP-(1|2)(t)?\b", re.IGNORECASE)


def _gen_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"


def _fetch_soup(title: str) -> BeautifulSoup:
    req = urllib.request.Request(f"https://en.wikipedia.org/wiki/{title}", headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=30).read()
    return BeautifulSoup(html, "html.parser")


def _split_cell_entries(cell) -> list[str]:
    """Splits a table cell on real <br> tags into one raw text fragment
    per player -- never splits on commas, since team names/selector lists
    legitimately contain commas."""
    parts, buf = [], []
    for node in cell.children:
        if getattr(node, "name", None) == "br":
            if buf:
                parts.append("".join(buf).strip())
                buf = []
        else:
            buf.append(node.get_text() if hasattr(node, "get_text") else str(node))
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def _parse_modern_year(soup: BeautifulSoup, season: int) -> list[dict]:
    out = []
    for t in soup.find_all("table", class_="wikitable"):
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        if "First team" not in headers:
            continue
        for r in t.find_all("tr"):
            cells = r.find_all("td")
            if len(cells) != 3:
                continue
            position_raw = cells[0].get_text(" ", strip=True)
            for honor_level, cell in (("FIRST_TEAM", cells[1]), ("SECOND_TEAM", cells[2])):
                for frag in _split_cell_entries(cell):
                    m = FRAGMENT_RE.match(frag)
                    if not m:
                        continue
                    name = m.group("name").strip()
                    team = (m.group("team") or "").strip()
                    sel_raw = (m.group("sel") or "").strip()
                    selectors = [s.strip() for s in sel_raw.split(",") if s.strip()]
                    is_ap = any(s.upper().startswith("AP") for s in selectors)
                    out.append({
                        "season": season, "position_raw": position_raw, "player_name_raw": name,
                        "team_name_raw": team, "honor_level": honor_level, "selectors_raw": sel_raw,
                        "is_ap": is_ap, "page_format": "MODERN_FIRST_SECOND_COLUMNS",
                    })
    return out


def _parse_classic_year(soup: BeautifulSoup, season: int) -> list[dict]:
    out = []
    tables = soup.find_all("table", class_="wikitable")
    if not tables:
        return out
    t = tables[0]
    for r in t.find_all("tr")[1:]:
        cells = r.find_all("td")
        if len(cells) != 4:
            continue
        position_raw, player_raw, team_raw, sel_raw = (c.get_text(" ", strip=True) for c in cells)
        if not player_raw:
            continue
        m = CLASSIC_SEL_TAG_RE.search(sel_raw)
        if m:
            honor_level = "FIRST_TEAM" if m.group(1) == "1" else "SECOND_TEAM"
            is_ap = True
        else:
            honor_level, is_ap = "UNKNOWN_NO_AP_TAG", False
        out.append({
            "season": season, "position_raw": position_raw, "player_name_raw": player_raw,
            "team_name_raw": team_raw, "honor_level": honor_level, "selectors_raw": sel_raw,
            "is_ap": is_ap, "page_format": "CLASSIC_SELECTOR_SUFFIX",
        })
    return out


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_all_pro_selections (
            selection_id TEXT PRIMARY KEY,
            season INTEGER NOT NULL,
            position_raw TEXT NOT NULL,
            player_name_raw TEXT NOT NULL,
            player_id TEXT,
            resolution_method TEXT NOT NULL,
            team_name_raw TEXT,
            team_franchise_id TEXT,
            team_code TEXT,
            honor_level TEXT NOT NULL,
            selectors_raw TEXT,
            is_ap INTEGER NOT NULL,
            page_format TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            UNIQUE(season, position_raw, player_name_raw, honor_level, team_name_raw)
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
            f"Pages used: https://en.wikipedia.org/wiki/YYYY_All-Pro_Team for each real season "
            f"1932-1962 and 1969-2025; retrieved {RETRIEVED_AT}.",
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
            "years_attempted": 0, "years_succeeded": 0, "skipped_years": {},
            "total_rows": 0, "ap_rows": 0, "player_identity_resolved": 0,
            "season_range_ingested": [None, None],
        }
        seasons_ok = []

        for season in list(MODERN_YEARS) + list(CLASSIC_YEARS):
            report["years_attempted"] += 1
            title = f"{season}_All-Pro_Team"
            try:
                soup = _fetch_soup(title)
            except Exception as exc:
                report["skipped_years"][str(season)] = f"FETCH_FAILED: {exc!r}"
                continue

            entries = _parse_modern_year(soup, season) if season in MODERN_YEARS else _parse_classic_year(soup, season)
            if not entries:
                report["skipped_years"][str(season)] = "NO_RECOGNIZED_TABLE_FORMAT"
                continue

            seasons_ok.append(season)
            report["years_succeeded"] += 1
            for e in entries:
                pid, method = _resolve_player(c, e["player_name_raw"], e["position_raw"].lower())
                tid, tcode, _tm = _resolve_team(c, e["team_name_raw"], season) if e["team_name_raw"] else (None, None, None)

                sel_id = _gen_id("ALLPRO", str(season), e["position_raw"], e["player_name_raw"], e["honor_level"], e["team_name_raw"] or "")
                c.execute(
                    """INSERT INTO nfl_all_pro_selections(
                        selection_id, season, position_raw, player_name_raw, player_id, resolution_method,
                        team_name_raw, team_franchise_id, team_code, honor_level, selectors_raw, is_ap,
                        page_format, source_id, source_page, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(season, position_raw, player_name_raw, honor_level, team_name_raw) DO NOTHING""",
                    (sel_id, season, e["position_raw"], e["player_name_raw"], pid, method,
                     e["team_name_raw"], tid, tcode, e["honor_level"], e["selectors_raw"], int(e["is_ap"]),
                     e["page_format"], SOURCE_ID, f"https://en.wikipedia.org/wiki/{title}", RETRIEVED_AT,
                     "WIKIPEDIA_STRUCTURED_SECONDARY"),
                )
                report["total_rows"] += 1
                if e["is_ap"]:
                    report["ap_rows"] += 1
                    if pid:
                        report["player_identity_resolved"] += 1
                        predicate = "AP_FIRST_TEAM_ALL_PRO" if e["honor_level"] == "FIRST_TEAM" else "AP_SECOND_TEAM_ALL_PRO"
                        c.execute(
                            """INSERT INTO relationships(subject_type, subject_id, predicate,
                               object_type, object_id, season_start, season_end, source_id, verification_status)
                               VALUES (?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                               DO NOTHING""",
                            ("nfl_player", pid, predicate, "nfl_all_pro_selection", sel_id,
                             season, season, SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY"),
                        )
            time.sleep(0.15)

        c.commit()
        if seasons_ok:
            report["season_range_ingested"] = [min(seasons_ok), max(seasons_ok)]
        report["skipped_transitional_years_1963_1968"] = SKIPPED_TRANSITIONAL_YEARS

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_all_pro_selections", rows_published=report["total_rows"],
            rows_rejected=0, rows_read=report["total_rows"], min_row_count_floor=1000,
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
