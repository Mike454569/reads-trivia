"""CFB All-America selections -- Engine-gap-audit operation.

Real source: Wikipedia's annual "{season} All-America college football team"
pages, 1889-present -- already `approved_for_import=1` in `sources` as
WIKIPEDIA_STRUCTURED (the same source the earlier NFL Wikipedia history
import used for Super Bowl/award history). Fetched via the real MediaWiki
API (`action=parse&prop=text`), parsed against the RENDERED HTML with
BeautifulSoup -- not raw wikitext regex -- matching that same prior import's
own documented reasoning: HTML parsing avoids transcription risk on
fact-dense tables that raw wikitext regex would be much more fragile against.

Real, disclosed format drift found before building (confirmed directly by
fetching and comparing 2025, 2000, 1995, 1990, 1985, 1980, 1975, 1950, 1920,
and 1889): this is NOT one consistent format across 137 years. Two real,
common formats cover the large majority of years and are what this importer
parses:
  1. LIST format (e.g. 2025, 2000, 1995, 1980): `<h2>`/`<h3>` position
     headings followed by `<ul><li>` entries -- bold (`<b>`) player name
     indicates Wikipedia's own "consensus" convention, text after the name
     up to `(` is the school, parenthesized text is the raw selector list.
  2. TABLE format (e.g. 1990, 1985, 1975): a `<table class="wikitable">`
     with a header row naming Name/Position/School columns (order and exact
     column set vary by year -- detected from the header row itself, never
     assumed fixed).
A third, much older format (1889 and its immediate neighbors: a definition
list keyed by position, one selector, no selector-count/consensus concept
at all) matches NEITHER pattern and is honestly left unparsed by this
importer -- a real, disclosed gap for a small number of the earliest years,
not a silent omission (this run's own report lists every season that failed
to parse under either format).

What is NOT attempted: decoding selector abbreviations (`AP-1`, `WC`,
`UPI`, `TSN`, etc.) into normalized per-selector-body facts. These
abbreviations drift in meaning and set across a century of different media
organizations; reliably mapping them all is a real, separate research
project this pass does not attempt. `selectors_raw` keeps the source's own
text verbatim instead of fabricating a false normalization.

No canonical player-ID resolution is attempted either -- most of this
population predates every player-identity source already in this Engine
(draft_facts starts 1980, cfb_roster_seasons_real starts 2002). `player_name`
is kept as real, verbatim source text; a school is resolved via
`import_data.resolve_school()` (the same real fuzzy-normalized match every
other CFB importer in this codebase already uses) wherever the source's
school text matches a real, known school.

No natural composite key survives 137 years of real editorial inconsistency
(a same-named player could legitimately appear at two positions in
different years, formatting varies row to row) -- this table uses a
surrogate autoincrement id and full delete-and-republish per run for this
source's scope, the same lesson already learned building
`nfl_contracts_refresh.py`.
"""
from __future__ import annotations

import datetime as _dt
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import import_data  # noqa: E402

from bs4 import BeautifulSoup  # noqa: E402

