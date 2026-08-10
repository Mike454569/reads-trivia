"""Reads Football Engine v4.0 -- v0.8 modern NFL roster import.

Extends the EXISTING canonical_players / canonical_roster_seasons tables
(built by the prior REL_NFLDATA_ROSTERS_2006_2019 import, which stops at
2019 -- see data_coverage.NFL_ROSTERS_HIST) with real 2020-2026 rosters from
nflverse-data's "rosters" GitHub release. Does NOT create a competing
roster table -- same tables, same verification_status/source_id
conventions, same "regular season only" semantic (data/grid.js's own
comment: "regular season, any length of stint") already established by the
historical import.

Source (already pre-approved in the `sources` table as NFLVERSE_ROSTERS,
approved_for_import=1):
  https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_<YEAR>.csv
  https://github.com/nflverse/nflverse-data/releases/download/players/players.csv
Real files downloaded this session to a local scratch dir (paths below) --
every sha256 recorded in source_releases matches the actually-downloaded
bytes, not a copied/assumed value.

Identity rule (canonical_rule in `meta`: "IDs are keys; display names are
never join keys"): gsis_id is the join key between the new roster files and
players.csv; pfr_id (100% populated in the existing canonical_players) is
the join key back to already-known players. A brand-new player (rookie
since 2020) gets player_id = "PFR:{pfr_id}" if players.csv has one, else
the honestly-labeled "GSIS:{gsis_id}" (a different, real namespace -- never
a fabricated PFR-style id for a player who doesn't have one).

Row grain (verified against the real downloaded files, not assumed): the
nflverse-data "rosters" release is ONE ROW PER (season, player) -- 3,216
rows for 2024 == 3,216 distinct gsis_ids, zero duplicates, confirmed by
direct count. `game_type`/`week` describe how far that player's team went
that season (REG/WC/DIV/CON/SB), not a per-week attendance log -- an
earlier version of this script filtered to game_type=='REG' assuming a
weekly log shape, which silently dropped every player on a playoff team
(caught by spot-checking Patrick Mahomes, who has exactly one 2024 row with
game_type='SB' and would have vanished entirely under that filter). Fixed:
no game_type filter, one canonical_roster_seasons row per source row.

Known real limitation from this row grain: the EXISTING 2006-2019 import
(from the older, weekly-granular nfldata source) captures 806 real
mid-season-trade cases as two roster rows per season. This new source
cannot -- a player traded mid-season here shows only their final team for
that season. Documented, not worked around (the source doesn't provide the
finer data; do not reconstruct it from guesses). `games`/`starts`/`av`
(present in the historical import) are also not in this release format and
are left NULL for new rows rather than fabricated or copied from the
unrelated historical convention.

Team-code normalization: the new roster files use nflverse's CURRENT-era
codes, which differ from the historical file's codes for two real,
already-documented cases -- confirmed against the existing team_aliases
table (franchise_id FR_LAR maps both 'STL' and 'LA' to the Rams; FR_LV maps
'OAK'; FR_LAC maps 'SD') plus one additional quirk found only in the 2026
pull ('AZ', 91 rows, alongside 'ARI'). Canonical target codes match
data/grid.js's own GRID_TEAM_NAMES vocabulary (which uses 'LAR', not the
newer 'LA') so nothing about the live frontend's team-code convention
changes.

Usage:
    python3 import_modern_rosters_v08.py --dry-run   # no writes, prints plan/counts
    python3 import_modern_rosters_v08.py --commit     # real writes, one transaction
"""
from __future__ import annotations

import argparse
import collections
import csv
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).with_name("reads_football_v4.0.sqlite")
SCRATCH = Path("/private/tmp/claude-501/-Users-enterprise2-Desktop-2026-NFL-Draft-Guide/"
                "fd39f422-2063-48a6-aae2-58ffea8e072c/scratchpad/v08_import")
SEASONS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]

# Verified against the real team_aliases table + one 2026-only quirk found
# by actually inspecting the downloaded files (see module docstring).
TEAM_CODE_ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LAR", "LA": "LAR", "AZ": "ARI"}

REAL_SOURCE_URLS = {
    "roster": "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{year}.csv",
    "players": "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv",
}


