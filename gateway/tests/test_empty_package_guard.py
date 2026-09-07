"""Closeout pass (Part 9): permanent regression coverage for the "SUPPORTED
mode routinely generates empty packages" failure class.

The actual guards here were built by an earlier "Reliability-design Phase
1/2/3" pass (tools/director_v02/feasibility.py, health_probe.py, catalog.py)
-- this file exists to prove they are ALL still wired correctly and that
every currently-public capability (including this pass's own new Franchise
Marathon rebuild) actually satisfies them, not to reimplement the guard.
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


def test_every_publicly_claiming_capability_has_a_real_passing_tier2_probe():
    """The real, structural guarantee behind "SUPPORTED means proven to
    generate": every capability_catalog row claiming PUBLIC_ENABLED or
    LEGACY_PUBLIC_PENDING_REVALIDATION must have a real Tier-2 (100-round)
    certification probe on record that actually passed. A row that slipped
    through without one would be exactly the "labeled SUPPORTED but
    generation returned Load failed" incident this whole mechanism exists
    to prevent."""
    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT capability_id, verification_status FROM capability_catalog "
            "WHERE verification_status IN ('PUBLIC_ENABLED', 'LEGACY_PUBLIC_PENDING_REVALIDATION')"
        ).fetchall()
        assert len(rows) >= 30, "sanity check -- the public capability count should not have collapsed"
        missing = []
        for row in rows:
            probe = c.execute(
                "SELECT passed FROM capability_health_probes WHERE capability_id=? AND tier='TIER2' "
                "ORDER BY probed_at DESC LIMIT 1",
                (row["capability_id"],),
            ).fetchone()
            if not probe or not probe["passed"]:
                missing.append(row["capability_id"])
        assert missing == [], f"public capabilities with no passing Tier-2 probe on record: {missing}"
    finally:
        c.close()


def test_franchise_marathon_has_a_real_passing_tier2_probe_on_record():
    """This pass's own new capability, checked explicitly by name -- not
    just swept up in the generic count above."""
    c = engine_bootstrap.connect()
    try:
        row = c.execute(
            "SELECT verification_status FROM capability_catalog WHERE capability_id=?",
            ("NFL_FRANCHISE_MARATHON__FRANCHISE_MARATHON_STAGE",),
        ).fetchone()
        assert row is not None
        assert row["verification_status"] == "PUBLIC_ENABLED"
        probe = c.execute(
            "SELECT passed, rounds_run FROM capability_health_probes WHERE capability_id=? AND tier='TIER2' "
            "ORDER BY probed_at DESC LIMIT 1",
            ("NFL_FRANCHISE_MARATHON__FRANCHISE_MARATHON_STAGE",),
        ).fetchone()
        assert probe is not None and probe["passed"]
        assert probe["rounds_run"] >= 100
    finally:
        c.close()


def test_generate_package_from_spec_never_reports_passed_with_zero_questions():
    """Structural guard at the source: tools/game_director_v01.py's own
    qa_status computation must require non-empty questions, not just an
    empty contract_failures list (both being empty is also true when there
    was simply nothing to fail validation)."""
    src = (REPO_ROOT / "tools" / "game_director_v01.py").read_text()
    assert 'if (not contract_failures and questions) else "FAILED"' in src, (
        "qa_status must require real, non-empty questions -- not just an absence of failures"
    )


def test_public_game_route_never_returns_a_hollow_success_for_an_impossible_filter():
    """Live functional check: an impossible caller-supplied filter (a
    franchise name that doesn't exist) must raise a real, clean error --
    never a 200 with an empty/degenerate package."""
    from gateway.errors import GatewayError
    from gateway.services import public_game as pg

    with pytest.raises(GatewayError) as exc_info:
        pg.get_public_game(
            mode="franchise_marathon_guess", difficulty=None, seed="test-empty-guard",
            exclude_game_ids=[], stage_index=0, filter_value="NotARealFranchiseXYZ",
        )
    assert exc_info.value.code == "NO_ELIGIBLE_GAME"


def test_public_modes_never_advertise_a_min_question_count_of_zero():
    """A registered capability's min_question_count must never be 0 -- that
    would mean the registry itself considers an empty package acceptable."""
    from tools.director_v02 import registry

    zero_min = [
        f"{mechanic}/{domain}/{predicate}"
        for (mechanic, domain, predicate), cap in registry.CAPABILITY_REGISTRY.items()
        if cap.get("min_question_count") == 0
    ]
    assert zero_min == [], f"capabilities with min_question_count=0: {zero_min}"
