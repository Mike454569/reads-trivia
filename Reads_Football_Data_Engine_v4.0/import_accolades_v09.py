"""Reads Football Engine v4.0 -- v0.9 accolade import (Hall of Fame,
First-Team All-Pro, Pro Bowl -- career-level facts).

Source: nflverse-data's "draft_picks" release (courtesy of Pro Football
Reference per the release's own description) -- ALREADY the source
draft_facts/nfl_players_draft were built from (same 1980+ draft-class
scope, same source_id=NFLVERSE_DATA, already approved_for_import=1 in the
`sources` table). This is not a new source: the original import only kept
round/pick/team columns and silently dropped hof/allpro/probowls, which
were sitting in the same file the whole time -- the same "audit before
importing" lesson v0.8 learned from draft_facts applies again here, one
file over.

--- REAL SEMANTIC VERIFICATION (done before trusting these columns) ---
Cross-checked against well-documented real players before use:
  Randy Moss   allpro=4   (real, known First-Team All-Pro count)
  J.J. Watt    allpro=5   (real, known First-Team All-Pro count)
  Jerry Rice   allpro=10  (real, known First-Team All-Pro count)
  Lawrence Taylor allpro=8 (real, known First-Team All-Pro count)
  Anthony Munoz hof=TRUE, allpro=9 (real Hall of Famer, real count)
This confirms `allpro` is nflverse's PFR-sourced FIRST-TEAM All-Pro count
specifically (not combined First+Second team) -- matches Grid's own
"3+ First-Team All-Pro" criterion exactly, not a semantic mismatch.
`probowls` is a plain career Pro Bowl selection count, matching Grid's
"5+/10+ Pro Bowls" criteria exactly. `hof` is a real boolean (102 TRUE
rows in the real downloaded file).

--- REAL, HONEST COVERAGE LIMITATION (read before trusting this data) ---
This is a DRAFT-PICKS file: it only covers players who were actually
drafted (1980-2026). It has no rows for undrafted players. A genuinely
undrafted Hall-of-Famer/All-Pro/Pro-Bowler (rare, but real historically)
would be invisible to this source and would incorrectly read as "does not
qualify" rather than "unknown" if this were treated as complete-universe
truth. gateway/services/grid.py marks these criteria
SUPPORTED_WITH_COVERAGE_LIMIT for exactly this reason, not plain SUPPORTED.

Also: `hof` has no induction year in this source (Grid's own `hof`
criterion is a plain boolean, so this doesn't block the Grid use case, but
Part 5's "induction year" field is honestly left NULL, not fabricated).
`allpro`/`probowls` are CAREER TOTALS, not season-by-season selection
lists -- this source cannot say WHICH seasons a player made the Pro Bowl,
only how many times total. Stored as career-count facts (accolade_type
ending in _CAREER_COUNT, season=NULL), not fabricated per-season rows.

--- REAL IDENTITY CHECK ---
2 real pfr_player_id duplicates exist in the file (JackBo00 = Bo Jackson,
famously drafted twice -- 1986 Tampa Bay, 1987 Raiders; EricCr00 = Craig
Erickson, also drafted twice). Both have IDENTICAL hof/allpro/probowls
values across their duplicate rows (verified below, not assumed) --
aggregated safely via MAX() per player_id. The script still asserts
duplicate rows agree before aggregating, so a genuine future conflict
(different values under the same pfr_id -- the Byron Young failure mode
from v0.8) fails loudly instead of silently picking one.

Usage:
    python3 import_accolades_v09.py --dry-run
    python3 import_accolades_v09.py --commit
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).with_name("reads_football_v4.0.sqlite")
SCRATCH = Path("/private/tmp/claude-501/-Users-enterprise2-Desktop-2026-NFL-Draft-Guide/"
                "fd39f422-2063-48a6-aae2-58ffea8e072c/scratchpad/v09_import")
SOURCE_URL = "https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_accolades (
    accolade_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    accolade_type TEXT NOT NULL,
    season INTEGER,
    count_value INTEGER,
    induction_year INTEGER,
    source_id TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    notes TEXT
)
"""
CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_player_accolades_player_type ON player_accolades(player_id, accolade_type)"


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    print(f"DB: {DB}")
    file_hash = sha256_file(SCRATCH / "draft_picks.csv")
    print(f"Real file checksum: {file_hash}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    existing = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='player_accolades'"
    ).fetchone()
    print(f"player_accolades table already exists: {existing is not None}")

    pfr_to_player_id = {
        r["pfr_id"]: r["player_id"] for r in c.execute("SELECT player_id, pfr_id FROM canonical_players") if r["pfr_id"]
    }
    print(f"canonical_players with a real pfr_id (join key): {len(pfr_to_player_id)}")

    rows = list(csv.DictReader(open(SCRATCH / "draft_picks.csv", newline="", encoding="utf-8")))
    print(f"draft_picks.csv real rows: {len(rows)}")

    # Group by pfr_player_id -- assert any duplicate rows agree before aggregating
    # (the Bo Jackson / Craig Erickson dual-draft cases; a disagreement here would be
    # a real identity risk, same class of bug as v0.8's Byron Young case).
    by_pfr = {}
    for r in rows:
        pfr = r["pfr_player_id"]
        if not pfr:
            continue
        fact = (r["hof"] == "TRUE", int(r["allpro"] or 0), int(r["probowls"] or 0))
        if pfr in by_pfr:
            if by_pfr[pfr] != fact:
                print(f"QA FAIL: pfr_player_id {pfr} has CONFLICTING accolade values across duplicate rows: "
                      f"{by_pfr[pfr]} vs {fact} -- refusing to guess which is correct.")
                sys.exit(1)
        else:
            by_pfr[pfr] = fact

    no_pfr = sum(1 for r in rows if not r["pfr_player_id"])
    print(f"rows with no pfr_player_id (skipped, cannot safely identify): {no_pfr}")

    unmatched_pfr = [pfr for pfr in by_pfr if pfr not in pfr_to_player_id]
    print(f"distinct pfr_player_ids not found in canonical_players (skipped): {len(unmatched_pfr)}")

    hof_facts, allpro_facts, probowl_facts = [], [], []
    for pfr, (is_hof, allpro_ct, probowl_ct) in by_pfr.items():
        player_id = pfr_to_player_id.get(pfr)
        if not player_id:
            continue
        if is_hof:
            hof_facts.append(player_id)
        if allpro_ct > 0:
            allpro_facts.append((player_id, allpro_ct))
        if probowl_ct > 0:
            probowl_facts.append((player_id, probowl_ct))

    print(f"\nReal facts to import:")
    print(f"  HALL_OF_FAME: {len(hof_facts)}")
    print(f"  ALL_PRO_FIRST_TEAM_CAREER_COUNT (>0): {len(allpro_facts)}")
    print(f"  PRO_BOWL_CAREER_COUNT (>0): {len(probowl_facts)}")

    if args.dry_run:
        print("\n--dry-run: no writes performed.")
        conn.close()
        return

    conn.execute("BEGIN")
    try:
        c.execute(CREATE_TABLE_SQL)
        c.execute(CREATE_INDEX_SQL)

        # Idempotency: remove any prior v0.9 rows from this exact import before
        # re-inserting (safe to re-run without duplicating facts).
        c.execute("DELETE FROM player_accolades WHERE source_id='NFLVERSE_DATA' AND notes LIKE 'v0.9%'")

        rows_to_insert = []
        for player_id in hof_facts:
            rows_to_insert.append((
                f"ACC:HOF:{player_id}", player_id, "HALL_OF_FAME", None, None, None,
                "NFLVERSE_DATA", "SOURCE_BACKED", "v0.9 import from nflverse-data draft_picks (courtesy Pro Football Reference).",
            ))
        for player_id, ct in allpro_facts:
            rows_to_insert.append((
                f"ACC:APCAREER:{player_id}", player_id, "ALL_PRO_FIRST_TEAM_CAREER_COUNT", None, ct, None,
                "NFLVERSE_DATA", "SOURCE_BACKED", "v0.9 import; career total, not season-by-season (source limitation, see module docstring).",
            ))
        for player_id, ct in probowl_facts:
            rows_to_insert.append((
                f"ACC:PBCAREER:{player_id}", player_id, "PRO_BOWL_CAREER_COUNT", None, ct, None,
                "NFLVERSE_DATA", "SOURCE_BACKED", "v0.9 import; career total, not season-by-season (source limitation, see module docstring).",
            ))

        c.executemany(
            "INSERT INTO player_accolades (accolade_id, player_id, accolade_type, season, count_value, "
            "induction_year, source_id, verification_status, notes) VALUES (?,?,?,?,?,?,?,?,?)",
            rows_to_insert,
        )

        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        c.execute(
            "INSERT INTO source_releases (release_id, source_id, dataset_name, release_version, source_url, "
            "retrieved_at, sha256, license_note, attribution_text, transform_version, import_status, row_count, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("REL_NFLVERSE_DRAFT_PICKS_ACCOLADES_V09", "NFLVERSE_DATA", "nflverse-data draft_picks (hof/allpro/probowls)",
             "current", SOURCE_URL, now, file_hash, "Code MIT; verify data terms.",
             "nflverse / nflverse-data (courtesy Pro Football Reference)", "reads-import-v0.9", "IMPORTED",
             len(rows_to_insert), "v0.9: HOF/First-Team All-Pro career count/Pro Bowl career count, drafted-players-only coverage."),
        )
        c.execute(
            "INSERT INTO import_batches (batch_id, dataset_name, source_id, source_file, source_sha256, "
            "started_at, finished_at, status, rows_read, rows_staged, rows_published, rows_rejected, "
            "qa_issue_count, transform_version, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("BATCH:v09_accolades", "player_accolades", "NFLVERSE_DATA", "draft_picks.csv", file_hash,
             now, now, "PUBLISHED", len(rows), len(rows_to_insert), len(rows_to_insert),
             no_pfr + len(unmatched_pfr), 0, "reads-import-v0.9",
             f"v0.9: {len(hof_facts)} HOF, {len(allpro_facts)} All-Pro career-count, "
             f"{len(probowl_facts)} Pro Bowl career-count facts. {no_pfr} rows skipped (no pfr_player_id), "
             f"{len(unmatched_pfr)} distinct pfr_ids skipped (no canonical_players match)."),
        )
        conn.commit()
        print(f"\nCOMMITTED. player_accolades: +{len(rows_to_insert)} rows.")
    except Exception:
        conn.rollback()
        print("ERROR -- transaction rolled back, database unchanged.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
