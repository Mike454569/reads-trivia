"""Phase 2 -- Tier-1/Tier-2 health probe tests.

Real, found-live bug this file guards against: player_from_clues.py's own
funnel dict uses "attempted" where game_director_v01.py's funnel uses
"considered" for the same real concept -- reading the wrong key silently
produced a false-negative probe result (5 real puzzles generated, zero
leaks, reported as failed). These tests exercise BOTH real mechanics, not
just the "guess" shape, specifically to catch this class of bug again.
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


def _cleanup(c, capability_id: str) -> None:
    c.execute("DELETE FROM capability_health_probes WHERE capability_id=?", (capability_id,))
    c.commit()


def test_tier1_probe_passes_for_real_guess_mechanic_capability():
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_DRAFT", "DRAFTED_BY")]
    try:
        result = health_probe.get_cached_tier1(c, "TEST_NFL_DRAFT__DRAFTED_BY", "guess", "NFL_DRAFT", "DRAFTED_BY", cap, force=True)
        assert result["passed"] is True
        assert result["checks"]["importable"] is True
        assert result["checks"]["leakage"]["leaks_found"] == 0
        assert result["checks"]["answer_evaluation"]["checked"] is True
        assert result["rounds_run"] == health_probe.TIER1_MIN_ROUNDS
    finally:
        _cleanup(c, "TEST_NFL_DRAFT__DRAFTED_BY")
        c.close()


def test_tier1_probe_passes_for_real_clue_reveal_mechanic_capability():
    """The exact regression test for the found-live 'attempted' vs
    'considered' bug -- must never again silently report a real, working
    mechanic as failed."""
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[("identify_player_from_clues", "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES")]
    try:
        result = health_probe.get_cached_tier1(
            c, "TEST_NFL_PLAYER_IDENTITY__IDENTIFY_FROM_CLUES", "identify_player_from_clues",
            "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES", cap, force=True,
        )
        assert result["passed"] is True, result
        assert result["checks"]["considered"] > 0
        assert result["checks"]["leakage"]["leaks_found"] == 0
    finally:
        _cleanup(c, "TEST_NFL_PLAYER_IDENTITY__IDENTIFY_FROM_CLUES")
        c.close()


def test_tier1_probe_is_cached_within_ttl():
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_DRAFT", "DRAFTED_BY")]
    try:
        first = health_probe.get_cached_tier1(c, "TEST_CACHE_CAP", "guess", "NFL_DRAFT", "DRAFTED_BY", cap, force=True)
        assert first["cached"] is False
        second = health_probe.get_cached_tier1(c, "TEST_CACHE_CAP", "guess", "NFL_DRAFT", "DRAFTED_BY", cap)
        assert second["cached"] is True
    finally:
        _cleanup(c, "TEST_CACHE_CAP")
        c.close()


def test_tier1_probe_fails_closed_on_unimportable_adapter():
    from tools.director_v02 import health_probe

    c = engine_bootstrap.connect()
    fake_cap = {"adapter": type("FakeModule", (), {"__name__": "not.a.real.module.path"})()}
    try:
        result = health_probe.run_probe(
            "TEST_FAKE_CAP", "guess", "FAKE_DOMAIN", "FAKE_PREDICATE", fake_cap, tier="TIER1", seed_prefix="test",
        )
        assert result["passed"] is False
        assert "not importable" in result["failure_reason"]
    finally:
        c.close()


def test_coverage_regression_needs_at_least_two_tier2_runs():
    from tools.director_v02 import health_probe

    c = engine_bootstrap.connect()
    try:
        result = health_probe.check_coverage_regression(c, "NOT_A_REAL_CAPABILITY_WITH_NO_HISTORY")
        assert result["regression_detected"] is False
        assert "insufficient history" in result["reason"]
    finally:
        c.close()


def test_coverage_regression_detects_a_real_drop():
    import datetime as _dt
    import json as _json

    from tools.director_v02 import health_probe

    c = engine_bootstrap.connect()
    cap_id = "TEST_REGRESSION_CAP"
    try:
        now = _dt.datetime.now(_dt.timezone.utc)
        older = (now - _dt.timedelta(hours=1)).isoformat()
        newer = now.isoformat()
        c.execute(
            "INSERT INTO capability_health_probes(capability_id, tier, passed, checks_json, rounds_run, probed_at) "
            "VALUES (?, 'TIER2', 1, ?, 100, ?)",
            (cap_id, _json.dumps({"considered": 1000}), older),
        )
        c.execute(
            "INSERT INTO capability_health_probes(capability_id, tier, passed, checks_json, rounds_run, probed_at) "
            "VALUES (?, 'TIER2', 1, ?, 100, ?)",
            (cap_id, _json.dumps({"considered": 400}), newer),  # 60% drop
        )
        c.commit()
        result = health_probe.check_coverage_regression(c, cap_id)
        assert result["regression_detected"] is True
        assert result["drop_fraction"] > health_probe.COVERAGE_REGRESSION_THRESHOLD
    finally:
        c.execute("DELETE FROM capability_health_probes WHERE capability_id=?", (cap_id,))
        c.commit()
        c.close()