LEAGUE = "CFB"
DATASET = "cfb_all_america"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
API_URL = "https://en.wikipedia.org/w/api.php"
MIN_SEASON = 1889
MAX_SEASON_ATTEMPT = _dt.datetime.now(_dt.timezone.utc).year


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS cfb_all_america (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            school_id INTEGER,
            school_name_raw TEXT,
            position TEXT,
            is_consensus INTEGER,
            selectors_raw TEXT,
            parse_format TEXT NOT NULL,
            source_page TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(source_id)
        )
    """)
    c.commit()


def _fetch_html(season: int) -> str | None:
    page = f"{season}_All-America_college_football_team"
    url = f"{API_URL}?action=parse&page={page}&prop=text&format=json&redirects=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Reads-Football-Data-Refresh/1.0"})
    last_err = None
    # A real 137-request full sweep (1889-present) hit Wikipedia's rate limit
    # under the original 0.3s inter-request pace (confirmed live: HTTP 429
    # partway through). A 429 specifically gets a real, longer backoff (10s)
    # before retrying -- distinct from a generic transient network error
    # (1.5s) -- since retrying a rate limit at the same pace that triggered
    # it doesn't fix anything.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                import json
                data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                return None  # page doesn't exist for this season -- not a transient failure
            return data["parse"]["text"]["*"]
        except urllib.error.HTTPError as e:
            last_err = e
            time.sleep(10.0 if e.code == 429 else 1.5)
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    if last_err:
        raise last_err
    return None


# Sections that appear after the real per-position selections on these
# pages and must never be scanned for player rows (reference lists,
# navboxes, external links, "substitutes"/"see also" content -- real text,
# but not a first-team All-America selection).
_STOP_HEADINGS = {
    "references", "external links", "see also", "notes", "citations",
    "further reading", "bibliography", "substitutes",
}


def _parse_list_format(soup: BeautifulSoup) -> list[dict]:
    # The MediaWiki `action=parse&prop=text` response wraps real article
    # content in `class="mw-parser-output"` -- NOT `id="mw-content-text"`
    # (that id only exists on a full page view, not this API's fragment).
    # Confirmed directly: scoping to the wrong selector silently fell back
    # to scanning the ENTIRE returned HTML, including navboxes and a
    # 137-item year-navigation list -- a real bug caught by inspecting
    # 1889's actual output before trusting it.
    content = soup.find(class_="mw-parser-output") or soup
    out: list[dict] = []
    current_position = None
    for el in content.find_all(["h2", "h3", "h4", "dt", "ul"], recursive=True):
        if el.name in ("h2", "h3", "h4"):
            text = el.get_text(strip=True)
            if text.lower() in _STOP_HEADINGS:
                break  # nothing past this point is a real per-player selection
            if text.lower() in ("offense", "defense", "special teams"):
                continue
            current_position = text
            continue
        if el.name == "dt":
            # Older-era pages (e.g. 1889) use a definition list (`;Position`
            # in wikitext) instead of an h3 for each position -- tracked the
            # same way as a heading.
            current_position = el.get_text(strip=True)
            continue
        if el.name == "ul" and current_position:
            for li in el.find_all("li", recursive=False):
                first_link = li.find("a")
                if not first_link:
                    continue
                # is_consensus / player_name must come from the SPECIFIC link
                # to the player, never "the first <b> anywhere in this <li>"
                # -- confirmed directly against real 2025 markup that a
                # selector abbreviation inside the parenthesized list (e.g.
                # `<b>TSN</b>`) can be bolded even when the player itself is
                # NOT a consensus pick, which previously produced a fabricated
                # "player" literally named after the selector abbreviation.
                player_name = first_link.get_text(" ", strip=True)
                is_consensus = 1 if first_link.find_parent("b") else 0
                full_text = li.get_text(" ", strip=True)
                paren_idx = full_text.find("(")
                before_paren = full_text[:paren_idx] if paren_idx != -1 else full_text
                selectors_raw = full_text[paren_idx:].strip() if paren_idx != -1 else None
                # school is the text between the player name and the parenthesis, after a comma
                comma_idx = before_paren.find(",")
                school_raw = before_paren[comma_idx + 1:].strip().rstrip(",").strip() if comma_idx != -1 else None
                if not school_raw:
                    continue
                out.append({
                    "player_name": player_name, "school_name_raw": school_raw,
                    "position": current_position, "is_consensus": is_consensus,
                    "selectors_raw": selectors_raw, "parse_format": "LIST",
                })
    return out


def _parse_table_format(soup: BeautifulSoup) -> list[dict]:
    content = soup.find(class_="mw-parser-output") or soup
    out: list[dict] = []
    for table in content.find_all("table", class_="wikitable"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = [c.get_text(" ", strip=True).lower() for c in rows[0].find_all(["th", "td"])]
        if not any("name" in h for h in header_cells) or not any("school" in h for h in header_cells):
            continue  # not the data table (could be an infobox or unrelated wikitable)
        name_idx = next((i for i, h in enumerate(header_cells) if "name" in h), None)
        pos_idx = next((i for i, h in enumerate(header_cells) if "position" in h), None)
        school_idx = next((i for i, h in enumerate(header_cells) if "school" in h), None)
        if name_idx is None or school_idx is None:
            continue
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) <= max(name_idx, school_idx):
                continue
            player_name = cells[name_idx].get_text(" ", strip=True)
            school_raw = cells[school_idx].get_text(" ", strip=True)
            position = cells[pos_idx].get_text(" ", strip=True) if pos_idx is not None and pos_idx < len(cells) else None
            if not player_name or not school_raw:
                continue
            selector_cells = [c.get_text(" ", strip=True) for i, c in enumerate(cells)
                               if i not in (name_idx, pos_idx, school_idx) and c.get_text(strip=True)]
            out.append({
                "player_name": player_name, "school_name_raw": school_raw, "position": position,
                "is_consensus": None,  # no reliable bold/consensus signal in table format -- never guessed
                "selectors_raw": " | ".join(selector_cells) if selector_cells else None,
                "parse_format": "TABLE",
            })
        if out:
            break  # first real data table found -- later tables on the page are navboxes/sidebars
    return out


def _parse_season(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = _parse_table_format(soup)
    if rows:
        return rows
    return _parse_list_format(soup)


def run_cfb_all_america_import(seasons: list[int] | None = None) -> dict:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    _ensure_schema(c)
    baseline_count = c.execute("SELECT COUNT(*) FROM cfb_all_america").fetchone()[0]
    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    c.close()

    backup = safety.create_verified_backup()

    target_seasons = seasons if seasons is not None else list(range(MIN_SEASON, MAX_SEASON_ATTEMPT + 1))
    total_published = 0
    seasons_parsed: list[int] = []
    seasons_unparseable: list[int] = []
    seasons_missing_page: list[int] = []
    seasons_fetch_failed: list[int] = []

    try:
        c = engine_bootstrap.connect()
        c.execute("PRAGMA foreign_keys=ON")
        # Scoped to exactly the seasons about to be re-fetched when a
        # specific `seasons` list is passed (a targeted backfill run) --
        # never wipes already-successfully-imported seasons outside that
        # list. A full run (seasons=None) still clears this source's whole
        # scope first, same as before.
        if seasons is not None:
            c.executemany(
                "DELETE FROM cfb_all_america WHERE source_id=? AND season=?",
                [(SOURCE_ID, s) for s in target_seasons],
            )
        else:
            c.execute("DELETE FROM cfb_all_america WHERE source_id=?", (SOURCE_ID,))
        for season in target_seasons:
            # A single season hitting a persistent rate-limit/network failure
            # must not abort the other 136+ real, otherwise-successful years
            # -- confirmed necessary live (a mid-sweep HTTP 429 previously
            # took down the entire run). Recorded honestly as its own
            # category, distinct from `seasons_missing_page` (no real page
            # exists for that year at all).
            try:
                html = _fetch_html(season)
            except Exception:
                seasons_fetch_failed.append(season)
                time.sleep(2.0)
                continue
            # 0.3s was measured live to still trip Wikipedia's rate limit
            # partway through a real 137-request full sweep (HTTP 429) --
            # 1.5s is the corrected, real-tested pace.
            time.sleep(1.5)
            if html is None:
                seasons_missing_page.append(season)
                continue
            rows = _parse_season(html)
            if not rows:
                seasons_unparseable.append(season)
                continue
            for row in rows:
                school_id = import_data.resolve_school(c, row["school_name_raw"])
                c.execute(
                    "INSERT INTO cfb_all_america(season, player_name, school_id, school_name_raw, position, "
                    "is_consensus, selectors_raw, parse_format, source_page, verification_status, source_id) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (season, row["player_name"], school_id, row["school_name_raw"], row["position"],
                     row["is_consensus"], row["selectors_raw"], row["parse_format"],
                     f"{season}_All-America_college_football_team", "WIKIPEDIA_STRUCTURED_SECONDARY", SOURCE_ID),
                )
                total_published += 1
            seasons_parsed.append(season)
        c.commit()

        try:
            safety.run_post_refresh_sanity_checks(
                c, table="cfb_all_america", rows_published=total_published, rows_rejected=0,
                rows_read=total_published, min_row_count_floor=baseline_count,
            )
        except safety.SanityCheckFailure as e:
            c.close()
            restore_info = safety.restore_from_backup(backup["path"])
            c = engine_bootstrap.connect()
            safety.finish_run(
                c, run_id, status="FAILED_RESTORED", backup_id=backup["backup_id"],
                rows_imported=total_published, failure_reason=str(e), detail={"restore": restore_info},
            )
            c.close()
            return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": str(e), "backup": backup}

        safety.finish_run(
            c, run_id, status="SUCCESS", backup_id=backup["backup_id"], rows_imported=total_published,
            no_op=(total_published == 0),
            detail={"seasons_parsed": seasons_parsed, "seasons_unparseable": seasons_unparseable,
                    "seasons_missing_page": seasons_missing_page, "seasons_fetch_failed": seasons_fetch_failed},
        )
        c.close()
        return {
            "status": "SUCCESS", "run_id": run_id, "rows_imported": total_published,
            "seasons_parsed_count": len(seasons_parsed), "seasons_unparseable": seasons_unparseable,
            "seasons_missing_page": seasons_missing_page, "seasons_fetch_failed": seasons_fetch_failed,
            "backup_id": backup["backup_id"],
        }
    except Exception as e:
        # Real bug found live: restoring the backup file (an atomic
        # os.replace over the live DB) while THIS script's own `c` connection
        # was still open on the pre-restore file caused a real, observed
        # cascading "database is locked" on the very next connection --
        # closing it first is required, not optional.
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


def last_run_status() -> dict | None:
    c = engine_bootstrap.connect()
    safety.ensure_refresh_tables(c)
    row = c.execute(
        "SELECT * FROM refresh_runs WHERE league=? AND dataset_name=? ORDER BY started_at DESC LIMIT 1",
        (LEAGUE, DATASET),
    ).fetchone()
    c.close()
    return dict(row) if row else None
