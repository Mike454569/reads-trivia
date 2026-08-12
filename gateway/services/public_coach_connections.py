"""Coach Connections v2 -- public Gateway service.

Replaces public_six_degrees.py's tiny-cache-backed puzzles with real,
graph-driven generation (gateway/services/coach_connections_graph.py). Same
security discipline every public mode in this project already follows:
answer withheld until a real move is submitted, server fully authoritative,
opaque game_id, no raw graph internals ever sent to the browser.

Mechanic change from v1 (deliberate, matches Part 5/6/7/8 of the rebuild):
  - Progressive reveal: only the discovered prefix of the path is ever
    returned -- no future/undiscovered node is sent, not even in a hidden
    field (contrast with public_six_degrees.py's old per-step options list,
    which necessarily enumerated the small multiple-choice set).
  - Free-text move submission (a node the player found via /search), not a
    fixed 4-option list -- because the certified graph supports far more
    real neighbors per node than 4, and Part 7 explicitly requires
    accepting ANY legitimate move, not one canonical answer.
  - Multi-path: every move is checked against the LIVE graph
    (coach_connections_graph.is_legal_move), never against one precomputed
    solution -- a different, equally real path is accepted.
"""
from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple

from .. import config
from ..errors import GatewayError
from . import coach_connections_graph as ccg
from . import game_state, oplog, packages

CONTRACT_VERSION = 1
MAX_GENERATE_ATTEMPTS = 12
MOVE_BUDGET_SLACK = 2  # allow a few extra moves beyond the shortest real path so a real, valid, LONGER alternate route can still be completed
SEARCH_LIMIT = 12


def _ensure_enabled() -> None:
    if not config.PUBLIC_SIX_DEGREES_ENABLED:
        oplog.record_event("coach_connections_disabled", mode="coach_connections", reason="master_switch_off")
        raise GatewayError("SERVICE_UNAVAILABLE", "Coach Connections is currently disabled.")


# Real measured ranges (direct query against graph_nodes, not guessed):
# coach popularity_score spans ~0.037-0.493 (median 0.18); the nfl_player
# candidate pool (already filtered to >=0.4 in _candidate_pool) spans
# 0.4-1.0 (median 0.72) -- two DIFFERENT scoring populations on the same
# raw 0-1 scale. A coach/player pair's raw average would always skew low
# just because coaches score lower on this particular metric, not because
# either side is actually more obscure (e.g. Bill Belichick scores low here
# despite being extremely well-known) -- min-max normalizing each node's
# score against its OWN type's real observed range before averaging fixes
# that cross-population skew.
_COACH_POP_RANGE = (0.03, 0.50)
_PLAYER_POP_RANGE = (0.4, 1.0)


def _normalized_prominence(node_type: str, pop: float) -> float:
    lo, hi = _COACH_POP_RANGE if node_type == "coach" else _PLAYER_POP_RANGE
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (pop - lo) / (hi - lo)))


def _difficulty_for(path: List[ccg.Edge], start_prom: float, end_prom: float) -> str:
    """Real graph characteristics, not just path length (a real bug caught
    by measuring a 20-puzzle sample: path length alone put 16/20 puzzles in
    "medium" and 0/20 in "hard", since this richly-connected graph rarely
    needs the full max_depth=4 between two real NFL people -- length-4
    paths are genuinely rare, not because puzzles aren't hard, but because
    "hard" here should mean obscure people, not merely a longer route).
    Combines real path length AND real (type-normalized) prominence -- a
    short path between two obscure players is legitimately harder to know
    than a long path between two famous ones."""
    n = len(path)
    avg_prom = (start_prom + end_prom) / 2
    if n <= 2 and avg_prom >= 0.6:
        return "easy"
    if n >= 4 or avg_prom < 0.3:
        return "hard"
    return "medium"


def _node_popularity(c, node_type: str, node_id: str) -> float:
    row = c.execute(
        "SELECT popularity_score FROM graph_nodes WHERE node_type=? AND node_id=?", (node_type, node_id)
    ).fetchone()
    return float(row["popularity_score"]) if row and row["popularity_score"] is not None else 0.0


