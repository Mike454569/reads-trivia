"""Coach Connections v2 -- the real, graph-driven engine.

Root cause of the old "~6 usable puzzles" ceiling, found by measuring the
actual data (not assumed): the old public adapter (public_six_degrees.py)
drew exclusively from `graph_path_cache`, a 500-row PRE-COMPUTED table
built once for team<->coach and team<->team pairs only. Only 23 of those
500 rows happened to be entirely typed within the public-safe node set.
That cache is a tiny, stale snapshot -- it was never the limit of what the
underlying `graph_edges` table actually supports.

Measured real graph (this pass, direct queries against the live DB):
  - 177 NFL coaches, ALL with real COACHED_TEAM_IN_SEASON edges (clean,
    single-source, zero parsing artifacts -- confirmed directly; unlike
    cfb_coaches, which has known artifact rows and is NOT used here).
  - 18,922 NFL players.
  - graph_edges: 908,274 real TEAMMATE_OF edges (nfl_player<->nfl_player,
    season-scoped, verification_status=DERIVED_SOURCE_BACKED -- an already-
    established safe tier, same convention identity_bridge_v16.py uses),
    60,246 PLAYED_FOR edges, 936 COACHED_TEAM_IN_SEASON edges (1999-2026),
    21,294 WORE_NUMBER, 12,253 DRAFTED_BY -- all real, all indexed
    (idx_graph_edges_subject / idx_graph_edges_object).
  - `Reads_Football_Data_Engine_v4.0/graph_explorer.py`'s own
    `shortest_path()` already does real live BFS directly against
    graph_edges when its cache misses -- confirming a live approach is
    viable on this schema. This module writes its OWN traversal instead of
    calling that one directly because it needs two things the generic
    version doesn't have: (1) derived PLAYER<->COACH edges (below), (2)
    bidirectional search (see find_path()) for real performance against
    this graph's actual hub sizes.

--- DERIVED RELATIONSHIPS (computed live via SQL JOIN, never written to
    graph_edges -- this whole module stays read-only against the Engine DB,
    preserving the same concurrency-safety proof every other public path
    in this project already relies on) ---
  PLAYER --PLAYED_UNDER--> COACH: player X played for team T in season S
  (a real PLAYED_FOR edge) AND coach C coached team T in season S (a real
  COACHED_TEAM_IN_SEASON edge, season overlap required) => X played under
  C. Never derived from name similarity -- both underlying edges are
  independently certified, joined only on (team, season).
  COACH <-> COACH (same team, different eras): NOT implemented as a
  synthetic direct edge -- per the explicit instruction to "connect through
  the TEAM node without falsely claiming they directly coached together,"
  two coaches of the same team in different seasons are already naturally
  connected via two real COACHED_TEAM_IN_SEASON edges through the real
  `team` node in the traversal below -- an honest 2-hop path, not a
  fabricated 1-hop one.

Every edge (real or derived) carries the true season it happened in, AND
the true real-world subject/object direction (never inferred from which
side of the search happened to reach it) -- returned to the client, never
hidden.
"""
from __future__ import annotations

import collections
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402,F401  (kept for parity with sibling services)

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import graph_explorer  # noqa: E402  Engine's own label()/search() -- reused, never modified

# The certified, safe-for-a-public-connections-game predicate set. Deliberately
# narrower than every predicate in graph_edges (e.g. excludes CFB_* entirely --
# this mode stays NFL-only, matching the existing public product framing;
# excludes team_game/stadium/record-shaped bookkeeping predicates that don't
# represent a real "these two are connected" fact a player would recognize).
CERTIFIED_PREDICATES = frozenset({
    "TEAMMATE_OF", "PLAYED_FOR", "COACHED_TEAM_IN_SEASON", "DRAFTED_BY", "WORE_NUMBER",
})
PUBLIC_NODE_TYPES = frozenset({"nfl_player", "team", "coach"})
MAX_FANOUT_PER_PREDICATE = 15  # bounded sampling -- see perf note below
MAX_PATH_DEPTH = 4
# Perf, measured directly against the real graph: a one-directional BFS at
# depth 4 (real hub nodes -- an NFL team can have 2000+ historical
# PLAYED_FOR/DRAFTED_BY edges) took up to 29s. Bidirectional search (see
# find_path()) plus this fanout cap brings that down to a real, measured
# sub-2s for generation and tens-of-milliseconds for a single-node
# is_legal_move() check (see test_coach_connections_graph.py).


