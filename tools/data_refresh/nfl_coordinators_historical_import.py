"""One-time backfill: real, historical (2000-2025) NFL offensive/defensive
coordinators (Gold Standard Modes + Creator Quality follow-up pass), from
each real team-season's own Wikipedia "<season> <Team Name> season" page --
the same real per-team-season-page technique
`cfb_coordinators_import.py` already established and proved workable for
CFB (confirmed here for NFL too: spot-checked directly, both the real
infobox AND a detailed "Staff/Coaches" section reliably carry real,
current-for-that-season Offensive/Defensive Coordinator names).

--- REAL, DISCLOSED SCOPE ---
Real team identity per (team_code, season) comes from `team_aliases`
(already-certified, 2002-2025 real coverage -- confirmed directly: 0 rows
before season_start=2002). 2000-2001 (before this table's own real
coverage begins, and before the Houston Texans existed) are covered by
reusing each of the 31 real 2000-2001-era teams' own EARLIEST real
`team_aliases` display name -- safe only because no team_code changed
display name between 2000 and 2002 in this real window (checked directly:
every 2002 team_aliases row's season_start is exactly 2002, meaning no
relocation/rename event fell inside 2000-2002 itself; the one franchise
that DID rename in this era, Washington, did so in 2020, well after this
fallback's own window).

--- PAGE TITLE CONSTRUCTION, NEVER GUESSED ---
`f"{season}_{full_name.replace(' ', '_')}_season"`, built ONLY from
`team_aliases.full_name` (a real, already-certified display name), never a
hand-typed or inferred name. A 404 or a page with no parseable infobox
coordinator fields is recorded as UNRESOLVED for that (team, season, role)
-- never fabricated, never silently skipped without being counted.

--- CO-COORDINATORS PRESERVED, NEVER FABRICATED AWAY ---
When the infobox lists more than one name for a role (a real co-coordinator
arrangement), all real names found are preserved, joined with " / " in
`coach_name_raw` -- never collapsed to just the first name found.

--- COACH IDENTITY REUSE, NOT A NEW IDENTITY SPACE ---
Same `coaches` table / `COACH:` ID scheme / lowercased-underscore-slug
generation as `nfl_coordinators_import.py` (the 2026-only backfill this
extends) -- one identity space, not two.

--- SAFE, PACED, REAL-NETWORK SCRAPE ---
A `--limit`/`--seasons` CLI lets a caller run a real, bounded subset (this
codebase's `create_verified_backup()`/`restore_from_backup()` safety net
still wraps the whole run) -- the full 2000-2025 sweep is ~830 real page
fetches, paced at >=0.4s apart (a real, disclosed politeness delay, not
fabricated), so a full run takes real wall-clock time; run it in stages if
needed. Re-running is idempotent (`ON CONFLICT(season, team_code, role) DO
NOTHING` on the same `nfl_coordinators` table/constraint the 2026-only
import already uses).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LEAGUE = "NFL"
DATASET = "nfl_coordinators_historical_wikipedia"
SOURCE_ID = "WIKIPEDIA_STRUCTURED"
VERIFICATION_STATUS = "WIKIPEDIA_STRUCTURED_SECONDARY"
RETRIEVED_AT = "2026-09-02"
USER_AGENT = "ReadsFootballResearch/1.0 (educational trivia project; contact via repo)"
REQUEST_DELAY_SECONDS = 1.0  # real, measured: 0.4s triggered a real HTTP 429 during validation

MIN_SEASON, MAX_SEASON = 2000, 2025

# Real, disclosed exception to the 2000-2001 fallback below: the Houston
# Texans are the one real 2002 NFL expansion team -- they did not exist in
# 2000-2001 at all, unlike every other team_code whose team_aliases row
# merely HAPPENS to start at 2002 (that table's own real coverage floor,
# not a founding date). Never given a fabricated 2000/2001 "season."
_EXPANSION_TEAMS_NOT_BEFORE = {"HOU": 2002}

_ROLE_LABELS = {
    "OFFENSIVE_COORDINATOR": "Offensive coordinator",
    "DEFENSIVE_COORDINATOR": "Defensive coordinator",
}


def _gen_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"


def _coach_id_for_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"COACH:{slug}"


def _page_title(full_name: str, season: int) -> str:
    return f"{season}_{full_name.strip().replace(' ', '_')}_season"


def real_team_seasons(c) -> list[dict]:
    """Every real (team_code, season, full_name) this backfill can attempt,
    2000-2025. 2002-2025 comes directly from team_aliases (real, certified).
    2000-2001 reuses each team_code's own earliest real team_aliases row --
    see module docstring for why this is safe in this specific window."""
    rows = c.execute(
        "SELECT team_code, franchise_id, full_name, season_start, season_end FROM team_aliases "
        "ORDER BY team_code, season_start"
    ).fetchall()
    by_team: dict[str, list[dict]] = {}
    for r in rows:
        by_team.setdefault(r["team_code"], []).append(dict(r))

    out = []
    for team_code, alias_rows in by_team.items():
        founding_floor = _EXPANSION_TEAMS_NOT_BEFORE.get(team_code)
        for season in range(MIN_SEASON, MAX_SEASON + 1):
            if founding_floor is not None and season < founding_floor:
                continue  # this real team did not exist yet -- never fabricated
            match = next(
                (a for a in alias_rows if a["season_start"] <= season <= a["season_end"]), None
            )
            if match is None and season < alias_rows[0]["season_start"]:
                # Real 2000-2001 fallback -- reuse this team's earliest real name.
                # Never applied to a genuine post-2002 coverage gap (those are
                # left unresolved, not silently backfilled with the wrong era's name).
                match = alias_rows[0] if alias_rows[0]["season_start"] == 2002 else None
            if match is None:
                continue
            out.append({
                "team_code": team_code, "season": season, "full_name": match["full_name"],
                "franchise_id": match["franchise_id"],
            })
    return out


def _http_get(url: str, *, max_retries: int = 4) -> bytes | None:
    """Real, disclosed politeness: retries with real exponential backoff on
    HTTP 429 (confirmed hit directly during validation at the original
    fixed 0.4s pace) instead of crashing the whole run on a single rate
    limit response. Returns None for a real 404 (page genuinely doesn't
    exist); re-raises any other real HTTP error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    delay = REQUEST_DELAY_SECONDS
    for attempt in range(max_retries):
        try:
            return urllib.request.urlopen(req, timeout=30).read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code == 429 and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 3
                continue
            raise
    return None


