"""Reads Football Engine v4.0 -- v1.1 historical player-team career facts.

PROBLEM (v1.0's own finding): canonical_players now has real historical
identities (Jerry Rice, Lawrence Taylor, ...) but PLAYED_FOR only covers
2006-2026 -- the engine knows WHO these players are but not WHICH TEAMS
they actually played for. "49ers x HOF -> Jerry Rice" cannot be answered.

SOURCE: nflverse-data's `stats_player` release (real, current, "courtesy"
of the same nflfastR/nflverse pipeline as every other NFLVERSE_DATA-sourced
table already in this database), files stats_player_reg_1999.csv through
stats_player_reg_2005.csv -- extends real coverage back to 1999 (7 seasons
earlier than the existing 2006 floor). Real files downloaded and
sha256-verified this session.

--- PART 2: PLAYED_FOR SEMANTICS (why this source, precisely) ---
The EXISTING 2006-2026 PLAYED_FOR/canonical_roster_seasons rows come from
roster SNAPSHOT files (nflverse "rosters" release, v0.7/v0.8) -- a player
could appear there without ever recording a single stat (inactive/practice
squad). This new 1999-2005 batch comes from `stats_player`, which requires
REAL RECORDED GAME STATS to appear at all (every one of the 11,987 real
rows checked has games>=1, zero blank/zero-game rows) -- if anything a
STRICTER, more conservative participation standard than the existing
roster-snapshot rows, and a better match to the spec's own preferred
definition ("actual player participation... not loose association").
Same predicate (PLAYED_FOR) is used for both eras -- normalized, not
forked into a second predicate, so every existing PLAYED_FOR consumer
(Grid, graph traversal, Player-From-Clues) keeps working unchanged --
but this evidentiary distinction is recorded honestly in a dedicated
source_releases row and in this file, per Part 2's explicit instruction
("normalize safely or create a distinct predicate" -- normalization was
chosen since the real-world relationship is identical either way and
fragmenting the predicate would break every existing consumer for a
provenance nuance, not a semantic one).

Known real limitation (grain, same class as v0.8's 2020-2026 rows): one
row per (season, player) as this release provides -- 0 of 11,987 real rows
have a duplicate player within a season (checked directly), so this
specific limitation doesn't cost anything for 1999-2005, but is still
documented for consistency. `av`/`starts` are not in this release format
and are left NULL.

--- SCOPE BOUNDARY (deliberate, Part 29: do not overbuild) ---
This import does NOT mint new canonical_players rows. It only attaches
PLAYED_FOR facts to players who are ALREADY canonical (from v0.7/v0.8's
2006-2026 roster imports or v1.0's historical draft-identity expansion).
A stats_player row for a player who was never drafted (1980+) and never
had a 2006+ roster season has no canonical home and is skipped, counted,
and reported -- not silently dropped, not used to mint a new identity
(identity expansion was v1.0's job, already done and QA'd; re-opening it
here would violate "do not turn this into another open-ended project").

--- FRANCHISE NORMALIZATION ---
Real, checked finding: this source uses 'LV'/'LA' for the Raiders/Rams
even in pre-relocation seasons (nflverse applies the current franchise
code retroactively in this release) while OTHER files in the SAME
download batch still use 'OAK'/'STL' -- an inconsistency in the upstream
data, not this script. Doesn't matter functionally: this codebase's
existing FRANCHISE_ALIASES (gateway/services/grid.py, established v0.7/
v0.8) already normalizes OAK/LA/STL to the same canonical codes (LV/LAR)
regardless of which raw form appears. One real NEW alias needed and
verified against the real team_aliases table: 'JAC' (old Jaguars code,
not in team_aliases at all) -> 'JAX' (team_aliases' real canonical code,
2002-2026). Blank recent_team values (1 real row across all 7 files,
"Steve Bono", 1999) are skipped -- no team to attribute, not guessed.

Usage:
    python3 import_historical_played_for_v11.py --dry-run
    python3 import_historical_played_for_v11.py --commit
"""
from __future__ import annotations

import argparse
import csv
import datetime
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).with_name("reads_football_v4.0.sqlite")
SCRATCH = Path("/private/tmp/claude-501/-Users-enterprise2-Desktop-2026-NFL-Draft-Guide/"
                "fd39f422-2063-48a6-aae2-58ffea8e072c/scratchpad/v11_import")
PLAYERS_CROSSWALK = Path("/private/tmp/claude-501/-Users-enterprise2-Desktop-2026-NFL-Draft-Guide/"
                          "fd39f422-2063-48a6-aae2-58ffea8e072c/scratchpad/v08_import/players.csv")
SEASONS = [1999, 2000, 2001, 2002, 2003, 2004, 2005]
SOURCE_URL_TMPL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_{year}.csv"