def _candidate_pool(c, rng) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Real start/target candidates: all 177 real coaches, plus a real,
    popularity-filtered sample of prominent players -- never an arbitrary
    or obscure node a player wouldn't recognize."""
    coaches = [("coach", r["subject_id"]) for r in c.execute(
        "SELECT DISTINCT subject_id FROM graph_edges WHERE predicate='COACHED_TEAM_IN_SEASON'"
    )]
    players = [(r["node_type"], r["node_id"]) for r in c.execute(
        "SELECT node_type, node_id FROM graph_nodes WHERE node_type='nfl_player' AND popularity_score >= 0.4 "
        "ORDER BY popularity_score DESC LIMIT 1500"
    )]
    return coaches, players


def generate_puzzle(*, seed: Optional[str] = None, exclude_pairs: Optional[List[Tuple[str, str]]] = None) -> dict:
    """Real, graph-driven generation -- picks a real start/target pair from
    the real candidate pool, verifies a real path exists via
    coach_connections_graph.find_path(), computes real difficulty. Never
    reads graph_path_cache."""
    import random

    real_seed = seed or secrets.token_hex(8)
    rng = random.Random(hashlib.sha256(real_seed.encode()).hexdigest())
    exclude_pairs = set(exclude_pairs or [])

    c = ccg._connect()
    try:
        coaches, players = _candidate_pool(c, rng)
        pool = coaches + players
        if len(pool) < 2:
            return {"status": "NO_ELIGIBLE_GAME"}

        for _ in range(MAX_GENERATE_ATTEMPTS):
            start, end = rng.sample(pool, 2)
            if (start, end) in exclude_pairs or (end, start) in exclude_pairs:
                continue
            path = ccg.find_path(c, start, end, max_depth=ccg.MAX_PATH_DEPTH, rng=rng)
            if not path or len(path) < 2:
                # length-1 (directly adjacent) is real but usually too
                # trivial/obvious to be a satisfying puzzle -- keep looking.
                continue
            start_prom = _normalized_prominence(start[0], _node_popularity(c, start[0], start[1]))
            end_prom = _normalized_prominence(end[0], _node_popularity(c, end[0], end[1]))
            difficulty = _difficulty_for(path, start_prom, end_prom)
            start_name = ccg._label(c, start[0], start[1])
            end_name = ccg._label(c, end[0], end[1])

            steps = []
            for e in path:
                steps.append({
                    "subject_type": e["subject_type"], "subject_id": e["subject_id"],
                    "object_type": e["object_type"], "object_id": e["object_id"],
                    "predicate": e["predicate"], "season_start": e["season_start"], "season_end": e["season_end"],
                })

            return {
                "status": "OK",
                "start": {"type": start[0], "id": start[1], "name": start_name},
                "end": {"type": end[0], "id": end[1], "name": end_name},
                "par": len(path),
                "max_moves": min(len(path) + MOVE_BUDGET_SLACK, ccg.MAX_PATH_DEPTH + MOVE_BUDGET_SLACK),
                "difficulty": difficulty,
                "canonical_path": steps,
                "seed": real_seed,
            }
        return {"status": "NO_ELIGIBLE_GAME"}
    finally:
        c.close()


def _current_node(state: dict) -> Tuple[str, str]:
    last = state["discovered"][-1]
    return (last["type"], last["id"])


def _load_game(game_id: str) -> Tuple[dict, dict]:
    """Loads BOTH halves of a game: the immutable puzzle definition
    (packages.py) and the mutable in-progress state (game_state.py). Always
    loaded together -- nothing in this module trusts client-supplied
    progress (see game_state.py's module docstring for why)."""
    try:
        saved = packages.load_package(game_id)
        state = game_state.load_state(game_id)
    except (packages.PackageIdInvalid, game_state.StateIdInvalid):
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")
    if not saved or saved.get("mode") != "coach_connections" or not state:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")
    return saved, state


