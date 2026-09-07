"""Absolute Final Closeout (Item 5): cross-mode repetition control.

Real gap found: Odd College Out, Spot the Fake Lineup, One School Missing,
Three Clues One Champion/Era Gauntlet, and Franchise Marathon's DEEP_CUT
stage all draw from the SAME real 595-board `_group_board_common` pool (see
registry.py's own comments), but each adapter's `DuplicateGuard` only
dedups WITHIN its own single generation call -- nothing prevented the same
real board (e.g. "1999 St. Louis Rams") from appearing in Odd College Out
and then immediately again in One School Missing for the same player.

Fix: every one of those 5 adapters now emits the SAME `"board:{board_id}"`
entity_key for the same real board (board_id is already globally unique
across all 5 pool kinds -- see _group_board_common.py's own board_id
formats), and gateway/services/public_game.py tracks a small, bounded,
in-memory recency window per client_id (the same getClientId() convention
Pick'em already uses) across EVERY mode a session plays -- the lightest
mechanism that fits this file's existing stateless-request architecture,
with no persistence and no permanent ban (a fixed-size rolling window).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

# The 4 real, non-sequential public modes that share the 595-board pool --
# each one individually retryable via public_game.py's exclude/entity loop.
_SHARED_POOL_MODES = (
    "cfb_odd_college_out_guess", "cfb_spot_the_fake_guess",
    "cfb_one_school_missing_guess", "cfb_three_clues_guess",
)


def test_the_four_shared_pool_adapters_now_emit_the_same_entity_key_format():
    """Direct adapter-level check (not the public API): every one of the 4
    non-sequential adapters built on _group_board_common must produce an
    entity_key of the exact form "board:{board_id}" -- the shared format
    that makes cross-mode recognition possible at all. Franchise Marathon's
    DEEP_CUT stage is checked separately below (it isn't one of these 4
    modules)."""
    import re

    from tools.quiz_export import engine
    from tools.quiz_export.adapters import (
        _group_board_common as gbc,
        cfb_odd_college_out,
        cfb_one_school_missing,
        cfb_spot_the_fake_lineup,
        cfb_three_clues_one_champion,
    )
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    boards = gbc.sb_champion_boards(c) + gbc.current_team_boards(c) + gbc.nfl_team_season_roster_boards(c)
    assert boards

    import random
    rng = random.Random("pytest-entity-key-format")

    for module in (cfb_odd_college_out, cfb_one_school_missing, cfb_spot_the_fake_lineup):
        guard = DuplicateGuard(track_entity=True)
        found_real_entity_key = False
        for board in boards[:40]:
            result = module.evaluate(c, board, rng, guard)
            if isinstance(result, str):
                continue  # a real, expected rejection (DUPLICATE_*, etc.) for this particular board
            record = result if isinstance(result, dict) else None
            if record is None:
                continue
            entity_key = record.get("_audit", {}).get("entity_key")
            if entity_key is None:
                continue
            assert re.match(r"^board:", entity_key), (module.__name__, entity_key)
            found_real_entity_key = True
        assert found_real_entity_key, f"{module.__name__} produced zero real entity_key values across 40 real boards"


def test_three_clues_one_champion_also_uses_the_shared_board_prefix():
    """cfb_three_clues_one_champion.py has a different evaluate() shape
    (era-pool based) from the other 3 -- checked separately via a direct
    package generation instead of calling evaluate() with a hand-picked
    board."""
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as tcoc

    spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "nfl_sb_champion_offense_board_college",
        "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES", "object_type": "team_season",
        "answer_type": "team_season", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, tcoc, request_text="pytest", director_request_id="pytest",
        seed="pytest-three-clues-entity-key", target_count=15, id_start=1,
    )
    assert pkg["questions"], "no real questions generated -- cannot check entity_key format"
    for q in pkg["questions"]:
        entity_key = q["entity_key"]
        assert entity_key.startswith("board:"), entity_key


def test_franchise_marathon_deep_cut_stage_uses_the_same_shared_board_prefix():
    """Franchise Marathon's DEEP_CUT stage draws from the exact same
    curated SB_CHAMPION boards as the 4 modes above -- its entity_key must
    use the identical "board:{board_id}" format so a real overlap (e.g. the
    same 1999 Rams board) is recognized across BOTH Franchise Marathon and
    Odd College Out/One School Missing/etc., not just within one mode."""
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import franchise_marathon as fm

    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_franchise_marathon_stage",
        "relationship_predicate": "FRANCHISE_MARATHON_STAGE", "object_type": "mixed",
        "answer_type": "mixed", "group_size": 4, "filters": {"franchise_name": "Patriots"},
    }
    pkg = v01.generate_package_from_spec(
        spec, fm, request_text="pytest", director_request_id="pytest",
        seed="pytest-fm-deep-cut-entity-key", target_count=8, id_start=1,
    )
    deep_cuts = [q for q in pkg["questions"] if q["question"].startswith("Final boss:")]
    # The Patriots have 6 real Super Bowl titles, so DEEP_CUT must be reachable.
    assert deep_cuts, "no DEEP_CUT stage reached for a real champion franchise"
    for q in deep_cuts:
        assert q["entity_key"] is not None and q["entity_key"].startswith("board:"), q["entity_key"]


def test_a_real_board_id_is_globally_unique_across_all_five_pool_kinds():
    """The whole cross-mode mechanism depends on board_id never colliding
    across the 5 different real sources -- verified directly against the
    live data, not assumed."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc

    c = engine.connect()
    all_boards = (
        gbc.sb_champion_boards(c) + gbc.current_team_boards(c) + gbc.nfl_team_season_roster_boards(c)
        + gbc.draft_class_boards(c) + gbc.honor_group_boards(c)
    )
    ids = [b["board_id"] for b in all_boards]
    assert len(ids) == len(set(ids)), "board_id collided across pool kinds -- the shared entity_key scheme is unsafe"
    assert len(ids) > 500  # real, measured pool size (595 at last count)


