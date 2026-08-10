"""Reads Football Engine v4.0 -- v1.0 historical canonical player identity
expansion.

PROBLEM (found by v0.9, this is the fix): `canonical_players` only has rows
for players with a real 2006-2026 roster season (how it was built in
v0.7/v0.8). Real legends whose careers ended before 2006 -- Jerry Rice,
Lawrence Taylor, Anthony Munoz -- have no canonical_players row, so real
accolade facts about them (v0.9) can't attach anywhere.

SOURCE (not a new download -- reusing an already-present, already-approved
table): `nfl_players_draft` (source_id=NFLVERSE_DATA, already
approved_for_import=1), 1980-2024, 12,253 rows. Real discovery this phase:
`graph_nodes`/`graph_edges` were ALREADY built from this full 1980-2024
universe independent of canonical_players -- Jerry Rice already has a real
`graph_nodes` row and real `DRAFTED_BY`/`DRAFTED_IN` edges (18,922 total
nfl_player graph_nodes vs canonical_players' 12,245). The actual gap is
purely in canonical_players, the relational identity table -- not in the
graph. This import does NOT add graph nodes/edges (they already exist);
it backfills the missing canonical_players rows so those already-real
graph identities have a proper relational home for accolade linking.

IDENTITY SAFETY -- `nfl_players_draft.id_quality` is an ALREADY-COMPUTED
identity-confidence field from a prior import phase:
    PFR_UNIQUE (10,442)              -- safe, exact, unambiguous PFR id
    SYNTHETIC_DRAFT_ID (1,805)       -- no real external id (derived from
                                         draft position + name) -- EXCLUDED
                                         from canonical promotion this
                                         phase ("do not create historical
                                         players from names alone")
    PFR_COLLISION_DISAMBIGUATED (6)  -- claims to be pre-resolved; VERIFIED
                                         independently below, not trusted
                                         blindly

A REAL BUG WAS FOUND in that pre-computed field, not assumed away: of the
3 distinct pfr_ids under PFR_COLLISION_DISAMBIGUATED
(JackBo00/EricCr00/JohnTy00), two (Bo Jackson, Craig Erickson -- verified
in v0.9 too) genuinely agree on (name, position) across their duplicate
rows and are safe. The third, JohnTy00, does NOT: nfl_players_draft has it
as BOTH "Ty Johnson" (RB, 2019 Detroit 6th-rounder) AND "Tyler Johnson"
(WR) -- two real, different people. Worse: canonical_players ALREADY has a
v0.8-imported row for PFR:JohnTy00 under a THIRD name, "Tyron Johnson"
(WR, real gsis_id/birth_date from the 2020-2026 roster import) -- meaning
this PFR code is claimed by at least three distinct real identities across
the underlying nflverse data, a genuine, pre-existing latent identity risk
that predates this phase and was never caught until this audit. NOT fixed
here (retroactively correcting an already-published v0.8 canonical_players
row is a separate, careful task) -- logged as a real `qa_issues` row and
reported honestly instead. JohnTy00 is excluded from this phase's new
canonicalizations (it's already in canonical_players from v0.8 regardless).

Usage:
    python3 import_historical_identity_v10.py --dry-run
    python3 import_historical_identity_v10.py --commit
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).with_name("reads_football_v4.0.sqlite")


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

    # --- identity verification: never trust id_quality blindly ---
    collision_pfrs = [r["pfr_id"] for r in c.execute(
        "SELECT DISTINCT pfr_id FROM nfl_players_draft WHERE id_quality='PFR_COLLISION_DISAMBIGUATED'"
    )]
    safe_collision_pfrs, blocked_collision = [], []
    for pfr in collision_pfrs:
        combos = c.execute(
            "SELECT DISTINCT player_name, position FROM nfl_players_draft WHERE pfr_id=?", (pfr,)
        ).fetchall()
        if len(combos) == 1:
            safe_collision_pfrs.append(pfr)
        else:
            blocked_collision.append((pfr, [(r["player_name"], r["position"]) for r in combos]))

    print(f"PFR_COLLISION_DISAMBIGUATED pfr_ids: {len(collision_pfrs)}")
    print(f"  verified safe (name+position agree): {safe_collision_pfrs}")
    print(f"  BLOCKED (real mismatch found): {blocked_collision}")

    dupes_within_unique = c.execute(
        "SELECT pfr_id, COUNT(*) c FROM nfl_players_draft WHERE id_quality='PFR_UNIQUE' GROUP BY pfr_id HAVING c>1"
    ).fetchall()
    if dupes_within_unique:
        print(f"QA FAIL: PFR_UNIQUE should never have duplicate pfr_ids, found {len(dupes_within_unique)}")
        sys.exit(1)

    safe_pfrs_placeholder = ",".join("?" for _ in safe_collision_pfrs) or "''"
    existing_pfrs = {r["pfr_id"] for r in c.execute("SELECT pfr_id FROM canonical_players WHERE pfr_id IS NOT NULL")}

    candidates = c.execute(
        f"""SELECT DISTINCT pfr_id, player_name, position FROM nfl_players_draft
            WHERE (id_quality='PFR_UNIQUE' OR pfr_id IN ({safe_pfrs_placeholder}))""",
        safe_collision_pfrs,
    ).fetchall()
    new_players = [r for r in candidates if r["pfr_id"] not in existing_pfrs]

    print(f"\nTotal verified-safe distinct pfr_ids in nfl_players_draft: {len(candidates)}")
    print(f"Already in canonical_players: {len(candidates) - len(new_players)}")
    print(f"NEW historical players to canonicalize: {len(new_players)}")

    # How many already have real graph_nodes/DRAFTED_BY (expected: nearly all,
    # since the graph was already built from the full nfl_players_draft universe).
    new_pfr_set = {r["pfr_id"] for r in new_players}
    already_graph_nodes = c.execute(
        "SELECT COUNT(*) FROM graph_nodes WHERE node_type='nfl_player' AND node_id IN ({})".format(
            ",".join("?" for _ in new_pfr_set)
        ),
        [f"PFR:{p}" for p in new_pfr_set],
    ).fetchone()[0] if new_pfr_set else 0
    print(f"Of those, already have a real graph_nodes entry (no new graph write needed): {already_graph_nodes}")

    if args.dry_run:
        print("\n--dry-run: no writes performed.")
        conn.close()
        return

    conn.execute("BEGIN")
    try:
        new_player_rows = [
            (f"PFR:{r['pfr_id']}", r["pfr_id"], r["player_name"], r["position"], "SOURCE_BACKED", "NFLVERSE_DATA")
            for r in new_players
        ]
        c.executemany(
            "INSERT INTO canonical_players (player_id, pfr_id, display_name, primary_position, "
            "verification_status, source_id) VALUES (?,?,?,?,?,?)",
            new_player_rows,
        )

        # Real QA record for the genuine JohnTy00 collision found this phase --
        # not fixed (a separate, careful task), but never silently dropped.
        existing_issue = c.execute(
            "SELECT issue_id FROM qa_issues WHERE entity_id='PFR:JohnTy00' AND issue_type='MULTIPLE_IDENTITIES_SAME_PFR_ID'"
        ).fetchone()
        if not existing_issue:
            import datetime
            c.execute(
                "INSERT INTO qa_issues (severity, entity_type, entity_id, field_name, issue_type, detail, status, created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                ("WARN", "nfl_player", "PFR:JohnTy00", "pfr_id", "MULTIPLE_IDENTITIES_SAME_PFR_ID",
                 "nfl_players_draft has pfr_id JohnTy00 under two different (name,position) combos -- "
                 "'Ty Johnson' (RB, 2019 DET 6th-rounder) and 'Tyler Johnson' (WR) -- despite being labeled "
                 "PFR_COLLISION_DISAMBIGUATED. canonical_players already has a THIRD identity under this same "
                 "pfr_id from the v0.8 roster import: 'Tyron Johnson' (WR, gsis_id 00-0036427). This PFR code "
                 "is claimed by at least 3 distinct real people across nflverse sources. Found by v1.0's "
                 "historical identity audit; NOT auto-fixed (retroactively correcting a published "
                 "canonical_players row needs its own careful review). Excluded from v1.0's new "
                 "canonicalizations.",
                 "OPEN", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            )
            print("Logged real QA issue for PFR:JohnTy00 (multi-identity collision).")

        conn.commit()
        print(f"\nCOMMITTED. canonical_players: +{len(new_player_rows)} new historical players.")
    except Exception:
        conn.rollback()
        print("ERROR -- transaction rolled back, database unchanged.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