def _connect():
    return graph_explorer.connect()


def _label(c, node_type: str, node_id: str) -> str:
    return graph_explorer.label(c, node_type, node_id)


Edge = Dict[str, Any]  # {subject_type, subject_id, predicate, object_type, object_id, season_start, season_end}


def _real_neighbors(c, node_type: str, node_id: str, *, rng: Optional[random.Random] = None) -> List[Tuple[Tuple[str, str], Edge]]:
    """Every real (or derived-but-certified) neighbor of one node, bounded
    for fan-out. Returns (neighbor_node, edge) pairs where `edge` always
    carries the TRUE real-world subject/object roles (never inferred from
    which side of a search reached it) -- this is what makes bidirectional
    search safe: whichever direction discovers an edge, its stored meaning
    is preserved exactly."""
    out: List[Tuple[Tuple[str, str], Edge]] = []

    placeholders = ",".join("?" for _ in CERTIFIED_PREDICATES)
    outgoing = c.execute(
        f"SELECT predicate, object_type, object_id, season_start, season_end FROM graph_edges "
        f"WHERE subject_type=? AND subject_id=? AND predicate IN ({placeholders}) "
        f"AND verification_status NOT IN ('AUTO_REVIEW','CONFLICT')",
        (node_type, node_id, *CERTIFIED_PREDICATES),
    ).fetchall()
    incoming = c.execute(
        f"SELECT predicate, subject_type, subject_id, season_start, season_end FROM graph_edges "
        f"WHERE object_type=? AND object_id=? AND predicate IN ({placeholders}) "
        f"AND verification_status NOT IN ('AUTO_REVIEW','CONFLICT')",
        (node_type, node_id, *CERTIFIED_PREDICATES),
    ).fetchall()

    by_pred: Dict[str, List[Tuple[Tuple[str, str], Edge]]] = collections.defaultdict(list)
    for r in outgoing:
        if r["object_type"] not in PUBLIC_NODE_TYPES:
            continue
        nbr = (r["object_type"], r["object_id"])
        edge: Edge = {"subject_type": node_type, "subject_id": node_id, "predicate": r["predicate"],
                      "object_type": r["object_type"], "object_id": r["object_id"],
                      "season_start": r["season_start"], "season_end": r["season_end"]}
        by_pred[r["predicate"]].append((nbr, edge))
    for r in incoming:
        if r["subject_type"] not in PUBLIC_NODE_TYPES:
            continue
        nbr = (r["subject_type"], r["subject_id"])
        edge = {"subject_type": r["subject_type"], "subject_id": r["subject_id"], "predicate": r["predicate"],
                "object_type": node_type, "object_id": node_id,
                "season_start": r["season_start"], "season_end": r["season_end"]}
        by_pred[r["predicate"]].append((nbr, edge))

    for pred, cands in by_pred.items():
        if len(cands) > MAX_FANOUT_PER_PREDICATE:
            (rng or random).shuffle(cands)
            cands = cands[:MAX_FANOUT_PER_PREDICATE]
        out.extend(cands)

    # Derived PLAYER <-> COACH edges (see module docstring) -- only expanded
    # from a nfl_player or coach node, computed live via JOIN, never stored.
    # These carry their own real subject/object roles (player is always the
    # subject of PLAYED_UNDER, coach always the subject of COACHED_PLAYER),
    # matching the direction the relationship actually reads in English.
    if node_type == "nfl_player":
        # A LIMIT inside the SQL itself (not fetch-all-then-sample) --
        # measured directly: the fetch-all version of this exact join took
        # ~390ms for a busy coach (thousands of matching rows before the
        # season-range join filter can apply); a bounded LIMIT keeps this
        # fast enough for a live per-move check. A small multiple of the
        # real cap is still fetched so the later shuffle has real variety
        # to pick from, not just SQLite's incidental row order.
        rows = c.execute(
            """SELECT c.subject_id AS coach_id, p.object_id AS team_id, p.season_start AS season
               FROM graph_edges p JOIN graph_edges c
                 ON c.predicate='COACHED_TEAM_IN_SEASON' AND c.object_type='team' AND c.object_id=p.object_id
                 AND c.season_start<=p.season_start AND c.season_end>=p.season_start
               WHERE p.predicate='PLAYED_FOR' AND p.subject_type='nfl_player' AND p.subject_id=?
                 AND p.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
                 AND c.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
               LIMIT ?""",
            (node_id, MAX_FANOUT_PER_PREDICATE * 4),
        ).fetchall()
        rows = list(rows)
        if len(rows) > MAX_FANOUT_PER_PREDICATE:
            (rng or random).shuffle(rows)
            rows = rows[:MAX_FANOUT_PER_PREDICATE]
        for r in rows:
            nbr = ("coach", r["coach_id"])
            edge = {"subject_type": "nfl_player", "subject_id": node_id, "predicate": "PLAYED_UNDER",
                    "object_type": "coach", "object_id": r["coach_id"],
                    "season_start": r["season"], "season_end": r["season"], "via_team": r["team_id"]}
            out.append((nbr, edge))
    elif node_type == "coach":
        rows = c.execute(
            """SELECT p.subject_id AS player_id, c.object_id AS team_id, c.season_start AS season
               FROM graph_edges c JOIN graph_edges p
                 ON p.predicate='PLAYED_FOR' AND p.subject_type='nfl_player' AND p.object_type='team'
                 AND p.object_id=c.object_id AND p.season_start<=c.season_end AND p.season_end>=c.season_start
               WHERE c.predicate='COACHED_TEAM_IN_SEASON' AND c.subject_id=?
                 AND c.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
                 AND p.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
               LIMIT ?""",
            (node_id, MAX_FANOUT_PER_PREDICATE * 4),
        ).fetchall()
        rows = list(rows)
        if len(rows) > MAX_FANOUT_PER_PREDICATE:
            (rng or random).shuffle(rows)
            rows = rows[:MAX_FANOUT_PER_PREDICATE]
        for r in rows:
            nbr = ("nfl_player", r["player_id"])
            edge = {"subject_type": "coach", "subject_id": node_id, "predicate": "COACHED_PLAYER",
                    "object_type": "nfl_player", "object_id": r["player_id"],
                    "season_start": r["season"], "season_end": r["season"], "via_team": r["team_id"]}
            out.append((nbr, edge))

    return out


