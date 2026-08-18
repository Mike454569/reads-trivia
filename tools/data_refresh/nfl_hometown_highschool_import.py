"""One-time backfill: real NFL player birthplace + high school
background, for a disclosed sample (Knowledge Expansion Batch 2), sourced
from each player's own Wikipedia infobox ("Born" / "High school" fields).

--- REAL, DISCLOSED SCOPE: THE RESOLVED HOF-PLAYER SET, NOT ALL NFL PLAYERS ---
There is no consolidated Wikipedia source for player hometown/high-school
data across the ~17,000-row `canonical_players` population -- this is
inherently a per-player-infobox fact, so ingesting it at scale requires
one fetch per player. This module scopes to the 107 real, identity-
resolved `nfl_hof_inductees` players from this batch's HOF import (a
real, notable, already-canonical-identity-linked cohort), not a claim of
league-wide coverage.

--- BIRTHPLACE vs HOMETOWN: A DISCLOSED, NOT SILENT, EQUIVALENCE ---
Wikipedia's infobox provides exactly one location field for a player's
origin -- "Born" (a real birthplace: city/state/country) -- and does NOT
carry a separately-verified "hometown" concept. Per instruction, hometown
is never silently inferred from birthplace; here it is explicitly NOT
invented as a distinct fact. `nfl_player_background.birthplace_city/state`
holds exactly what the source says. There is no `hometown_city` column --
callers needing "hometown" should read `birthplace_*` and treat it as
exactly that, which is disclosed here and in the query-fact module,
rather than silently duplicating the same value under a second name.

--- HIGH SCHOOL KEPT SEPARATE FROM BIRTHPLACE ---
`high_school_name` / `high_school_city` / `high_school_state` come from
the infobox's own distinct "High school" field (e.g. "Westlake (Austin,
Texas)") -- real cases exist in this run where the high school city
differs from the birth city (player born elsewhere, moved before high
school), which is exactly why the two are never merged.
"""
from __future__ import annotations

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
LEAGUE = "NFL"
DATASET = "nfl_hometown_highschool_wikipedia"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
RETRIEVED_AT = "2026-08-18"
USER_AGENT = "ReadsFootballResearch/1.0 (educational trivia project; contact via repo)"

BORN_LOC_RE_AGE = re.compile(r"\(age\s*\d+\)\s*(?P<loc>.+)$")
BORN_LOC_RE_FALLBACK = re.compile(r"\d{4}\)\s*(?P<loc>.+?)(?:\s+Died\b.*)?$")
HS_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<loc>[^)]+)\)\s*$")


def _fetch_soup(title: str) -> BeautifulSoup:
    req = urllib.request.Request(f"https://en.wikipedia.org/wiki/{title}", headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=30).read()
    soup = BeautifulSoup(html, "html.parser")
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    return soup


def _wiki_title_for_player(display_name: str) -> str:
    return display_name.strip().replace(" ", "_")


