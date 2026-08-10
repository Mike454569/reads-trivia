"""Reads Football Engine v4.0 -- v1.0 Part 9: mirror player_accolades facts
into the graph as real relationships, for players who already have a real
nfl_player graph_nodes entry.

Design choice: these are EXISTENCE edges (a player has the honor or not),
not per-selection edges with a count. graph_edges has no count/quantity
column (season_start/season_end are real years, not encodable as a
count without being misleading) -- the real career-total counts stay in
the already-indexed, already-authoritative player_accolades.count_value
column, which Grid already queries directly. Adding a graph edge here is
about making these facts graph-traversable (e.g. a future Six Degrees
puzzle routing through "inducted into the Hall of Fame"), not about
duplicating the count.

season_start/season_end are left NULL on every edge here: HALL_OF_FAME has
no induction year in this source (see import_accolades_v09.py), and
All-Pro/Pro-Bowl are career totals with no single associated season.

New node_type: 'honor' (3 nodes: PRO_FOOTBALL_HOF, FIRST_TEAM_ALL_PRO,
PRO_BOWL). New predicates: INDUCTED_INTO, SELECTED_ALL_PRO, SELECTED_TO.

Idempotent: deletes its own prior edges (source_id='NFLVERSE_DATA',
predicate IN (...), object_type='honor') before re-inserting, safe to
re-run after any accolade re-link.

Usage:
    python3 add_accolade_graph_edges_v10.py --dry-run
    python3 add_accolade_graph_edges_v10.py --commit
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("reads_football_v4.0.sqlite")

HONOR_NODES = [
    ("PRO_FOOTBALL_HOF", "Pro Football Hall of Fame"),
    ("FIRST_TEAM_ALL_PRO", "First-Team All-Pro"),
    ("PRO_BOWL", "Pro Bowl"),
]

ACCOLADE_TO_PREDICATE_AND_HONOR = {
    "HALL_OF_FAME": ("INDUCTED_INTO", "PRO_FOOTBALL_HOF"),
    "ALL_PRO_FIRST_TEAM_CAREER_COUNT": ("SELECTED_ALL_PRO", "FIRST_TEAM_ALL_PRO"),
    "PRO_BOWL_CAREER_COUNT": ("SELECTED_TO", "PRO_BOWL"),
}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    existing_player_nodes = {r["node_id"] for r in c.execute("SELECT node_id FROM graph_nodes WHERE node_type='nfl_player'")}

    rows = c.execute("SELECT player_id, accolade_type FROM player_accolades").fetchall()
    edges_to_add = []
    skipped_no_node = 0
    for r in rows:
        if r["accolade_type"] not in ACCOLADE_TO_PREDICATE_AND_HONOR:
            continue
        if r["player_id"] not in existing_player_nodes:
            skipped_no_node += 1
            continue
        predicate, honor_id = ACCOLADE_TO_PREDICATE_AND_HONOR[r["accolade_type"]]
        edges_to_add.append((r["player_id"], predicate, honor_id))

    print(f"player_accolades rows considered: {len(rows)}")
    print(f"skipped (no real nfl_player graph_nodes entry): {skipped_no_node}")
    print(f"edges to add: {len(edges_to_add)}")
    for pred in ("INDUCTED_INTO", "SELECTED_ALL_PRO", "SELECTED_TO"):
        print(f"  {pred}: {sum(1 for e in edges_to_add if e[1] == pred)}")

    if args.dry_run:
        print("\n--dry-run: no writes performed.")
        conn.close()
        return

    conn.execute("BEGIN")
    try:
        existing_honor_nodes = {r["node_id"] for r in c.execute("SELECT node_id FROM graph_nodes WHERE node_type='honor'")}
        new_honor_nodes = [(nid, name, 0.05, "SOURCE_BACKED") for nid, name in HONOR_NODES if nid not in existing_honor_nodes]
        c.executemany(
            "INSERT INTO graph_nodes (node_type, node_id, display_name, popularity_score, verification_status) "
            "VALUES ('honor', ?, ?, ?, ?)",
            new_honor_nodes,
        )

        c.execute(
            "DELETE FROM graph_edges WHERE source_id='NFLVERSE_DATA' AND object_type='honor' "
            "AND predicate IN ('INDUCTED_INTO','SELECTED_ALL_PRO','SELECTED_TO')"
        )
        edge_rows = [
            ("nfl_player", player_id, predicate, "honor", honor_id, None, None, "NFLVERSE_DATA", "SOURCE_BACKED")
            for player_id, predicate, honor_id in edges_to_add
        ]
        c.executemany(
            "INSERT INTO graph_edges (subject_type, subject_id, predicate, object_type, object_id, "
            "season_start, season_end, source_id, verification_status) VALUES (?,?,?,?,?,?,?,?,?)",
            edge_rows,
        )
        conn.commit()
        print(f"\nCOMMITTED. graph_nodes (honor): +{len(new_honor_nodes)}. graph_edges: +{len(edge_rows)}.")
    except Exception:
        conn.rollback()
        print("ERROR -- transaction rolled back, database unchanged.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