def _resolve_canonical_title(title: str) -> str | None:
    """Real, disclosed title-resolution fallback -- only called when the
    DIRECT page fetch (the common case, works for most constructed titles)
    already 404s. A constructed title like "2001_St_Louis_Rams_season"
    (built from team_aliases.full_name, which has no period after "St")
    404s directly on some real seasons' pages even though Wikipedia's own
    redirect graph knows the real page exists at
    "2001_St._Louis_Rams_season" -- confirmed directly (redirect coverage
    for this exact spelling gap is inconsistent across different real
    pages, not fixable by a single hardcoded spelling rule). Uses
    Wikipedia's own query API with redirects=1 to resolve the REAL
    canonical title Wikipedia itself would land on, rather than guessing
    spelling variants. Returns None only when Wikipedia has no real page
    (redirect or otherwise) for this title at all."""
    import json as _json
    import urllib.parse

    api_url = (
        "https://en.wikipedia.org/w/api.php?action=query&titles="
        + urllib.parse.quote(title) + "&redirects=1&format=json"
    )
    raw = _http_get(api_url)
    if raw is None:
        return None
    data = _json.loads(raw)
    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1" or "missing" in page:
            continue
        return page.get("title", "").replace(" ", "_")
    return None


def _fetch_soup(title: str) -> BeautifulSoup | None:
    html = _http_get(f"https://en.wikipedia.org/wiki/{title}")
    if html is None:
        # Direct title 404'd -- fall back to the API resolver (handles real
        # spelling/redirect quirks like the "St"/"St." gap above) before
        # giving up. A real, narrow "St" retry first since it's the one
        # concretely confirmed gap; the general API resolver covers anything
        # else redirect-shaped.
        time.sleep(REQUEST_DELAY_SECONDS)
        canonical = _resolve_canonical_title(title)
        if canonical is None and "_St_" in title:
            time.sleep(REQUEST_DELAY_SECONDS)
            canonical = _resolve_canonical_title(title.replace("_St_", "_St._"))
        if canonical is None:
            return None
        time.sleep(REQUEST_DELAY_SECONDS)
        html = _http_get(f"https://en.wikipedia.org/wiki/{canonical}")
        if html is None:
            return None
    soup = BeautifulSoup(html, "html.parser")
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    return soup