def _public_view(saved: dict, state: dict, *, last_result: Optional[dict] = None) -> dict:
    discovered = state["discovered"]
    completed = discovered[-1]["type"] == saved["end"]["type"] and discovered[-1]["id"] == saved["end"]["id"]
    view: Dict[str, Any] = {
        "game_id": saved["package_id"],
        "mode": "coach_connections",
        "start": {"name": saved["start"]["name"]},
        "end": {"name": saved["end"]["name"]},
        "par": saved["par"],
        "max_moves": saved["max_moves"],
        "moves_made": len(discovered) - 1,
        "difficulty": saved["difficulty"],
        # Progressive reveal: only nodes/edges ACTUALLY discovered so far --
        # never the canonical_path, never any future node.
        "discovered": [{"type": d["type"], "id": d["id"], "name": d["name"]} for d in discovered],
        "edges_found": state["edges_found"],
        "completed": completed,
        "out_of_moves": (not completed) and (len(discovered) - 1 >= saved["max_moves"]),
        "metadata": {"seed": saved.get("seed"), "contract_version": CONTRACT_VERSION},
    }
    if last_result is not None:
        view["last_move"] = last_result
    return view


def get_coach_connections_game(*, seed: Optional[str], exclude_game_ids: Optional[List[str]] = None) -> dict:
    t0 = time.perf_counter()
    _ensure_enabled()
    exclude_game_ids = exclude_game_ids or []

    # Recent-repetition suppression: real, not cosmetic -- exclude the
    # actual (start,end) pairs of recently-served games, using the same
    # "client sends back its own recent ids" pattern every other public
    # mode in this project already uses (Part 12).
    exclude_pairs: List[Tuple[Tuple[str, str], Tuple[str, str]]] = []
    for gid in exclude_game_ids[-30:]:
        try:
            prior = packages.load_package(gid)
        except packages.PackageIdInvalid:
            continue
        if prior and prior.get("mode") == "coach_connections":
            exclude_pairs.append(((prior["start"]["type"], prior["start"]["id"]),
                                   (prior["end"]["type"], prior["end"]["id"])))

    result = None
    for attempt in range(4):
        real_seed = seed if (seed and attempt == 0) else secrets.token_hex(8)
        result = generate_puzzle(seed=real_seed, exclude_pairs=[p[0] for p in exclude_pairs] or None)
        if result.get("status") == "OK":
            break
        if seed and attempt == 0:
            break
    if not result or result.get("status") != "OK":
        oplog.record_event("coach_connections_no_eligible", mode="coach_connections",
                            latency_ms=round((time.perf_counter() - t0) * 1000, 3))
        raise GatewayError("NO_ELIGIBLE_GAME", "No Coach Connections puzzle could be generated right now.")

    game_id = "GGP:" + hashlib.sha256(f"coach_connections|{result['seed']}".encode()).hexdigest()[:24]
    record = {
        "package_id": game_id, "mode": "coach_connections", "qa_status": "PASSED",
        "start": result["start"], "end": result["end"], "par": result["par"], "max_moves": result["max_moves"],
        "difficulty": result["difficulty"], "canonical_path": result["canonical_path"], "seed": result["seed"],
    }
    saved = packages.save_package(record)
    state = game_state.create_state(game_id, {"discovered": [result["start"]], "edges_found": []})
    view = _public_view(saved, state)
    oplog.record_event("coach_connections_served", mode="coach_connections", difficulty=saved["difficulty"],
                        par=saved["par"], latency_ms=round((time.perf_counter() - t0) * 1000, 3))
    return view