def find_path(c, start: Tuple[str, str], end: Tuple[str, str], *, max_depth: int = MAX_PATH_DEPTH,
              rng: Optional[random.Random] = None) -> Optional[List[Edge]]:
    """Real, live BIDIRECTIONAL BFS over the certified + derived edge set --
    the actual generation/validation engine, not a lookup into
    graph_path_cache (never queried by this module at all).

    Bidirectional (search from both start AND end, meet in the middle) is a
    real, standard algorithmic fix for this graph's actual shape, not a
    hack: real hub nodes (an NFL team can have 2000+ historical
    PLAYED_FOR/DRAFTED_BY edges) make a one-directional search's node count
    grow like fanout^depth -- measured directly, a depth-4 one-directional
    search over this real graph took up to 29s. Two roughly-half-depth
    searches meeting in the middle grow like ~2*fanout^(depth/2), which is
    what keeps this fast in practice.

    Returns a list of real Edge dicts (each with true subject/object roles,
    see _real_neighbors) from start to end, or None if no path exists
    within max_depth."""
    if start == end:
        return []
    if max_depth <= 0:
        return None

    forward: Dict[Tuple[str, str], List[Edge]] = {start: []}
    backward: Dict[Tuple[str, str], List[Edge]] = {end: []}
    frontier_f = [start]
    frontier_b = [end]
    depth_f = depth_b = 0
    half = (max_depth + 1) // 2

    def _expand_forward() -> Optional[Tuple[str, str]]:
        nonlocal frontier_f
        nxt_frontier = []
        for node in frontier_f:
            for nbr, edge in _real_neighbors(c, node[0], node[1], rng=rng):
                if nbr in forward:
                    continue
                forward[nbr] = forward[node] + [edge]
                if nbr in backward:
                    return nbr
                nxt_frontier.append(nbr)
        frontier_f = nxt_frontier
        return None

    def _expand_backward() -> Optional[Tuple[str, str]]:
        nonlocal frontier_b
        nxt_frontier = []
        for node in frontier_b:
            for nbr, edge in _real_neighbors(c, node[0], node[1], rng=rng):
                if nbr in backward:
                    continue
                # `edge` is a real subject->object fact from `node` to `nbr`.
                # We reached `node` walking backward from `end`; prepending
                # this edge keeps backward[nbr] as a real, correctly-ordered
                # subject->object chain from `nbr` through to `end`.
                backward[nbr] = [edge] + backward[node]
                if nbr in forward:
                    return nbr
                nxt_frontier.append(nbr)
        frontier_b = nxt_frontier
        return None

    while depth_f + depth_b < max_depth and frontier_f and frontier_b:
        if len(frontier_f) <= len(frontier_b):
            meet = _expand_forward()
            depth_f += 1
        else:
            meet = _expand_backward()
            depth_b += 1
        if meet is not None:
            return forward[meet] + backward[meet]
        if depth_f >= half and depth_b >= half:
            break
    return None


