"""Public-readiness punch-list -- POSITION_LINEUP_GRID starvation fix.

Two independent, real defects were found and fixed:

1. Root cause (tools/quiz_export/adapters/lineup.py): certified_college_
   lookup() was rebuilt from two real DB queries on EVERY one of 415
   per-candidate evaluate() calls -- confirmed via cProfile, ~0.4s per
   call from an unindexed `relationships` COUNT alone, ~40s total per
   generation. Fixed by warming the cache exactly once per real generation
   run, from fetch_ordered_candidates() (called once), never from inside
   evaluate() (called once per candidate). Verified below: a real
   generation call for this domain must now complete in well under the
   45s timeout.

2. Defense-in-depth (gateway/services/generation.py): even with the perf
   fix, `Future.result(timeout=...)` still cannot cancel a genuinely stuck
   thread, so POSITION_LINEUP_GRID's admin generation calls are now
   isolated onto their own dedicated lock/executor pair -- a stuck lineup
   call can only ever occupy its OWN slot, never the shared one every
   other admin/Creator mechanic depends on. Verified below by artificially
   forcing a lineup call to hang past a shortened timeout and confirming
   an immediately-following, unrelated generation call is not delayed.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

_LINEUP_COLLEGE_SPEC = {
    "mechanic": "guess", "domain": "NFL_OFFENSE_LINEUP_COLLEGE",
    "relationship_predicate": "TEAM_OF_STARTING_LINEUP_BY_COLLEGE",
    "question_count": 3, "difficulty": "any", "filters": {}, "exclusions": [],
}
_OTHER_SPEC = {
    "mechanic": "guess", "domain": "NFL_DRAFT", "relationship_predicate": "DRAFTED_BY",
    "question_count": 1, "difficulty": "any", "filters": {}, "exclusions": [],
}


def test_lineup_college_generation_completes_well_under_the_timeout():
    """The real, root-cause perf fix. Before the fix this took ~40-43s
    (confirmed by direct measurement); the 45s timeout gave almost no
    margin. A generous 10s ceiling here still leaves 4x headroom below the
    real timeout while being a real, meaningful regression guard."""
    from gateway.services import generation as generation_service

    t0 = time.time()
    result = generation_service.generate(
        request_text=None, spec=_LINEUP_COLLEGE_SPEC, provider="mock",
        puzzle_count=None, difficulty=None, seed="starvation-fix-perf-check",
    )
    elapsed = time.time() - t0
    assert result.get("qa_status") == "PASSED"
    assert len(result.get("questions") or []) == 3
    assert elapsed < 10.0, f"lineup-college generation took {elapsed:.1f}s -- regression in the cache-warming fix"


def test_lineup_college_coverage_unchanged_by_the_cache_fix():
    """Correctness check: the real, measured coverage number must be
    identical to what it was before the fix (68/412, confirmed independently
    in Phase 6) -- the cache must return the same data, just computed once
    instead of 415 times."""
    from tools.quiz_export.adapters import lineup

    c = engine_bootstrap.connect()
    try:
        cov = lineup.lineup_college_coverage(c)
    finally:
        c.close()
    assert cov["total_candidate_team_seasons"] == 412
    assert cov["skill_positions_only_college_coverage"] == 68


def test_stuck_lineup_generation_does_not_starve_other_mechanics(monkeypatch):
    """Defense-in-depth check, independent of the perf fix: artificially
    force a lineup generation call to hang past a shortened timeout, then
    prove an unrelated generation call issued immediately after is NOT
    delayed -- the exact acceptance criterion the punch-list specifies
    ("another mechanic requested immediately afterward still succeeds")."""
    from gateway.services import generation as generation_service
    from gateway import config as gateway_config
    from gateway.errors import GatewayError

    # Real, measured baseline (this environment): a bare NFL_DRAFT generate()
    # call takes ~0.6-0.7s on its own (DB + pipeline work, no mocking) --
    # the timeout/sleep values below are picked with real headroom above
    # that baseline, so this test's own overhead can never masquerade as a
    # starvation failure the way an unrealistically tight timeout would.
    monkeypatch.setattr(gateway_config, "GENERATION_TIMEOUT_SECONDS", 3.0)

    original_run = generation_service.director_pipeline.run

    def _slow_run(*args, **kwargs):
        spec = kwargs.get("spec")
        if spec and spec.get("domain") == "NFL_OFFENSE_LINEUP_COLLEGE":
            time.sleep(5.0)  # forces a real timeout regardless of how fast the real query now is
        return original_run(*args, **kwargs)

    monkeypatch.setattr(generation_service.director_pipeline, "run", _slow_run)

    with pytest.raises(GatewayError):
        generation_service.generate(
            request_text=None, spec=_LINEUP_COLLEGE_SPEC, provider="mock",
            puzzle_count=None, difficulty=None, seed="stuck-lineup-thread",
        )

    # The lineup call's background thread is now "stuck" sleeping for ~5s on
    # its OWN isolated executor. A different-domain call must not wait on it
    # -- if it were queued behind the stuck thread it would take >5s (or hit
    # its own 3s timeout first); real headroom (well under 3s) proves it
    # never contended for the stuck executor/lock at all.
    t0 = time.time()
    result = generation_service.generate(
        request_text=None, spec=_OTHER_SPEC, provider="mock",
        puzzle_count=None, difficulty=None, seed="unblocked-by-stuck-lineup",
    )
    elapsed = time.time() - t0
    assert result.get("qa_status") == "PASSED"
    assert elapsed < 2.5, f"unrelated generation call took {elapsed:.2f}s -- it was blocked by the stuck lineup thread"


def test_lineup_isolated_executor_is_actually_separate_from_the_shared_one():
    from gateway.services import generation as generation_service

    assert generation_service._lineup_executor is not generation_service._executor
    assert generation_service._lineup_generation_lock is not generation_service._generation_lock
    assert "NFL_OFFENSE_LINEUP" in generation_service._LINEUP_ISOLATED_DOMAINS
    assert "NFL_OFFENSE_LINEUP_COLLEGE" in generation_service._LINEUP_ISOLATED_DOMAINS
