"""Reliability-design Phase 1 -- lifecycle-transition enforcement tests.

catalog.transition() is the ONLY place a capability's verification_status
may change. These tests prove invalid transitions are rejected (never
silently clamped), the row is never mutated on a rejected transition, and
LEGACY_PUBLIC_PENDING_REVALIDATION is only reachable via the backfill, never
via transition() itself.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _make_test_row(c, capability_id: str, state: str) -> None:
    import datetime as _dt

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    c.execute(
        "INSERT INTO capability_catalog(capability_id, version, mechanic, domain, relationship_predicate, "
        "verification_status, public_availability, created_at, updated_at) VALUES (?,1,?,?,?,?,?,?,?)",
        (capability_id, "guess", "TEST_DOMAIN", f"TEST_PREDICATE_{uuid.uuid4().hex[:8]}", state, "PRIVATE", now, now),
    )
    c.commit()


def _cleanup(c, capability_id: str) -> None:
    c.execute("DELETE FROM capability_catalog WHERE capability_id=?", (capability_id,))
    c.commit()


def test_valid_forward_transition_succeeds():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "DISCOVERED")
        result = catalog.transition(c, cap_id, "DATA_PRESENT")
        assert result["from_state"] == "DISCOVERED"
        assert result["to_state"] == "DATA_PRESENT"
        assert catalog.get_capability(c, cap_id)["verification_status"] == "DATA_PRESENT"
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_skipping_states_is_rejected():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "DISCOVERED")
        with pytest.raises(catalog.InvalidTransitionError):
            catalog.transition(c, cap_id, "PUBLIC_ENABLED")
        # row must be unchanged -- a rejected transition never mutates anything
        assert catalog.get_capability(c, cap_id)["verification_status"] == "DISCOVERED"
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_legacy_state_only_reachable_via_backfill_never_via_transition():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "HUMAN_APPROVED")
        with pytest.raises(catalog.InvalidTransitionError):
            catalog.transition(c, cap_id, "LEGACY_PUBLIC_PENDING_REVALIDATION")
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_legacy_state_can_resume_into_structurally_validated():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "LEGACY_PUBLIC_PENDING_REVALIDATION")
        result = catalog.transition(c, cap_id, "STRUCTURALLY_VALIDATED")
        assert result["to_state"] == "STRUCTURALLY_VALIDATED"
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_blocked_reachable_from_any_state_but_never_straight_back_to_public():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "PUBLIC_ENABLED")
        result = catalog.transition(c, cap_id, "BLOCKED")
        assert result["to_state"] == "BLOCKED"
        with pytest.raises(catalog.InvalidTransitionError):
            catalog.transition(c, cap_id, "PUBLIC_ENABLED")
        # must repass HUMAN_APPROVED first
        catalog.transition(c, cap_id, "HUMAN_APPROVED")
        catalog.transition(c, cap_id, "PUBLIC_ENABLED")
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_transition_on_nonexistent_capability_raises_not_found():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    try:
        with pytest.raises(catalog.CapabilityNotFoundError):
            catalog.transition(c, "NOT_A_REAL_CAPABILITY_ID", "DATA_PRESENT")
    finally:
        c.close()


def test_invalid_target_state_name_raises():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "DISCOVERED")
        with pytest.raises(catalog.InvalidTransitionError):
            catalog.transition(c, cap_id, "NOT_A_REAL_STATE")
    finally:
        _cleanup(c, cap_id)
        c.close()