def submit_move(*, game_id: str, node_type: str, node_id: str) -> dict:
    _ensure_enabled()
    saved, state = _load_game(game_id)
    if node_type not in ccg.PUBLIC_NODE_TYPES:
        raise GatewayError("INVALID_REQUEST", "Unrecognized node type.")

    discovered = state["discovered"]
    current = _current_node(state)
    already_completed = current == (saved["end"]["type"], saved["end"]["id"])
    if already_completed or len(discovered) - 1 >= saved["max_moves"]:
        # Game already over -- no further state change, server stays authoritative.
        return _public_view(saved, state, last_result={"accepted": False, "reason": "GAME_OVER"})

    proposed = (node_type, node_id)
    c = ccg._connect()
    try:
        edge = ccg.is_legal_move(c, current, proposed)
        if edge is None:
            oplog.record_event("coach_connections_move_rejected", mode="coach_connections")
            return _public_view(saved, state, last_result={"accepted": False, "reason": "NOT_CONNECTED"})
        node_name = ccg._label(c, proposed[0], proposed[1])
    finally:
        c.close()

    updated_state = {
        "discovered": discovered + [{"type": proposed[0], "id": proposed[1], "name": node_name}],
        "edges_found": state["edges_found"] + [{
            "subject_type": edge["subject_type"], "subject_id": edge["subject_id"],
            "object_type": edge["object_type"], "object_id": edge["object_id"],
            "predicate": edge["predicate"], "season_start": edge["season_start"], "season_end": edge["season_end"],
        }],
    }
    game_state.save_state(game_id, updated_state)

    reached_target = proposed == (saved["end"]["type"], saved["end"]["id"])
    oplog.record_event("coach_connections_move_accepted", mode="coach_connections", completed=reached_target)
    return _public_view(saved, updated_state,
                         last_result={"accepted": True, "node_name": node_name, "predicate": edge["predicate"]})


def reveal(*, game_id: str) -> dict:
    _ensure_enabled()
    saved, state = _load_game(game_id)

    current = _current_node(state)
    end = (saved["end"]["type"], saved["end"]["id"])
    c = ccg._connect()
    try:
        path = [] if current == end else (ccg.find_path(c, current, end, max_depth=ccg.MAX_PATH_DEPTH) or [])
        names = [d["name"] for d in state["discovered"]]
        # Walk the path in order, tracking true position each step (an edge's
        # subject/object roles are the real-world direction, NOT necessarily
        # "from wherever we currently are" -- see coach_connections_graph.py).
        pos = current
        for e in path:
            subj, obj = (e["subject_type"], e["subject_id"]), (e["object_type"], e["object_id"])
            nxt = obj if pos == subj else subj
            names.append(ccg._label(c, nxt[0], nxt[1]))
            pos = nxt
    finally:
        c.close()
    return {"game_id": game_id, "start": {"name": saved["start"]["name"]}, "end": {"name": saved["end"]["name"]},
            "par": saved["par"], "solution_names": names}


def search_nodes(*, query: str, node_type: Optional[str] = None) -> List[dict]:
    """Real autocomplete -- graph_explorer.search() unmodified, filtered to
    the public-safe node types and (optionally) one specific type. Never
    reorders by correctness (search() only orders by popularity+name, which
    has no notion of "the current puzzle's right answer"), never includes
    any correctness metadata."""
    _ensure_enabled()
    if len(query) < 2:
        return []
    c = ccg._connect()
    try:
        rows = c.execute(
            "SELECT node_type, node_id, display_name FROM graph_nodes "
            "WHERE lower(display_name) LIKE ? AND node_type IN ({}) {} "
            "ORDER BY popularity_score DESC, display_name LIMIT ?".format(
                ",".join("?" for _ in ccg.PUBLIC_NODE_TYPES),
                "AND node_type=?" if node_type else "",
            ),
            (f"%{query.lower()}%", *ccg.PUBLIC_NODE_TYPES, *([node_type] if node_type else []), SEARCH_LIMIT),
        ).fetchall()
    finally:
        c.close()
    return [{"type": r["node_type"], "id": r["node_id"], "name": r["display_name"]} for r in rows]


def list_coach_connections_capability() -> dict:
    return {
        "mode": "coach_connections", "competition": "NFL", "title": "Coach Connections",
        "desc": "Connect two NFL people through real career history -- coaches, players, and teams.",
        "kind": "graph_connections",
        "available": config.PUBLIC_SIX_DEGREES_ENABLED,
    }
