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


# --- Phase 3 measurement corrections: generation_attempts/successful_ -----
# --- generations/unique_questions_exercised/eligible_pool_size/test_sample_rate
#
# Naming correction (owner-flagged after the Phase 3 report): the field was
# originally called "coverage_rate", which was misleading -- it does not
# measure data coverage or eligibility, only what fraction of the eligible
# pool ONE certification run happened to sample. Renamed to
# `test_sample_rate` everywhere; see health_probe.run_probe()'s own
# docstring for the full three-way distinction (test sampling vs.
# eligibility vs. coverage-regression drift).

def test_tier2_runs_100_executions_even_when_pool_is_smaller_than_100():
    """Real regression test for the Phase 2 -> Phase 3 correction: a pool of
    24 real Super Bowls resolving to a team identity must still complete
    100 real generation executions (by cycling through the 24 real,
    already-verified candidates) -- never truncate rounds_run to the pool
    size, and never fabricate a 25th candidate to reach 100."""
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_SUPER_BOWL", "WON_CHAMPIONSHIP")]
    try:
        result = health_probe.run_tier2_certification(
            c, "TEST_SUPER_BOWL_TIER2", "guess", "NFL_SUPER_BOWL", "WON_CHAMPIONSHIP", cap,
        )
        checks = result["checks"]
        assert result["passed"] is True, result
        assert checks["generation_attempts"] == health_probe.TIER2_MIN_ROUNDS == 100
        assert checks["successful_generations"] == 100
        assert checks["eligible_pool_size"] == 60
        assert checks["unique_questions_exercised"] == 24  # the real, honest ceiling -- never padded
        assert checks["test_sample_rate"] == pytest.approx(24 / 60)
        assert "coverage_rate" not in checks  # renamed, never left as a stale alias
    finally:
        _cleanup(c, "TEST_SUPER_BOWL_TIER2")
        c.close()


def test_tier2_reports_full_sampling_when_pool_exceeds_100():
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_DRAFT", "DRAFTED_BY")]
    try:
        result = health_probe.run_tier2_certification(
            c, "TEST_DRAFT_TIER2", "guess", "NFL_DRAFT", "DRAFTED_BY", cap,
        )
        checks = result["checks"]
        assert result["passed"] is True, result
        assert checks["generation_attempts"] == checks["successful_generations"] == 100
        assert checks["unique_questions_exercised"] == 100  # pool is large -- no repeats needed
        assert checks["eligible_pool_size"] > 100
        assert 0 < checks["test_sample_rate"] < 1
    finally:
        _cleanup(c, "TEST_DRAFT_TIER2")
        c.close()


def test_tier2_runtime_health_is_separate_from_low_test_sample_rate():
    """A capability can be operationally healthy (100/100 executions
    succeed, zero leakage, correct answer evaluation) while still having a
    real, low test_sample_rate (a large eligible pool relative to 100
    sampled executions) -- test sampling depth is never treated as a
    pass/fail runtime-health signal."""
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_SUPER_BOWL", "WON_CHAMPIONSHIP")]
    try:
        result = health_probe.run_tier2_certification(
            c, "TEST_SUPER_BOWL_HEALTH", "guess", "NFL_SUPER_BOWL", "WON_CHAMPIONSHIP", cap,
        )
        assert result["passed"] is True
        assert result["checks"]["test_sample_rate"] < 0.5  # real, low sampling fraction for this run
        assert result["checks"]["leakage"]["leaks_found"] == 0
        assert result["checks"]["answer_evaluation"]["checked"] is True
    finally:
        _cleanup(c, "TEST_SUPER_BOWL_HEALTH")
        c.close()


def test_tier2_fails_closed_on_a_genuinely_empty_pool():
    """Distinguishes a healthy-but-low-coverage capability from a genuinely
    broken one: zero eligible candidates means zero successful generations,
    which must fail the runtime-health check even though the code path
    doesn't crash."""
    from tools.director_v02 import health_probe

    c = engine_bootstrap.connect()
    empty_cap = {
        "adapter": type("FakeAdapter", (), {
            "__name__": "tools.director_v02.catalog",  # any real, importable module
        })(),
    }

    import types
    fake_module = types.ModuleType("tools.director_v02.catalog")

    def fake_generate_fn(*args, **kwargs):
        return {"funnel": {"considered": 0}, "questions": []}

    try:
        import tools.director_v02.registry as registry_mod
        orig = registry_mod._generate_guess_package
        registry_mod._generate_guess_package = fake_generate_fn
        try:
            result = health_probe.run_probe(
                "TEST_EMPTY_POOL", "guess", "FAKE_DOMAIN", "FAKE_PREDICATE", empty_cap,
                tier="TIER2", seed_prefix="test-empty",
            )
        finally:
            registry_mod._generate_guess_package = orig
        assert result["passed"] is False
        assert result["checks"]["eligible_pool_size"] == 0
        assert result["checks"]["successful_generations"] == 0
        assert "0/100" in result["failure_reason"]
    finally:
        c.close()


def test_tier1_still_uses_single_batched_call_not_100_executions():
    """Tier-1 is unaffected by the Tier-2 measurement correction -- it stays
    a cheap, single batched call for TIER1_MIN_ROUNDS rounds."""
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_DRAFT", "DRAFTED_BY")]
    try:
        result = health_probe.get_cached_tier1(c, "TEST_TIER1_UNCHANGED", "guess", "NFL_DRAFT", "DRAFTED_BY", cap, force=True)
        assert result["checks"]["generation_attempts"] == health_probe.TIER1_MIN_ROUNDS == 5
        assert result["rounds_run"] == 5
    finally:
        _cleanup(c, "TEST_TIER1_UNCHANGED")
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
