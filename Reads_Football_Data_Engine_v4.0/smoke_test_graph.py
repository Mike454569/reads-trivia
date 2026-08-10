"""
Smoke test for graph_explorer.py against the freshly rebuilt, checksum-verified
Reads_v4_Database.sqlite (symlinked as reads_football_v4.0.sqlite in this same
directory, which is the exact path graph_explorer.py/api_server.py hardcode).

Read-only: does not modify the database. Run with:
    python3 smoke_test_graph.py
"""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).with_name("reads_football_v4.0.sqlite")

print(f"DB path: {DB}")
print(f"DB exists: {DB.exists()}")
if not DB.exists():
    print("FAIL: database file/symlink not found at the expected path.")
    sys.exit(1)

try:
    import graph_explorer
except Exception as e:
    print(f"FAIL: could not import graph_explorer.py: {e}")
    sys.exit(1)

results = []
def check(label, cond):
    results.append((label, bool(cond)))

# ---- 1. raw connection + table presence + row counts ----
conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

for table in ["graph_nodes", "graph_edges", "graph_path_cache", "puzzle_catalog", "puzzle_collisions"]:
    try:
        cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
        n = cur.fetchone()["c"]
        check(f"table '{table}' exists and is queryable (count={n})", n is not None)
        print(f"  {table}: {n} rows")
    except Exception as e:
        check(f"table '{table}' exists and is queryable", False)
        print(f"  {table}: ERROR {e}")

# ---- 2. PRAGMA foreign_key_check ----
cur.execute("PRAGMA foreign_key_check")
fk_errors = cur.fetchall()
check("PRAGMA foreign_key_check returns zero errors", len(fk_errors) == 0)
print(f"  foreign_key_check errors: {len(fk_errors)}")

# ---- 3. real graph_explorer.search() ----
try:
    search_results = graph_explorer.search("Mahomes", limit=5)
    check("search('Mahomes') returns at least one real result", len(search_results) > 0)
    print(f"  search('Mahomes') -> {len(search_results)} results, first: {dict(search_results[0]) if search_results else None}")
except Exception as e:
    check("search('Mahomes') runs without throwing", False)
    print(f"  search() ERROR: {e}")

# ---- 4. real graph_explorer.shortest_path() between two well-known, likely-connected entities ----
# Try a couple of plausible node_id pairs pulled straight from search results so this isn't guessing IDs.
try:
    src_candidates = graph_explorer.search("Patrick Mahomes", limit=3)
    dst_candidates = graph_explorer.search("Kansas City Chiefs", limit=3)
    if src_candidates and dst_candidates:
        src = src_candidates[0]
        dst = dst_candidates[0]
        path = graph_explorer.shortest_path(src["node_type"], src["node_id"], dst["node_type"], dst["node_id"])
        check("shortest_path(Mahomes, Chiefs) runs without throwing", True)
        check("shortest_path(Mahomes, Chiefs) actually finds a real connecting path", path is not None and len(path) > 0)
        print(f"  shortest_path({src['node_type']}:{src['node_id']} -> {dst['node_type']}:{dst['node_id']}) = {path}")

        # Also confirm the path cache actually gets used on a second identical call
        # (same query should now hit graph_path_cache instead of re-running BFS).
        path2 = graph_explorer.shortest_path(src["node_type"], src["node_id"], dst["node_type"], dst["node_id"])
        check("shortest_path is repeatable/consistent across two calls", path == path2)
    else:
        check("shortest_path smoke test had real candidates to test with", False)
        print(f"  no candidates found: src={src_candidates}, dst={dst_candidates}")
except Exception as e:
    check("shortest_path() runs without throwing", False)
    print(f"  shortest_path() ERROR: {e}")

# ---- 5. real graph_explorer.random_six() ----
try:
    six = graph_explorer.random_six(seed=42)
    check("random_six(seed=42) returns a real puzzle structure", isinstance(six, dict) and len(six) > 0)
    print(f"  random_six(seed=42) -> {six}")
    # Determinism check: same seed should give the same result.
    six_again = graph_explorer.random_six(seed=42)
    check("random_six is deterministic for the same seed", six == six_again)
except Exception as e:
    check("random_six() runs without throwing", False)
    print(f"  random_six() ERROR: {e}")

conn.close()

print("\n=== RESULTS ===")
all_pass = True
for label, passed in results:
    print(("PASS" if passed else "FAIL") + " - " + label)
    if not passed:
        all_pass = False
print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")
sys.exit(0 if all_pass else 1)