# Verified against the real team_aliases table -- 'JAC' isn't a recognized
# code there at all (only 'JAX', 2002-2026). Everything else this source
# uses (OAK/LA/LV/SD/STL) is already covered by the existing alias map this
# repo has used since v0.7/v0.8.
EXTRA_FRANCHISE_ALIASES = {"JAC": "JAX"}


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_team(raw: str, base_aliases: dict) -> str:
    if raw in EXTRA_FRANCHISE_ALIASES:
        raw = EXTRA_FRANCHISE_ALIASES[raw]
    return base_aliases.get(raw, raw)


def load_gsis_to_pfr():
    mapping = {}
    with open(PLAYERS_CROSSWALK, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("gsis_id") and row.get("pfr_id"):
                mapping[row["gsis_id"]] = row["pfr_id"]
    return mapping


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

    # Real franchise alias map already used by gateway/services/grid.py --
    # imported here by value (not by importing the module, to keep this
    # script standalone/runnable without the gateway package on sys.path).
    base_aliases = {"OAK": "LV", "SD": "LAC", "STL": "LAR", "LA": "LAR", "AZ": "ARI"}

    # QA must validate against the CANONICAL (post-normalization) code set, not
    # the raw team_aliases codes -- 'LAR' is this codebase's own chosen
    # canonical target (matching data/grid.js's vocabulary, established
    # v0.7/v0.8), and legitimately never appears as a raw team_aliases.team_code
    # itself (only 'LA'/'STL' do, both aliasing to it). Comparing against raw
    # codes directly would incorrectly reject every real Rams row.
    raw_team_codes = {r["team_code"] for r in c.execute("SELECT team_code FROM team_aliases")}
    real_franchise_codes = {canonical_team(code, base_aliases) for code in raw_team_codes}
    gsis_to_pfr = load_gsis_to_pfr()
    canonical_by_pfr = {r["pfr_id"]: r["player_id"] for r in c.execute(
        "SELECT player_id, pfr_id FROM canonical_players WHERE pfr_id IS NOT NULL")}

    file_hashes = {}
    all_rows = []
    total_rows_read = 0
    skipped_blank_team, skipped_zero_games, skipped_no_crosswalk, skipped_no_canonical = 0, 0, 0, 0
    for season in SEASONS:
        path = SCRATCH / f"stats_{season}.csv"
        file_hashes[season] = sha256_file(path)
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                total_rows_read += 1
                team_raw = row.get("recent_team", "")
                if not team_raw:
                    skipped_blank_team += 1
                    continue
                games = int(row["games"]) if row.get("games") else 0
                if games <= 0:
                    skipped_zero_games += 1
                    continue
                gsis = row["player_id"]
                pfr = gsis_to_pfr.get(gsis)
                if not pfr:
                    skipped_no_crosswalk += 1
                    continue
                player_id = canonical_by_pfr.get(pfr)
                if not player_id:
                    skipped_no_canonical += 1
                    continue
                team = canonical_team(team_raw, base_aliases)
                all_rows.append({
                    "season": int(row["season"]), "team": team, "player_id": player_id,
                    "position": row.get("position") or None, "games": games,
                })

    print(f"Real rows read across {len(SEASONS)} seasons ({SEASONS[0]}-{SEASONS[-1]}): {total_rows_read}")
    print(f"Skipped -- blank team: {skipped_blank_team}")
    print(f"Skipped -- games<=0: {skipped_zero_games}")
    print(f"Skipped -- no gsis->pfr crosswalk: {skipped_no_crosswalk}")
    print(f"Skipped -- pfr not in canonical_players (no canonical identity, not minted here): {skipped_no_canonical}")
    print(f"Real, safely-identified (season,team,player) facts: {len(all_rows)}")

    bad_teams = {r["team"] for r in all_rows if r["team"] not in real_franchise_codes}
    if bad_teams:
        print(f"QA FAIL: unrecognized team codes after normalization: {bad_teams}")
        sys.exit(1)

    existing_keys = {(r["season"], r["team_code"], r["player_id"])
                      for r in c.execute("SELECT season, team_code, player_id FROM canonical_roster_seasons")}
    rows_to_insert = [r for r in all_rows if (r["season"], r["team"], r["player_id"]) not in existing_keys]
    print(f"Already present (idempotent no-op): {len(all_rows) - len(rows_to_insert)}")
    print(f"NEW canonical_roster_seasons rows to insert: {len(rows_to_insert)}")

    if args.dry_run:
        print("\n--dry-run: no writes performed.")
        conn.close()
        return

    conn.execute("BEGIN")
    try:
        c.executemany(
            "INSERT INTO canonical_roster_seasons (season, team_code, player_id, position, "
            "verification_status, source_id, games) VALUES (?,?,?,?,?,?,?)",
            [(r["season"], r["team"], r["player_id"], r["position"], "SOURCE_BACKED", "NFLVERSE_DATA", r["games"])
             for r in rows_to_insert],
        )

        existing_player_nodes = {r["node_id"] for r in c.execute("SELECT node_id FROM graph_nodes WHERE node_type='nfl_player'")}
        played_for_edges, played_pos_edges = [], []
        for r in rows_to_insert:
            if r["player_id"] not in existing_player_nodes:
                continue  # should not happen (v1.0 confirmed near-universal graph_nodes coverage), but never assume
            played_for_edges.append(("nfl_player", r["player_id"], "PLAYED_FOR", "team", r["team"],
                                      r["season"], r["season"], "NFLVERSE_DATA", "SOURCE_BACKED"))
            if r["position"]:
                played_pos_edges.append(("nfl_player", r["player_id"], "PLAYED_POSITION", "position", r["position"],
                                          r["season"], r["season"], "NFLVERSE_DATA", "SOURCE_BACKED"))
        edge_sql = ("INSERT INTO graph_edges (subject_type, subject_id, predicate, object_type, object_id, "
                     "season_start, season_end, source_id, verification_status) VALUES (?,?,?,?,?,?,?,?,?)")
        c.executemany(edge_sql, played_for_edges)
        c.executemany(edge_sql, played_pos_edges)

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # Idempotency (same real bug class v1.0 found and fixed in
        # import_accolades_v09.py -- applied proactively here, then verified by
        # actually re-running this script twice, not assumed from the fix alone).
        c.executemany("DELETE FROM source_releases WHERE release_id=?", [(f"REL_NFLVERSE_STATS_PLAYER_{s}",) for s in SEASONS])
        release_rows = []
        for season in SEASONS:
            release_rows.append((
                f"REL_NFLVERSE_STATS_PLAYER_{season}", "NFLVERSE_DATA", "nflverse-data stats_player (reg)", str(season),
                SOURCE_URL_TMPL.format(year=season), now, file_hashes[season],
                "Code MIT; verify data terms.", "nflverse / nflverse-data", "reads-import-v1.1", "IMPORTED",
                len([r for r in rows_to_insert if r["season"] == season]),
                "v1.1 historical PLAYED_FOR extension. PARTICIPATION-based evidence (games>=1 required to appear "
                "in this source at all) -- a stricter standard than the roster-snapshot-based 2006-2026 rows. "
                "Same PLAYED_FOR predicate used for both eras (normalized, not forked) -- see "
                "import_historical_played_for_v11.py's module docstring for the full reasoning.",
            ))
        c.executemany(
            "INSERT INTO source_releases (release_id, source_id, dataset_name, release_version, source_url, "
            "retrieved_at, sha256, license_note, attribution_text, transform_version, import_status, row_count, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            release_rows,
        )

        c.execute("DELETE FROM import_batches WHERE batch_id='BATCH:v11_historical_played_for'")
        c.execute(
            "INSERT INTO import_batches (batch_id, dataset_name, source_id, source_file, source_sha256, "
            "started_at, finished_at, status, rows_read, rows_staged, rows_published, rows_rejected, "
            "qa_issue_count, transform_version, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("BATCH:v11_historical_played_for", "canonical_roster_seasons", "NFLVERSE_DATA",
             "stats_player_reg_1999..2005.csv", file_hashes[2005], now, now, "PUBLISHED",
             len(all_rows) + skipped_blank_team + skipped_zero_games + skipped_no_crosswalk + skipped_no_canonical,
             len(rows_to_insert), len(rows_to_insert),
             skipped_blank_team + skipped_zero_games + skipped_no_crosswalk + skipped_no_canonical, 0,
             "reads-import-v1.1",
             f"v1.1: +{len(rows_to_insert)} canonical_roster_seasons rows (1999-2005), "
             f"+{len(played_for_edges)} PLAYED_FOR, +{len(played_pos_edges)} PLAYED_POSITION edges. "
             f"Skipped: {skipped_blank_team} blank-team, {skipped_zero_games} zero-games, "
             f"{skipped_no_crosswalk} no gsis-pfr crosswalk, {skipped_no_canonical} no canonical_players match "
             f"(not minted -- identity expansion is v1.0's scope, not v1.1's)."),
        )

        conn.commit()
        print(f"\nCOMMITTED.")
        print(f"  canonical_roster_seasons: +{len(rows_to_insert)}")
        print(f"  graph_edges PLAYED_FOR: +{len(played_for_edges)}")
        print(f"  graph_edges PLAYED_POSITION: +{len(played_pos_edges)}")
    except Exception:
        conn.rollback()
        print("ERROR -- transaction rolled back, database unchanged.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
