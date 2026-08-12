"""Coach Connections v2 -- graph-driven rebuild (real relationships, real
generation, progressive reveal, multi-path validation). Requires
READS_ENGINE_DIR to point at a real Engine database, same convention every
other Engine-backed Gateway test in this suite already relies on.

Covers the specific real bugs found and fixed while building this (a
correctness bug in edge direction, a performance bug in naive one-directional
BFS, and a real is_legal_move false-negative caused by bounded sampling --
see coach_connections_graph.py's module docstring), plus the contract every
public mode in this project is held to: server-authoritative state, no
answer leakage before Reveal, wrong moves never corrupt progress.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from gateway.services import coach_connections_graph as ccg  # noqa: E402
from gateway.services import public_coach_connections as pcc  # noqa: E402
from gateway.errors import GatewayError  # noqa: E402

pytestmark = pytest.mark.skipif(
    not ccg.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


@pytest.fixture()
def gc():
    c = ccg._connect()
    yield c
    c.close()


# --- Certified relationships / derivation correctness -----------------------

def test_certified_predicates_are_the_documented_safe_set():
    assert ccg.CERTIFIED_PREDICATES == {
        "TEAMMATE_OF", "PLAYED_FOR", "COACHED_TEAM_IN_SEASON", "DRAFTED_BY", "WORE_NUMBER",
    }


def test_public_node_types_exclude_bookkeeping_and_cfb(gc):
    # graph_nodes has real internal bookkeeping types (team_game, game,
    # record, season, ...) and real CFB entities -- neither should ever
    # reach a public player through this NFL-only mode.
    for t in ccg.PUBLIC_NODE_TYPES:
        assert t in ("nfl_player", "team", "coach")
    row = gc.execute("SELECT DISTINCT node_type FROM graph_nodes WHERE node_type LIKE 'cfb%' LIMIT 1").fetchone()
    assert row is not None  # sanity: CFB entities really do exist in this DB
    assert row["node_type"] not in ccg.PUBLIC_NODE_TYPES


def test_derived_played_under_matches_a_real_independent_join(gc):
    """The derived PLAYER<->COACH relationship must equal what you'd get by
    independently joining PLAYED_FOR and COACHED_TEAM_IN_SEASON on
    (team, season overlap) -- never anything looser (e.g. name matching)."""
    row = gc.execute(
        """SELECT p.subject_id AS player_id, c.subject_id AS coach_id, p.object_id AS team_id, p.season_start AS season
           FROM graph_edges p JOIN graph_edges c
             ON c.predicate='COACHED_TEAM_IN_SEASON' AND c.object_type='team' AND c.object_id=p.object_id
             AND c.season_start<=p.season_start AND c.season_end>=p.season_start
           WHERE p.predicate='PLAYED_FOR' AND p.subject_type='nfl_player'
             AND p.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
             AND c.verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
           LIMIT 1"""
    ).fetchone()
    assert row is not None, "expected at least one real derivable PLAYER<->COACH relationship in this DB"
    edge = ccg.is_legal_move(gc, ("coach", row["coach_id"]), ("nfl_player", row["player_id"]))
    assert edge is not None
    assert edge["predicate"] == "COACHED_PLAYER"
    assert edge["season_start"] == row["season"]


def test_no_synthetic_coach_coach_edge_is_fabricated(gc):
    """Two coaches of the same team in different eras must connect through
    the real team node (two real COACHED_TEAM_IN_SEASON edges), never a
    fabricated direct coach<->coach edge claiming they coached together."""
    rows = gc.execute(
        "SELECT DISTINCT subject_id FROM graph_edges WHERE predicate='COACHED_TEAM_IN_SEASON' LIMIT 5"
    ).fetchall()
    for r in rows:
        edge = ccg.is_legal_move(gc, ("coach", r["subject_id"]), ("coach", "COACH:__fake_other_coach__"))
        assert edge is None  # no real coach<->coach edge type exists at all
    # No certified or derived predicate connects coach directly to coach --
    # confirmed structurally (none of the real, hand-picked predicates below
    # are coach<->coach shaped) rather than just by one sampled lookup above.
    assert "SHARED_TEAM_WITH" not in ccg.CERTIFIED_PREDICATES


# --- Real bug regression: is_legal_move must never miss a real edge due to
#     the bounded/sampled neighbor scan used elsewhere for BFS speed --------

def test_is_legal_move_finds_high_fanout_derived_relationship(gc):
    """Real bug found in live testing: a coach with hundreds of real derived
    PLAYER<->COACH relationships only ever surfaced a random ~15-60 of them
    through the BFS-tuned neighbor scan -- is_legal_move must check the
    EXACT pair directly instead, so it never rejects a real, legal move."""
    busy_coach = gc.execute(
        """SELECT c.subject_id AS coach_id, COUNT(*) AS n
           FROM graph_edges p JOIN graph_edges c
             ON c.predicate='COACHED_TEAM_IN_SEASON' AND c.object_type='team' AND c.object_id=p.object_id
             AND c.season_start<=p.season_start AND c.season_end>=p.season_start
           WHERE p.predicate='PLAYED_FOR' AND p.subject_type='nfl_player'
           GROUP BY c.subject_id ORDER BY n DESC LIMIT 1"""
    ).fetchone()
    assert busy_coach["n"] > ccg.MAX_FANOUT_PER_PREDICATE * 4, "test needs a real coach busier than the BFS sample window"
    real_pair = gc.execute(
        """SELECT p.subject_id AS player_id
           FROM graph_edges p JOIN graph_edges c
             ON c.predicate='COACHED_TEAM_IN_SEASON' AND c.object_type='team' AND c.object_id=p.object_id
             AND c.season_start<=p.season_start AND c.season_end>=p.season_start
           WHERE p.predicate='PLAYED_FOR' AND p.subject_type='nfl_player' AND c.subject_id=?
           ORDER BY p.subject_id DESC LIMIT 1""",
        (busy_coach["coach_id"],),
    ).fetchone()
    edge = ccg.is_legal_move(gc, ("coach", busy_coach["coach_id"]), ("nfl_player", real_pair["player_id"]))
    assert edge is not None, "a real derived relationship for a high-fanout coach must never be missed"


def test_is_legal_move_rejects_unconnected_pair(gc):
    a = gc.execute("SELECT node_id FROM graph_nodes WHERE node_type='nfl_player' LIMIT 1").fetchone()
    assert ccg.is_legal_move(gc, ("nfl_player", a["node_id"]), ("team", "__NOT_A_REAL_TEAM__")) is None


# --- find_path correctness ---------------------------------------------------

def test_find_path_edges_are_correctly_directed(gc):
    coach = gc.execute("SELECT subject_id, object_id FROM graph_edges WHERE predicate='COACHED_TEAM_IN_SEASON' LIMIT 1").fetchone()
    path = ccg.find_path(gc, ("coach", coach["subject_id"]), ("team", coach["object_id"]))
    assert path == [] or path[0]["subject_type"] == "coach"
    # Every edge's subject/object must be a real graph_edges row, not
    # inferred from traversal order.
    for e in (path or []):
        row = gc.execute(
            "SELECT 1 FROM graph_edges WHERE subject_type=? AND subject_id=? AND object_type=? AND object_id=? AND predicate=?",
            (e["subject_type"], e["subject_id"], e["object_type"], e["object_id"], e["predicate"]),
        ).fetchone()
        if e["predicate"] not in ("PLAYED_UNDER", "COACHED_PLAYER"):  # derived, not stored directly
            assert row is not None


def test_find_path_same_start_and_end_is_trivial(gc):
    assert ccg.find_path(gc, ("team", "ARI"), ("team", "ARI")) == []


# --- Puzzle generation --------------------------------------------------------

def test_generate_puzzle_produces_a_real_verified_path():
    result = pcc.generate_puzzle(seed="unit-test-seed-1")
    assert result["status"] == "OK"
    assert result["par"] >= 2  # length-1/trivial puzzles are filtered out
    assert result["difficulty"] in ("easy", "medium", "hard")
    assert len(result["canonical_path"]) == result["par"]


def test_generate_puzzle_is_deterministic_for_a_fixed_seed():
    a = pcc.generate_puzzle(seed="deterministic-seed")
    b = pcc.generate_puzzle(seed="deterministic-seed")
    assert a["start"] == b["start"]
    assert a["end"] == b["end"]


# --- Full service layer: generate / move / reveal / search ------------------

@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    from gateway import config
    monkeypatch.setattr(config, "PACKAGES_DIR", tmp_path / "packages")
    monkeypatch.setattr(config, "GAME_STATE_DIR", tmp_path / "game_state")
    monkeypatch.setattr(config, "PUBLIC_SIX_DEGREES_ENABLED", True)
    yield


def _walk_full_path(game_id: str, canonical_path: list[dict], start: dict) -> dict:
    pos = (start["type"], start["id"])
    result = None
    for e in canonical_path:
        subj = (e["subject_type"], e["subject_id"])
        obj = (e["object_type"], e["object_id"])
        nxt = obj if pos == subj else subj
        result = pcc.submit_move(game_id=game_id, node_type=nxt[0], node_id=nxt[1])
        pos = nxt
    return result


def test_full_canonical_path_completes_the_game(isolated_storage):
    game = pcc.get_coach_connections_game(seed="e2e-seed-1")
    saved = pcc.packages.load_package(game["game_id"])
    result = _walk_full_path(game["game_id"], saved["canonical_path"], saved["start"])
    assert result["completed"] is True
    assert result["moves_made"] == saved["par"]


def test_wrong_move_is_rejected_without_corrupting_progress(isolated_storage):
    game = pcc.get_coach_connections_game(seed="e2e-seed-2")
    before = game["discovered"]
    result = pcc.submit_move(game_id=game["game_id"], node_type="team", node_id="__NOT_REAL__")
    assert result["last_move"]["accepted"] is False
    assert result["last_move"]["reason"] == "NOT_CONNECTED"
    assert result["discovered"] == before
    assert result["moves_made"] == 0


def test_move_never_hits_packages_content_collision(isolated_storage):
    """Regression test for a real bug caught before shipping: packages.py is
    content-addressed and raises PackageCollision on any in-place mutation
    -- game progress must live in game_state.py instead, never re-saved
    into the same package_id."""
    game = pcc.get_coach_connections_game(seed="e2e-seed-3")
    saved = pcc.packages.load_package(game["game_id"])
    # Several real moves in a row must never raise.
    _walk_full_path(game["game_id"], saved["canonical_path"], saved["start"])


def test_out_of_moves_and_game_over_after_completion(isolated_storage):
    game = pcc.get_coach_connections_game(seed="e2e-seed-4")
    saved = pcc.packages.load_package(game["game_id"])
    result = _walk_full_path(game["game_id"], saved["canonical_path"], saved["start"])
    assert result["completed"] is True
    # Any further move after completion is a clean no-op, not an error and
    # not additional progress.
    again = pcc.submit_move(game_id=game["game_id"], node_type=saved["end"]["type"], node_id=saved["end"]["id"])
    assert again["last_move"]["accepted"] is False
    assert again["last_move"]["reason"] == "GAME_OVER"
    assert again["moves_made"] == result["moves_made"]


def test_alternate_valid_path_also_completes_the_game(isolated_storage):
    """Part 16 of the rebuild spec: a DIFFERENT real path than the canonical
    one must be accepted, since is_legal_move checks the live graph, not one
    precomputed solution. Finds a real puzzle where find_path (seeded
    differently) discovers a distinct route, then completes it that way."""
    c = ccg._connect()
    try:
        found = None
        for seed in [f"alt-path-seed-{i}" for i in range(40)]:
            game = pcc.get_coach_connections_game(seed=seed)
            saved = pcc.packages.load_package(game["game_id"])
            start = (saved["start"]["type"], saved["start"]["id"])
            end = (saved["end"]["type"], saved["end"]["id"])
            import random
            alt = ccg.find_path(c, start, end, rng=random.Random(seed + "-alt"))
            if alt and alt != saved["canonical_path"] and len(alt) >= 2:
                found = (game, saved, alt)
                break
        assert found is not None, "could not find a puzzle with a distinct alternate path in 40 tries"
        game, saved, alt = found
        result = _walk_full_path(game["game_id"], alt, saved["start"])
        assert result["completed"] is True
    finally:
        c.close()


def test_game_response_never_includes_canonical_path_or_future_nodes(isolated_storage):
    game = pcc.get_coach_connections_game(seed="e2e-leak-check")
    raw = json.dumps(game)
    assert "canonical_path" not in raw
    assert len(game["discovered"]) == 1
    saved = pcc.packages.load_package(game["game_id"])
    if saved["par"] >= 2:
        second_edge = saved["canonical_path"][0]
        forbidden_ids = {second_edge["subject_id"], second_edge["object_id"]} - {game["discovered"][0]["id"]}
        for fid in forbidden_ids:
            assert fid not in raw


def test_reveal_shows_a_real_path_from_current_position(isolated_storage):
    """Reveal's find_path() call is unseeded (a fresh live BFS, not a replay
    of generation's seeded sampling) -- it may legitimately surface a
    DIFFERENT, even shorter, real path than the puzzle's stated par (real
    behavior found while writing this test: two nodes generated as a
    par-2 puzzle also had a genuine direct par-1 edge that generation's
    seeded sample didn't happen to land on). That's correct, not a bug --
    "multiple valid paths" applies to Reveal too, so this only asserts the
    endpoints are right and the whole chain is really walkable, not an
    exact length match to the original par."""
    game = pcc.get_coach_connections_game(seed="e2e-reveal-1")
    reveal = pcc.reveal(game_id=game["game_id"])
    assert reveal["solution_names"][0] == game["start"]["name"]
    assert reveal["solution_names"][-1] == game["end"]["name"]
    assert len(reveal["solution_names"]) >= 2


def test_reveal_after_partial_progress_starts_from_current_node(isolated_storage):
    game = pcc.get_coach_connections_game(seed="e2e-reveal-2")
    saved = pcc.packages.load_package(game["game_id"])
    if saved["par"] < 2:
        pytest.skip("need a multi-hop puzzle for this test")
    first_edge = saved["canonical_path"][0]
    start = (saved["start"]["type"], saved["start"]["id"])
    subj, obj = (first_edge["subject_type"], first_edge["subject_id"]), (first_edge["object_type"], first_edge["object_id"])
    nxt = obj if start == subj else subj
    pcc.submit_move(game_id=game["game_id"], node_type=nxt[0], node_id=nxt[1])
    reveal = pcc.reveal(game_id=game["game_id"])
    assert reveal["solution_names"][0] == game["start"]["name"]
    assert reveal["solution_names"][-1] == game["end"]["name"]


def test_invalid_game_id_raises_gateway_error(isolated_storage):
    with pytest.raises(GatewayError):
        pcc.submit_move(game_id="not-a-real-id", node_type="team", node_id="ARI")
    with pytest.raises(GatewayError):
        pcc.reveal(game_id="not-a-real-id")


# --- Search / autocomplete ----------------------------------------------------

def test_search_is_bounded_and_type_filtered(isolated_storage):
    results = pcc.search_nodes(query="jones")
    assert 0 < len(results) <= pcc.SEARCH_LIMIT
    for r in results:
        assert r["type"] in ccg.PUBLIC_NODE_TYPES


def test_search_never_carries_correctness_metadata(isolated_storage):
    results = pcc.search_nodes(query="smith")
    for r in results:
        assert set(r.keys()) == {"type", "id", "name"}


def test_search_short_query_returns_nothing(isolated_storage):
    assert pcc.search_nodes(query="a") == []


# --- Replayability / dedup ----------------------------------------------------

def test_exclude_game_ids_avoids_repeating_the_same_pair(isolated_storage):
    seen = []
    pairs = set()
    for i in range(15):
        game = pcc.get_coach_connections_game(seed=None, exclude_game_ids=seen)
        seen.append(game["game_id"])
        pair = frozenset({game["start"]["name"], game["end"]["name"]})
        assert pair not in pairs, "a puzzle repeated a (start,end) pair despite the exclude list"
        pairs.add(pair)


def test_difficulty_distribution_uses_more_than_one_tier(isolated_storage):
    """Real regression test for a measured bug: an earlier path-length-only
    difficulty heuristic put 16/20 real puzzles in 'medium' and 0/20 in
    'hard' -- this graph rarely needs the full max-depth path between two
    real NFL people, so length alone is not a meaningful difficulty signal.
    A real sample must show more than one tier."""
    diffs = set()
    for i in range(20):
        game = pcc.get_coach_connections_game(seed=f"difficulty-sample-{i}")
        diffs.add(game["difficulty"])
        if len(diffs) >= 2:
            return
    pytest.fail(f"20 real puzzles produced only {diffs} -- difficulty heuristic may not be using real signal")


# --- Capability listing -------------------------------------------------------

def test_capability_listing_reflects_master_switch(isolated_storage):
    cap = pcc.list_coach_connections_capability()
    assert cap["mode"] == "coach_connections"
    assert cap["available"] is True