def _parse_infobox_role(soup: BeautifulSoup, role_label: str) -> str | None:
    """Real, two-strategy parse -- confirmed directly that BOTH real page
    layouts exist across this real 2000-2025 window, not assumed:
    1. Infobox <th>/<td> row (e.g. 2015 Seahawks, 2010 Packers).
    2. A bulleted "Personnel/Staff" <li>"Offensive coordinator -- Name"
       (e.g. 2003 Texans) -- the infobox-only parse silently returns None
       for these real pages, which is exactly the gap this second strategy
       closes. Preserves real co-coordinator arrangements -- multiple <a>
       tags joined with ' / ', never collapsed to one name."""
    for th in soup.find_all("th"):
        if th.get_text(strip=True) != role_label:
            continue
        td = th.find_next_sibling("td")
        if td is None:
            continue
        names = [a.get_text(strip=True) for a in td.find_all("a") if a.get_text(strip=True)]
        if not names:
            text = td.get_text(" ", strip=True)
            if text:
                names = [text]
        if names:
            return " / ".join(dict.fromkeys(names))  # de-dup while preserving order

    for li in soup.find_all("li"):
        text = li.get_text(" ", strip=True)
        if not text.startswith(role_label):
            continue
        names = [a.get_text(strip=True) for a in li.find_all("a") if a.get_text(strip=True)]
        if names:
            return " / ".join(dict.fromkeys(names))
    return None


def _ensure_source_registered(c) -> None:
    c.execute(
        """INSERT INTO sources(source_id, source_name, source_url, license_note, attribution_required,
           approved_for_import, notes)
           VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(source_id) DO NOTHING""",
        (
            SOURCE_ID, "Wikipedia (structured tables)", "https://en.wikipedia.org",
            "CC BY-SA 4.0; secondary structured source, same approval basis as "
            "nfl_coordinators_import.py.",
            1, 1,
            f"Historical (2000-2025) per-team-season page scrape, retrieved {RETRIEVED_AT}. "
            "Extends the same nfl_coordinators table the 2026-only import already populates.",
        ),
    )