def test_recency_window_is_never_leaked_to_the_public_client(client):
    """ANSWER LEAKAGE BOUNDARY (public_game.py's own module docstring):
    entity_key values encode real season/team/board identity (e.g.
    "board:NFL_TEAM_SEASON:2015:NE") -- exposing them to the client would
    leak the correct answer outright for a team/season-guessing mode. The
    cross-mode mechanism must therefore never appear in a JSON response."""
    import json

    r = client.get("/v1/public/game", params={"mode": "cfb_one_school_missing_guess", "client_id": "pytest-leak-check-client"})
    assert r.status_code == 200
    body = r.text
    assert "entity_key" not in body
    assert "board:" not in body
    parsed = json.loads(body)
    assert set(parsed.keys()) <= {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}


def test_a_shared_client_id_avoids_repeating_the_same_real_board_across_two_different_modes(client):
    """The concrete regression this pass fixes: the same client plays Odd
    College Out, then immediately One School Missing (both drawing from the
    same 595-board pool) -- with a shared client_id, the second mode's
    served board should not be the exact one just seen in the first, given
    a pool this size. Uses a fixed, real, reproducible client_id."""
    client_id = "pytest-cross-mode-repeat-check-001"
    r1 = client.get("/v1/public/game", params={"mode": "cfb_odd_college_out_guess", "client_id": client_id, "seed": "pytest-xmr-1"})
    assert r1.status_code == 200

    from gateway.services import packages as packages_mod
    saved1 = packages_mod.load_package(r1.json()["game_id"])
    entity1 = saved1["questions"][0]["entity_key"]

    seen_same_entity = False
    for i in range(10):
        r2 = client.get("/v1/public/game", params={"mode": "cfb_one_school_missing_guess", "client_id": client_id, "seed": f"pytest-xmr-2-{i}"})
        assert r2.status_code == 200
        saved2 = packages_mod.load_package(r2.json()["game_id"])
        entity2 = saved2["questions"][0]["entity_key"]
        if entity2 == entity1:
            seen_same_entity = True
    assert not seen_same_entity, "the exact same real board was served again immediately in a different mode"


def test_recency_window_is_bounded_not_a_permanent_ban(monkeypatch):
    """Explicit requirement: "no permanent bans." The per-client deque has
    a fixed maxlen -- verified directly against the real implementation,
    not just its documented intent."""
    from gateway.services import public_game

    assert isinstance(public_game._RECENT_ENTITY_WINDOW, int) and public_game._RECENT_ENTITY_WINDOW > 0
    dq = public_game._recent_entities_for("pytest-bounded-window-client")
    assert dq.maxlen == public_game._RECENT_ENTITY_WINDOW
    for i in range(public_game._RECENT_ENTITY_WINDOW * 3):
        dq.append(f"board:fake-{i}")
    assert len(dq) == public_game._RECENT_ENTITY_WINDOW
    assert "board:fake-0" not in dq  # the oldest entries fell off -- not an ever-growing ban list


def test_seven_named_modes_played_sequentially_by_one_client_stress_test(client):
    """Item 5's required stress test: cycle a single shared client_id
    through 7 real public modes (the 4 shared-pool modes plus 3 more with
    disjoint data so they can never collide anyway) and report the real,
    measured cross-mode entity overlap rate. Printed for visibility in
    `-s` runs; asserted against a generous real-world bound (a handful of
    coincidental repeats among ~50 draws from a 595-board shared pool is
    expected and fine -- the requirement is "no giant new architecture,"
    not "mathematically impossible collision")."""
    from gateway.app import public_game_limiter
    from gateway.services import packages as packages_mod

    modes_cycle = [
        "cfb_odd_college_out_guess", "cfb_spot_the_fake_guess", "cfb_one_school_missing_guess",
        "cfb_three_clues_guess", "draft_guess", "championship_guess", "cfb_heisman_guess",
    ]
    client_id = "pytest-seven-mode-stress-client"
    entity_history: list[str] = []
    immediate_repeats = 0
    total_shared_pool_draws = 0
    rounds = 12
    for round_idx in range(rounds):
        # This is a real, deliberately-enforced production rate limit
        # (config.PUBLIC_GAME_RATE_LIMIT_MAX, 20/60s) -- reset it between
        # rounds so this stress test can exercise real request VOLUME
        # without either weakening that real protection or silently
        # measuring almost nothing once it kicks in.
        public_game_limiter.reset()
        for mode in modes_cycle:
            r = client.get("/v1/public/game", params={"mode": mode, "client_id": client_id, "seed": f"pytest-7mode-{round_idx}-{mode}"})
            if r.status_code != 200:
                continue
            saved = packages_mod.load_package(r.json()["game_id"])
            entity_key = saved["questions"][0].get("entity_key")
            if entity_key is None or not entity_key.startswith("board:"):
                continue  # draft_guess/championship_guess/cfb_heisman_guess have no shared-pool entity_key
            total_shared_pool_draws += 1
            if entity_history and entity_history[-1] == entity_key:
                immediate_repeats += 1
            entity_history.append(entity_key)
    assert total_shared_pool_draws >= 20, "too few shared-pool draws to measure anything real"
    repeat_rate = immediate_repeats / total_shared_pool_draws
    print(f"\n[cross-mode stress] shared-pool draws={total_shared_pool_draws} "
          f"immediate_repeats={immediate_repeats} rate={repeat_rate:.1%}")
    assert repeat_rate < 0.10, f"immediate cross-mode repeat rate too high: {repeat_rate:.1%}"