def canonical_team(raw: str) -> str:
    return TEAM_CODE_ALIASES.get(raw, raw)


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_players_csv():
    """Returns pfr_id->row and gsis_id->row maps from the real downloaded
    nflverse players.csv (identity master, NFLVERSE_PLAYERS source)."""
    by_pfr, by_gsis = {}, {}
    with open(SCRATCH / "players.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("pfr_id"):
                by_pfr[row["pfr_id"]] = row
            if row.get("gsis_id"):
                by_gsis[row["gsis_id"]] = row
    return by_pfr, by_gsis


def load_roster_rows(season: int):
    """One row per (season, gsis_id) already -- see module docstring. No
    game_type filter (that was the bug this replaced: filtering to 'REG'
    silently dropped every player whose row reflected a playoff game_type)."""
    path = SCRATCH / f"roster_{season}.csv"
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("gsis_id"):
                continue
            rows.append(row)
    return rows


def aggregate_season_team_player(rows):
    """Despite the name (kept for call-site compatibility), no aggregation
    happens -- the source is already one row per (season, player). QA-checks
    the one-row-per-player assumption still holds (raises if it doesn't,
    rather than silently picking one row) since a future release format
    change should fail loudly, not be quietly mishandled."""
    seen = {}
    for r in rows:
        key = (int(r["season"]), r["gsis_id"])
        if key in seen:
            raise ValueError(f"unexpected duplicate (season,gsis_id) row {key} -- "
                              f"source grain assumption no longer holds, do not silently aggregate")
        seen[key] = r
    out = []
    for r in rows:
        out.append({
            "season": int(r["season"]), "team": canonical_team(r["team"]), "gsis_id": r["gsis_id"],
            "position": r.get("position") or None,
            "jersey_number": r.get("jersey_number") or None,
            "status": r.get("status") or None,
            "games": None,  # not provided by this release format -- see module docstring
            "years_exp": r.get("years_exp") or None,
            "full_name": r.get("full_name") or None,
            "pfr_id": r.get("pfr_id") or None,
            "birth_date": r.get("birth_date") or None,
            "height": r.get("height") or None,
            "weight": r.get("weight") or None,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    print(f"DB: {DB}")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # --- 0. real file checksums (recorded into source_releases either way) ---
    file_hashes = {}
    for season in SEASONS:
        p = SCRATCH / f"roster_{season}.csv"
        file_hashes[f"roster_{season}"] = sha256_file(p)
    file_hashes["players"] = sha256_file(SCRATCH / "players.csv")
    print("Real file checksums:")
    for k, v in file_hashes.items():
        print(f"  {k}: {v}")

    # --- 1. identity crosswalk: backfill canonical_players.gsis_id via pfr_id ---
    by_pfr, by_gsis = load_players_csv()
    existing_players = {r["player_id"]: dict(r) for r in c.execute("SELECT * FROM canonical_players")}
    pfr_to_player_id = {r["pfr_id"]: r["player_id"] for r in existing_players.values() if r["pfr_id"]}

    gsis_backfill = []  # (gsis_id, player_id)
    scalar_backfill = []  # (birth_date, height_in, weight_lb, player_id)
    for player_id, row in existing_players.items():
        pfr = row["pfr_id"]
        if not pfr or pfr not in by_pfr:
            continue
        src = by_pfr[pfr]
        if src.get("gsis_id"):
            gsis_backfill.append((src["gsis_id"], player_id))
        bd = row["birth_date"] or (src.get("birth_date") or None)
        ht = row["height_in"] if row["height_in"] is not None else (int(src["height"]) if src.get("height") else None)
        wt = row["weight_lb"] if row["weight_lb"] is not None else (int(src["weight"]) if src.get("weight") else None)
        if (row["birth_date"] is None and bd) or (row["height_in"] is None and ht) or (row["weight_lb"] is None and wt):
            scalar_backfill.append((bd, ht, wt, player_id))

    gsis_to_player_id = {gsis: pid for gsis, pid in gsis_backfill}

    # --- 2. parse + aggregate all seasons ---
    new_roster_rows = []
    new_players_needed = {}  # gsis_id -> dict of fields for a brand-new canonical_players row
    for season in SEASONS:
        raw = load_roster_rows(season)
        agg = aggregate_season_team_player(raw)
        for row in agg:
            gsis = row["gsis_id"]
            if gsis in gsis_to_player_id:
                player_id = gsis_to_player_id[gsis]
            else:
                # players.csv (by_gsis, keyed by the stable gsis_id) is trusted OVER the roster
                # row's own pfr_id column -- caught a real upstream data bug this way: the 2023
                # roster_2023.csv file mislabels BOTH real, distinct "Byron Young"s (gsis
                # 00-0038978, a DL out of Alabama, and 00-0039137, a LB out of Tennessee -- same
                # 2023 draft class, same surname) with pfr_id='YounBy01', which would have merged
                # two different people under one player_id. players.csv correctly disambiguates
                # them (YounBy00 vs YounBy01) because it's keyed by the unambiguous gsis_id, not
                # copied per-row into a roster file that can (and here, does) get it wrong.
                pfr = (by_gsis.get(gsis, {}).get("pfr_id")) or row["pfr_id"]
                player_id = f"PFR:{pfr}" if pfr else f"GSIS:{gsis}"
                if gsis not in new_players_needed:
                    new_players_needed[gsis] = {
                        "player_id": player_id, "gsis_id": gsis, "pfr_id": pfr,
                        "display_name": row["full_name"],
                        "birth_date": row["birth_date"] or None,
                        "height_in": int(row["height"]) if row["height"] else None,
                        "weight_lb": int(row["weight"]) if row["weight"] else None,
                        "primary_position": row["position"],
                    }
                gsis_to_player_id[gsis] = player_id
            row["player_id"] = player_id
            new_roster_rows.append(row)

    existing_keys = {(r["season"], r["team_code"], r["player_id"])
                      for r in c.execute("SELECT season, team_code, player_id FROM canonical_roster_seasons")}
    roster_rows_to_insert = [r for r in new_roster_rows
                              if (r["season"], r["team"], r["player_id"]) not in existing_keys]

    print()
    print(f"Existing canonical_players: {len(existing_players)}")
    print(f"gsis_id backfilled for existing players: {len(gsis_backfill)}")
    print(f"scalar (birth_date/height/weight) backfilled: {len(scalar_backfill)}")
    print(f"Brand-new canonical_players to insert: {len(new_players_needed)}")
    print(f"New canonical_roster_seasons rows to insert: {len(roster_rows_to_insert)}")
    print(f"  (of {len(new_roster_rows)} total parsed season/team/player rows across {SEASONS[0]}-{SEASONS[-1]})")

    # --- 3. QA checks before any write ---
    real_franchise_codes = {canonical_team(r["team_code"]) for r in c.execute("SELECT team_code FROM team_aliases")}
    bad_teams = {r["team"] for r in roster_rows_to_insert if canonical_team(r["team"]) not in real_franchise_codes}
    if bad_teams:
        print(f"QA FAIL: unrecognized team codes after normalization: {bad_teams}")
        sys.exit(1)
    dupe_check = collections.Counter((r["season"], r["team"], r["player_id"]) for r in roster_rows_to_insert)
    dupes = [k for k, n in dupe_check.items() if n > 1]
    if dupes:
        print(f"QA FAIL: {len(dupes)} duplicate (season,team,player_id) rows in the new insert set, e.g. {dupes[:3]}")
        sys.exit(1)

    # Two different real gsis_ids must never mint the same player_id (would silently
    # merge two distinct people -- see the "Byron Young" case in the comment above).
    id_to_gsis = collections.defaultdict(set)
    for gsis, p in new_players_needed.items():
        id_to_gsis[p["player_id"]].add(gsis)
    collisions = {pid: gs for pid, gs in id_to_gsis.items() if len(gs) > 1}
    if collisions:
        print(f"QA FAIL: {len(collisions)} minted player_id(s) claimed by more than one gsis_id: {collisions}")
        sys.exit(1)
    also_existing = {pid for pid in id_to_gsis if pid in existing_players}
    if also_existing:
        print(f"QA FAIL: {len(also_existing)} minted player_id(s) already exist in canonical_players: {also_existing}")
        sys.exit(1)
    print("QA checks passed: all team codes recognized, no duplicate (season,team,player) keys, "
          "no player_id collisions between distinct gsis_ids or against existing players.")

    if args.dry_run:
        print("\n--dry-run: no writes performed.")
        conn.close()
        return

    # --- 4. real writes, one transaction ---
    conn.execute("BEGIN")
    try:
        c.executemany("UPDATE canonical_players SET gsis_id=? WHERE player_id=?", gsis_backfill)
        c.executemany(
            "UPDATE canonical_players SET birth_date=COALESCE(birth_date,?), "
            "height_in=COALESCE(height_in,?), weight_lb=COALESCE(weight_lb,?) WHERE player_id=?",
            scalar_backfill,
        )

        new_player_rows = [
            (p["player_id"], p["gsis_id"], p["pfr_id"], p["display_name"], p["birth_date"],
             p["height_in"], p["weight_lb"], p["primary_position"], "SOURCE_BACKED", "NFLVERSE_ROSTERS")
            for p in new_players_needed.values()
        ]
        c.executemany(
            "INSERT INTO canonical_players (player_id, gsis_id, pfr_id, display_name, birth_date, "
            "height_in, weight_lb, primary_position, verification_status, source_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            new_player_rows,
        )

        roster_insert_rows = [
            (r["season"], r["team"], r["player_id"], int(r["jersey_number"]) if r["jersey_number"] else None,
             r["position"], r["status"], "SOURCE_BACKED", "NFLVERSE_ROSTERS", r["games"],
             int(r["years_exp"]) if r["years_exp"] else None)
            for r in roster_rows_to_insert
        ]
        c.executemany(
            "INSERT INTO canonical_roster_seasons (season, team_code, player_id, jersey_number, position, "
            "roster_status, verification_status, source_id, games, years_experience) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            roster_insert_rows,
        )

        # --- graph extension: nfl_player nodes, PLAYED_FOR/PLAYED_POSITION/WORE_NUMBER edges ---
        existing_player_nodes = {r["node_id"] for r in c.execute("SELECT node_id FROM graph_nodes WHERE node_type='nfl_player'")}
        new_node_rows = [
            (p["player_id"], p["display_name"], 0.05, "SOURCE_BACKED")
            for p in new_players_needed.values() if p["player_id"] not in existing_player_nodes
        ]
        # graph_nodes PK is (node_type, node_id) -- see gateway/services/graph.py's earlier schema read
        c.executemany(
            "INSERT INTO graph_nodes (node_type, node_id, display_name, popularity_score, verification_status) "
            "VALUES ('nfl_player', ?, ?, ?, ?)",
            new_node_rows,
        )

        existing_jersey_nodes = {r["node_id"] for r in c.execute("SELECT node_id FROM graph_nodes WHERE node_type='jersey_number'")}
        needed_numbers = {str(int(r["jersey_number"])) for r in roster_rows_to_insert if r["jersey_number"]}
        new_jersey_nodes = [(n, n, 0.02, "SOURCE_BACKED") for n in needed_numbers if n not in existing_jersey_nodes]
        c.executemany(
            "INSERT INTO graph_nodes (node_type, node_id, display_name, popularity_score, verification_status) "
            "VALUES ('jersey_number', ?, ?, ?, ?)",
            new_jersey_nodes,
        )

        played_for_edges, played_pos_edges, wore_number_edges = [], [], []
        for r in roster_rows_to_insert:
            played_for_edges.append(("nfl_player", r["player_id"], "PLAYED_FOR", "team", r["team"],
                                      r["season"], r["season"], "NFLVERSE_ROSTERS", "SOURCE_BACKED"))
            if r["position"]:
                played_pos_edges.append(("nfl_player", r["player_id"], "PLAYED_POSITION", "position", r["position"],
                                          r["season"], r["season"], "NFLVERSE_ROSTERS", "SOURCE_BACKED"))
            if r["jersey_number"]:
                wore_number_edges.append(("nfl_player", r["player_id"], "WORE_NUMBER", "jersey_number",
                                           str(int(r["jersey_number"])), r["season"], r["season"],
                                           "NFLVERSE_ROSTERS", "SOURCE_BACKED"))

        edge_sql = ("INSERT INTO graph_edges (subject_type, subject_id, predicate, object_type, object_id, "
                     "season_start, season_end, source_id, verification_status) VALUES (?,?,?,?,?,?,?,?,?)")
        c.executemany(edge_sql, played_for_edges)
        c.executemany(edge_sql, played_pos_edges)
        c.executemany(edge_sql, wore_number_edges)

        # --- source_releases: real files, real hashes, real timestamps ---
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        release_rows = []
        for season in SEASONS:
            release_rows.append((
                f"REL_NFLVERSE_ROSTERS_{season}", "NFLVERSE_ROSTERS", "nflverse-data rosters", str(season),
                REAL_SOURCE_URLS["roster"].format(year=season), now, file_hashes[f"roster_{season}"],
                "Code MIT; verify data terms.", "nflverse / nflverse-data", "reads-import-v0.8", "IMPORTED",
                len([r for r in roster_rows_to_insert if r["season"] == season]),
                "v0.8 modern roster extension; one row per (season, player) as provided by the source "
                "(no mid-season-trade granularity in this release -- see module docstring).",
            ))
        release_rows.append((
            "REL_NFLVERSE_PLAYERS_V08", "NFLVERSE_PLAYERS", "nflverse-data players", "current",
            REAL_SOURCE_URLS["players"], now, file_hashes["players"],
            "Check release/repo terms.", "nflverse / nflverse-data", "reads-import-v0.8", "IMPORTED",
            len(new_players_needed), "Identity crosswalk (gsis_id/pfr_id/birth_date/height/weight) for v0.8.",
        ))
        c.executemany(
            "INSERT INTO source_releases (release_id, source_id, dataset_name, release_version, source_url, "
            "retrieved_at, sha256, license_note, attribution_text, transform_version, import_status, row_count, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            release_rows,
        )

        batch_id = "BATCH:v08_modern_rosters"
        c.execute(
            "INSERT INTO import_batches (batch_id, dataset_name, source_id, source_file, source_sha256, "
            "started_at, finished_at, status, rows_read, rows_staged, rows_published, rows_rejected, "
            "qa_issue_count, transform_version, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (batch_id, "canonical_roster_seasons", "NFLVERSE_ROSTERS", "roster_2020..2026.csv + players.csv",
             file_hashes["roster_2024"], now, now, "PUBLISHED", len(new_roster_rows), len(roster_rows_to_insert),
             len(roster_rows_to_insert), 0, 0, "reads-import-v0.8",
             f"v0.8: +{len(roster_rows_to_insert)} roster-season rows, +{len(new_players_needed)} new players, "
             f"+{len(played_for_edges)} PLAYED_FOR, +{len(played_pos_edges)} PLAYED_POSITION, "
             f"+{len(wore_number_edges)} WORE_NUMBER (new predicate) edges."),
        )

        # --- data_coverage: update only with real, just-imported facts ---
        c.execute(
            "UPDATE data_coverage SET coverage_end=2026, current_through='2026 (preseason rosters present)', "
            "completeness='HISTORICAL_AND_CURRENT_IMPORTED', notes=? WHERE domain_id='NFL_ROSTERS_HIST'",
            (f"v0.8: extended 2006-2019 historical import with real 2020-2026 nflverse-data 'rosters' release "
             f"REG-season rows ({len(roster_rows_to_insert)} new roster-season rows). "
             f"Renamed in spirit only -- NFL_ROSTERS_CURRENT below still tracks the un-imported broader-history adapter.",),
        )
        c.execute(
            "UPDATE data_coverage SET completeness='SUPERSEDED_BY_NFL_ROSTERS_HIST', production_safe=0, "
            "notes='v0.8: NFL_ROSTERS_HIST now covers 2006-2026 via the nflverse-data rosters release; "
            "this row (1920-2026 via a different loader) was never imported and is not needed now.' "
            "WHERE domain_id='NFL_ROSTERS_CURRENT'",
        )

        conn.commit()
        print("\nCOMMITTED.")
        print(f"  canonical_players: +{len(new_player_rows)} new, {len(gsis_backfill)} gsis_id backfilled, "
              f"{len(scalar_backfill)} scalar-backfilled")
        print(f"  canonical_roster_seasons: +{len(roster_insert_rows)}")
        print(f"  graph_nodes (nfl_player): +{len(new_node_rows)}")
        print(f"  graph_nodes (jersey_number, new predicate/type): +{len(new_jersey_nodes)}")
        print(f"  graph_edges PLAYED_FOR: +{len(played_for_edges)}")
        print(f"  graph_edges PLAYED_POSITION: +{len(played_pos_edges)}")
        print(f"  graph_edges WORE_NUMBER (new): +{len(wore_number_edges)}")
    except Exception:
        conn.rollback()
        print("ERROR -- transaction rolled back, database unchanged.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
