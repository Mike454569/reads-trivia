"""One-time historical backfill: NFL Pro Bowl selections (Knowledge
Expansion Batch 2), from Wikipedia's real, per-season "YYYY Pro Bowl"
roster tables. Same production safety pattern as every other
tools/data_refresh module; same Wikipedia-as-secondary-source basis as
nfl_wikipedia_history_import.py / nfl_hof_import.py / nfl_all_pro_import.py.

--- REAL, DISCLOSED SCOPE: 1972-2025, NOT THE FULL 1951+ HISTORY ---
Direct inspection found the Pro Bowl roster tables are far more
inconsistently formatted year-to-year than the All-Pro pages: 1951-1971
mix at least three incompatible table shapes (a nested American/National
Conference header, a nested-th layout, nothing recognizable at all in
several years), and several individual years even in the 1970s-1990s
render as zero real `wikitable`-classed tables outright. Only years from
1972 onward, using the "Position | Starter(s) | Reserve(s) [|
Alternate(s)]" or "Position | AFC | NFC" shapes, are ingested here; every
other year (including all of 1951-1971) is skipped and reported, never
guessed. `earliest_reliable_season` in the run report reflects the real,
achieved floor, not the league's full history.

--- TWO REAL SELECTION TIERS, NEVER COLLAPSED ---
* STARTER / RESERVE / ALTERNATE, when the source table distinguishes them
  (the modern, most-common shape).
* SELECTED (undifferentiated), for years (1976-1977 confirmed) whose
  table only splits by conference (AFC/NFC), not by starter/reserve --
  a real, different granularity, never upgraded to a fake STARTER guess.
Alternates are recorded as real alternates (not promoted to RESERVE even
if a source note says they later played), matching the "no replacement-
vs-original invention" instruction.
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
from tools.data_refresh.nfl_all_pro_import import _split_cell_entries  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "NFL"
DATASET = "nfl_pro_bowl_wikipedia"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
RETRIEVED_AT = "2026-08-18"
USER_AGENT = "ReadsFootballResearch/1.0 (educational trivia project; contact via repo)"

YEARS = range(1972, 2026)

# Two real, distinct name/team separators seen across eras: an ordinary
# comma (modern format) and an en-dash "Player – Team" (1976-1977 format).
# ASCII hyphens are deliberately excluded from the separator class -- real
# player names (e.g. "Amon-Ra St. Brown") legitimately contain one.
PB_FRAGMENT_RE = re.compile(r"^(?:\d+\s+)?(?P<name>[^,–—\[]+?)\s*[,–—]\s*(?P<team>[^,\[]+)")


def _gen_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"


def _fetch_soup(title: str) -> BeautifulSoup:
    req = urllib.request.Request(f"https://en.wikipedia.org/wiki/{title}", headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=30).read()
    soup = BeautifulSoup(html, "html.parser")
    # Real bug found this batch: some citation-footnote spans embed a
    # <style> tag whose raw CSS text leaks into get_text() (e.g. a team
    # name silently growing "Kansas City.mw-parser-output .citation{...").
    # Stripped here, once, rather than patched with fragile per-field regex.
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    return soup


def _column_tier_map(headers: list[str]) -> dict[int, str] | None:
    """Maps each data-column index (0-based, position column excluded) to
    a real selection tier, from whatever header text this specific table
    actually uses -- never assumes a fixed column count."""
    tiers = {}
    for i, h in enumerate(headers[1:]):
        hl = h.lower()
        if "starter" in hl:
            tiers[i] = "STARTER"
        elif "reserve" in hl:
            tiers[i] = "RESERVE"
        elif "alternate" in hl:
            tiers[i] = "ALTERNATE"
        elif hl.strip() in ("afc", "nfc"):
            tiers[i] = "SELECTED"
        else:
            return None  # unrecognized column -- do not guess a tier
    return tiers or None


def _parse_year(soup: BeautifulSoup, season: int) -> list[dict]:
    out = []
    for t in soup.find_all("table", class_="wikitable"):
        header_cells = t.find("tr")
        if not header_cells:
            continue
        headers = [c.get_text(" ", strip=True) for c in header_cells.find_all(["th", "td"])]
        if not headers or "position" not in headers[0].lower():
            continue
        tiers = _column_tier_map(headers)
        if tiers is None:
            continue
        for r in t.find_all("tr")[1:]:
            cells = r.find_all("td")
            if len(cells) != len(headers):
                continue
            position_raw = cells[0].get_text(" ", strip=True)
            if not position_raw:
                continue
            for col_idx, tier in tiers.items():
                cell = cells[col_idx + 1]
                for frag in _split_cell_entries(cell):
                    m = PB_FRAGMENT_RE.match(frag)
                    if not m:
                        continue
                    name = m.group("name").strip()
                    team = m.group("team").strip()
                    if not name or not team:
                        continue
                    out.append({
                        "season": season, "position_raw": position_raw, "player_name_raw": name,
                        "team_name_raw": team, "tier": tier,
                    })
    return out


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS nfl_pro_bowl_selections (
            selection_id TEXT PRIMARY KEY,
            season INTEGER NOT NULL,
            position_raw TEXT NOT NULL,
            player_name_raw TEXT NOT NULL,
            player_id TEXT,
            resolution_method TEXT NOT NULL,
            team_name_raw TEXT,
            team_franchise_id TEXT,
            team_code TEXT,
            tier TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_page TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            UNIQUE(season, position_raw, player_name_raw, tier, team_name_raw)
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
            f"Pages used: https://en.wikipedia.org/wiki/YYYY_Pro_Bowl for real seasons 1972-2025 "
            f"(gaps disclosed per-year); retrieved {RETRIEVED_AT}.",
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
            "total_rows": 0, "player_identity_resolved": 0, "season_range_ingested": [None, None],
            "tier_counts": {},
        }
        seasons_ok = []

        for season in YEARS:
            report["years_attempted"] += 1
            title = f"{season}_Pro_Bowl"
            try:
                soup = _fetch_soup(title)
            except Exception as exc:
                report["skipped_years"][str(season)] = f"FETCH_FAILED: {exc!r}"
                continue

            entries = _parse_year(soup, season)
            if not entries:
                report["skipped_years"][str(season)] = "NO_RECOGNIZED_TABLE_FORMAT"
                continue

            seasons_ok.append(season)
            report["years_succeeded"] += 1
            for e in entries:
                pid, method = _resolve_player(c, e["player_name_raw"], e["position_raw"].lower())
                tid, tcode, _tm = _resolve_team(c, e["team_name_raw"], season) if e["team_name_raw"] else (None, None, None)

                sel_id = _gen_id("PROBOWL", str(season), e["position_raw"], e["player_name_raw"], e["tier"], e["team_name_raw"])
                c.execute(
                    """INSERT INTO nfl_pro_bowl_selections(
                        selection_id, season, position_raw, player_name_raw, player_id, resolution_method,
                        team_name_raw, team_franchise_id, team_code, tier,
                        source_id, source_page, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(season, position_raw, player_name_raw, tier, team_name_raw) DO NOTHING""",
                    (sel_id, season, e["position_raw"], e["player_name_raw"], pid, method,
                     e["team_name_raw"], tid, tcode, e["tier"],
                     SOURCE_ID, f"https://en.wikipedia.org/wiki/{title}", RETRIEVED_AT,
                     "WIKIPEDIA_STRUCTURED_SECONDARY"),
                )
                report["total_rows"] += 1
                report["tier_counts"][e["tier"]] = report["tier_counts"].get(e["tier"], 0) + 1
                if pid:
                    report["player_identity_resolved"] += 1
                    c.execute(
                        """INSERT INTO relationships(subject_type, subject_id, predicate,
                           object_type, object_id, season_start, season_end, source_id, verification_status)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end)
                           DO NOTHING""",
                        ("nfl_player", pid, "PRO_BOWL_SELECTION", "nfl_pro_bowl_selection", sel_id,
                         season, season, SOURCE_ID, "WIKIPEDIA_STRUCTURED_SECONDARY"),
                    )
            time.sleep(0.15)

        c.commit()
        if seasons_ok:
            report["season_range_ingested"] = [min(seasons_ok), max(seasons_ok)]

        safety.run_post_refresh_sanity_checks(
            c, table="nfl_pro_bowl_selections", rows_published=report["total_rows"],
            rows_rejected=0, rows_read=report["total_rows"], min_row_count_floor=500,
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