def _parse_location(text: str) -> tuple[str | None, str | None, str | None]:
    """Splits a real 'City, State, Country' (or 'City, State' / 'City')
    string into (city, state, country) -- never guesses a missing part."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 3:
        return parts[0], parts[1], parts[-1]
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 1:
        return parts[0], None, None
    return None, None, None


def _extract_infobox_fields(soup: BeautifulSoup) -> dict:
    infobox = soup.find("table", class_="infobox")
    if not infobox:
        return {}
    fields = {}
    for r in infobox.find_all("tr"):
        th, td = r.find("th"), r.find("td")
        if th and td:
            fields[th.get_text(" ", strip=True)] = td.get_text(" ", strip=True)
    return fields


def _parse_player_page(soup: BeautifulSoup) -> dict:
    fields = _extract_infobox_fields(soup)
    out = {
        "birthplace_raw": None, "birthplace_city": None, "birthplace_state": None, "birthplace_country": None,
        "high_school_raw": None, "high_school_name": None, "high_school_city": None, "high_school_state": None,
    }
    born = fields.get("Born")
    if born:
        m = BORN_LOC_RE_AGE.search(born) or BORN_LOC_RE_FALLBACK.search(born)
        if m:
            loc = m.group("loc").strip()
            out["birthplace_raw"] = loc
            out["birthplace_city"], out["birthplace_state"], out["birthplace_country"] = _parse_location(loc)

    hs = fields.get("High school")
    if hs:
        out["high_school_raw"] = hs
        m = HS_RE.match(hs)
        if m:
            out["high_school_name"] = m.group("name").strip()
            city, state, _country = _parse_location(m.group("loc"))
            out["high_school_city"], out["high_school_state"] = city, state
        else:
            out["high_school_name"] = hs.strip()
    return out


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_player_background (
            player_id TEXT PRIMARY KEY,
            display_name_raw TEXT NOT NULL,
            birthplace_raw TEXT,
            birthplace_city TEXT,
            birthplace_state TEXT,
            birthplace_country TEXT,
            high_school_raw TEXT,
            high_school_name TEXT,
            high_school_city TEXT,
            high_school_state TEXT,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL
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
            f"Per-player infobox fetch for the 107 identity-resolved nfl_hof_inductees players "
            f"(disclosed sample, not league-wide); retrieved {RETRIEVED_AT}.",
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

        players = c.execute(
            "SELECT DISTINCT h.player_id, h.inductee_name_raw FROM nfl_hof_inductees h WHERE h.player_id IS NOT NULL"
        ).fetchall()

        report = {
            "players_attempted": len(players), "players_succeeded": 0, "fetch_failed": {},
            "birthplace_resolved": 0, "high_school_resolved": 0, "both_resolved": 0,
        }

        for row in players:
            title = _wiki_title_for_player(row["inductee_name_raw"])
            try:
                soup = _fetch_soup(title)
            except Exception as exc:
                report["fetch_failed"][row["inductee_name_raw"]] = repr(exc)
                continue

            data = _parse_player_page(soup)
            has_birthplace = data["birthplace_city"] is not None
            has_hs = data["high_school_name"] is not None
            if has_birthplace or has_hs:
                report["players_succeeded"] += 1
            if has_birthplace:
                report["birthplace_resolved"] += 1
            if has_hs:
                report["high_school_resolved"] += 1
            if has_birthplace and has_hs:
                report["both_resolved"] += 1

            c.execute(
                """INSERT INTO nfl_player_background(
                    player_id, display_name_raw, birthplace_raw, birthplace_city, birthplace_state,
                    birthplace_country, high_school_raw, high_school_name, high_school_city, high_school_state,
                    source_id, source_page, retrieved_at, verification_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(player_id) DO UPDATE SET
                     birthplace_raw=excluded.birthplace_raw, birthplace_city=excluded.birthplace_city,
                     birthplace_state=excluded.birthplace_state, birthplace_country=excluded.birthplace_country,
                     high_school_raw=excluded.high_school_raw, high_school_name=excluded.high_school_name,
                     high_school_city=excluded.high_school_city, high_school_state=excluded.high_school_state""",
                (row["player_id"], row["inductee_name_raw"], data["birthplace_raw"], data["birthplace_city"],
                 data["birthplace_state"], data["birthplace_country"], data["high_school_raw"],
                 data["high_school_name"], data["high_school_city"], data["high_school_state"],
                 SOURCE_ID, f"https://en.wikipedia.org/wiki/{title}", RETRIEVED_AT,
                 "WIKIPEDIA_STRUCTURED_SECONDARY"),
            )
            time.sleep(0.15)

        c.commit()

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_player_background", rows_published=report["players_succeeded"],
            rows_rejected=0, rows_read=len(players), min_row_count_floor=50,
        )

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
            rows_downloaded=len(players), rows_imported=report["players_succeeded"],
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