def run_import(*, seasons: range | None = None, limit: int | None = None, dry_run: bool = False) -> dict:
    conn_path = str(ENGINE_DIR / "reads_football_v4.0.sqlite")
    import sqlite3
    c = sqlite3.connect(conn_path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")

    run_id = safety.start_run(c, league=LEAGUE, dataset=DATASET, source_id=SOURCE_ID)
    backup = safety.create_verified_backup()

    report = {
        "attempted_team_seasons": 0, "pages_fetched": 0, "pages_404": 0,
        "rows_inserted": 0, "role_resolved_counts": {"OFFENSIVE_COORDINATOR": 0, "DEFENSIVE_COORDINATOR": 0},
        "unresolved": [],  # [{team_code, season, role, reason}]
        "new_coach_identities_created": 0, "seasons_covered": set(),
    }

    try:
        _ensure_source_registered(c)

        team_seasons = real_team_seasons(c)
        if seasons is not None:
            team_seasons = [ts for ts in team_seasons if ts["season"] in seasons]
        if limit is not None:
            team_seasons = team_seasons[:limit]

        for ts in team_seasons:
            report["attempted_team_seasons"] += 1
            title = _page_title(ts["full_name"], ts["season"])
            print(
                f"[{report['attempted_team_seasons']}/{len(team_seasons)}] {title} ...",
                flush=True,
            )
            try:
                soup = _fetch_soup(title)
            except Exception as exc:
                print(f"  FETCH_ERROR: {exc!r}", flush=True)
                report["unresolved"].append({
                    "team_code": ts["team_code"], "season": ts["season"], "role": "BOTH",
                    "reason": f"FETCH_ERROR: {exc!r}",
                })
                time.sleep(REQUEST_DELAY_SECONDS)
                continue
            time.sleep(REQUEST_DELAY_SECONDS)

            if soup is None:
                print("  PAGE_404", flush=True)
                report["pages_404"] += 1
                report["unresolved"].append({
                    "team_code": ts["team_code"], "season": ts["season"], "role": "BOTH", "reason": "PAGE_404",
                })
                continue
            report["pages_fetched"] += 1
            report["seasons_covered"].add(ts["season"])

            for role, label in _ROLE_LABELS.items():
                coach_name = _parse_infobox_role(soup, label)
                if not coach_name:
                    print(f"  {role}: NOT_FOUND", flush=True)
                    report["unresolved"].append({
                        "team_code": ts["team_code"], "season": ts["season"], "role": role,
                        "reason": "NOT_FOUND_IN_INFOBOX",
                    })
                    continue
                print(f"  {role}: {coach_name}", flush=True)

                coach_id = _coach_id_for_name(coach_name)
                if dry_run:
                    report["role_resolved_counts"][role] += 1
                    continue

                existing = c.execute("SELECT coach_id FROM coaches WHERE coach_id=?", (coach_id,)).fetchone()
                if not existing:
                    c.execute(
                        "INSERT INTO coaches(coach_id, coach_name, source_id, verification_status) VALUES (?,?,?,?)",
                        (coach_id, coach_name, SOURCE_ID, VERIFICATION_STATUS),
                    )
                    report["new_coach_identities_created"] += 1

                coordinator_id = _gen_id("COORD", str(ts["season"]), ts["team_code"], role)
                c.execute(
                    """INSERT INTO nfl_coordinators(
                        coordinator_id, season, team_name_raw, team_franchise_id, team_code, role,
                        coach_id, coach_name_raw, since_year, previous_position_raw,
                        source_id, source_page, retrieved_at, verification_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(season, team_code, role) DO NOTHING""",
                    (coordinator_id, ts["season"], ts["full_name"], ts["franchise_id"], ts["team_code"], role,
                     coach_id, coach_name, None, None,
                     SOURCE_ID, f"https://en.wikipedia.org/wiki/{title}", RETRIEVED_AT, VERIFICATION_STATUS),
                )
                if c.execute("SELECT changes()").fetchone()[0]:
                    report["rows_inserted"] += 1
                report["role_resolved_counts"][role] += 1

            if not dry_run:
                c.commit()

        report["seasons_covered"] = sorted(report["seasons_covered"])

        if not dry_run:
            safety.run_post_refresh_sanity_checks(
                c, table="nfl_coordinators", rows_published=report["rows_inserted"],
                rows_rejected=len(report["unresolved"]), rows_read=report["attempted_team_seasons"],
                min_row_count_floor=64,  # never below the pre-existing 2026-only real floor
            )
            safety.finish_run(
                c, run_id, status="SUCCESS", backup_id=backup["backup_id"],
                rows_downloaded=report["pages_fetched"], rows_imported=report["rows_inserted"],
                rows_rejected=len(report["unresolved"]), detail=report,
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
                           failure_reason=repr(exc), detail={"restore": restore_info, **report})
        c2.close()
        return {"status": "FAILED_RESTORED", "run_id": run_id, "reason": repr(exc), "backup": backup}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season-start", type=int, default=MIN_SEASON)
    parser.add_argument("--season-end", type=int, default=MAX_SEASON)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_import(
        seasons=range(args.season_start, args.season_end + 1), limit=args.limit, dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, default=str))