def is_legal_move(c, current: Tuple[str, str], proposed: Tuple[str, str]) -> Optional[Edge]:
    """Real-time single-hop validation: is there a genuine certified (or
    derived-certified) edge directly connecting `current` to `proposed`?
    Returns the real edge if so (never just True/False -- the caller needs
    the real predicate/season to show the player what actually connects
    them), else None. This is what makes multiple valid paths work: it
    never compares against one precomputed canonical path, only against
    the live graph.

    Deliberately does NOT call _real_neighbors() (real bug found in live
    testing: a coach with 279 real derived PLAYER<->COACH relationships only
    ever surfaces LIMIT 60 -> sampled-to-15 of them there, since that
    function is tuned for BFS breadth/speed, not exhaustiveness -- a
    perfectly legal move that find_path() itself had just used to build a
    puzzle's canonical path was then rejected here because it didn't survive
    a second, independently-sampled draw). Authoritative move validation
    must check the exact (current, proposed) pair directly -- cheap, since
    it's an indexed lookup for two specific ids, not a fan-out scan -- so a
    real edge is never missed regardless of how high-fanout either node is."""
    cur_t, cur_id = current
    prop_t, prop_id = proposed
    if prop_t not in PUBLIC_NODE_TYPES:
        return None

    placeholders = ",".join("?" for _ in CERTIFIED_PREDICATES)
    row = c.execute(
        f"SELECT predicate, subject_type, subject_id, object_type, object_id, season_start, season_end "
        f"FROM graph_edges WHERE predicate IN ({placeholders}) "
        f"AND verification_status NOT IN ('AUTO_REVIEW','CONFLICT') "
        f"AND ((subject_type=? AND subject_id=? AND object_type=? AND object_id=?) "
        f"OR (subject_type=? AND subject_id=? AND object_type=? AND object_id=?)) LIMIT 1",
        (*CERTIFIED_PREDICATES, cur_t, cur_id, prop_t, prop_id, prop_t, prop_id, cur_t, cur_id),
    ).fetchone()
    if row:
        return {"subject_type": row["subject_type"], "subject_id": row["subject_id"],
                "predicate": row["predicate"], "object_type": row["object_type"], "object_id": row["object_id"],
                "season_start": row["season_start"], "season_end": row["season_end"]}

    # Derived PLAYER <-> COACH (module docstring) -- exact pair check, never sampled.
    if {cur_t, prop_t} == {"nfl_player", "coach"}:
        player_id = cur_id if cur_t == "nfl_player" else prop_id
        coach_id = cur_id if cur_t == "coach" else prop_id
        drow = c.execute(
            """SELECT p.season_start AS season
               FROM graph_edges p JOIN graph_edges c
                 ON c.predicate='COACHED_TEAM_IN_SEASON' AND c.object_type='team' AND c.object_id=p.object_id
                 AND c.season_start<=p.season_start AND c.season_end>=p.season_start
               WHERE p.predicate='PLAYED_FOR' AND p.subject_type='nfl_player' AND p.subject_id=?
                 AND c.subject_id=?
                 AND p.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
                 AND c.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
               LIMIT 1""",
            (player_id, coach_id),
        ).fetchone()
        if drow:
            if cur_t == "nfl_player":
                return {"subject_type": "nfl_player", "subject_id": player_id, "predicate": "PLAYED_UNDER",
                        "object_type": "coach", "object_id": coach_id,
                        "season_start": drow["season"], "season_end": drow["season"]}
            return {"subject_type": "coach", "subject_id": coach_id, "predicate": "COACHED_PLAYER",
                    "object_type": "nfl_player", "object_id": player_id,
                    "season_start": drow["season"], "season_end": drow["season"]}
    return None
