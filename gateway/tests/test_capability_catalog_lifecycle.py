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


def _make_test_row(c, capability_id: str, state: str, *, runtime_adapter_module: str | None = None) -> tuple:
    """Returns the (mechanic, domain, predicate) triple used, so a caller
    that needs to satisfy the Phase 2 IMPLEMENTED/PUBLIC_ENABLED registry-
    consistency gate can register a matching fake registry.py entry."""
    import datetime as _dt

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    domain, predicate = "TEST_DOMAIN", f"TEST_PREDICATE_{uuid.uuid4().hex[:8]}"
    c.execute(
        "INSERT INTO capability_catalog(capability_id, version, mechanic, domain, relationship_predicate, "
        "verification_status, public_availability, runtime_adapter_module, created_at, updated_at) "
        "VALUES (?,1,?,?,?,?,?,?,?,?)",
        (capability_id, "guess", domain, predicate, state, "PRIVATE", runtime_adapter_module, now, now),
    )
    c.commit()
    return ("guess", domain, predicate)


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


def test_blocked_reachable_from_any_state_but_never_straight_back_to_public(monkeypatch):
    from tools.director_v02 import catalog, registry

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        triple = _make_test_row(c, cap_id, "PUBLIC_ENABLED", runtime_adapter_module="tools.director_v02.catalog")
        # Phase 2's PUBLIC_ENABLED gate requires a real, matching registry.py
        # entry -- registered here so this test proves the transition-graph
        # rule (never straight back to PUBLIC_ENABLED without repassing
        # HUMAN_APPROVED), independent of the separate gate tests below.
        monkeypatch.setitem(registry.CAPABILITY_REGISTRY, triple, {})

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


# --- Phase 2: real automated gates on IMPLEMENTED/GENERATION_VERIFIED/ -----
# --- PUBLIC_ENABLED, not just graph-reachability ---------------------------

def test_implemented_transition_rejected_without_matching_registry_entry():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "STRUCTURALLY_VALIDATED")  # no registry.py entry registered
        with pytest.raises(catalog.InvalidTransitionError, match="registry"):
            catalog.transition(c, cap_id, "IMPLEMENTED")
        assert catalog.get_capability(c, cap_id)["verification_status"] == "STRUCTURALLY_VALIDATED"
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_implemented_transition_rejected_when_adapter_module_not_importable(monkeypatch):
    from tools.director_v02 import catalog, registry

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        triple = _make_test_row(
            c, cap_id, "STRUCTURALLY_VALIDATED",
            runtime_adapter_module="tools.director_v02.not_a_real_module_xyz",
        )
        monkeypatch.setitem(registry.CAPABILITY_REGISTRY, triple, {})
        with pytest.raises(catalog.InvalidTransitionError, match="not importable"):
            catalog.transition(c, cap_id, "IMPLEMENTED")
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_implemented_transition_succeeds_with_real_registry_entry_and_importable_adapter(monkeypatch):
    from tools.director_v02 import catalog, registry

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        triple = _make_test_row(
            c, cap_id, "STRUCTURALLY_VALIDATED", runtime_adapter_module="tools.director_v02.catalog",
        )
        monkeypatch.setitem(registry.CAPABILITY_REGISTRY, triple, {})
        result = catalog.transition(c, cap_id, "IMPLEMENTED")
        assert result["to_state"] == "IMPLEMENTED"
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_generation_verified_transition_rejected_without_any_tier2_probe():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "IMPLEMENTED")
        with pytest.raises(catalog.InvalidTransitionError, match="Tier-2"):
            catalog.transition(c, cap_id, "GENERATION_VERIFIED")
    finally:
        _cleanup(c, cap_id)
        c.close()


def test_generation_verified_transition_rejected_when_latest_tier2_probe_failed():
    import datetime as _dt

    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "IMPLEMENTED")
        c.execute(
            "INSERT INTO capability_health_probes(capability_id, tier, passed, checks_json, failure_reason, "
            "rounds_run, probed_at) VALUES (?,?,?,?,?,?,?)",
            (cap_id, "TIER2", 0, "{}", "simulated real probe failure", 100,
             _dt.datetime.now(_dt.timezone.utc).isoformat()),
        )
        c.commit()
        with pytest.raises(catalog.InvalidTransitionError, match="failed"):
            catalog.transition(c, cap_id, "GENERATION_VERIFIED")
    finally:
        c.execute("DELETE FROM capability_health_probes WHERE capability_id=?", (cap_id,))
        c.commit()
        _cleanup(c, cap_id)
        c.close()


def test_generation_verified_transition_succeeds_after_a_real_passing_tier2_probe():
    import datetime as _dt

    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "IMPLEMENTED")
        c.execute(
            "INSERT INTO capability_health_probes(capability_id, tier, passed, checks_json, failure_reason, "
            "rounds_run, probed_at) VALUES (?,?,?,?,?,?,?)",
            (cap_id, "TIER2", 1, "{}", None, 100, _dt.datetime.now(_dt.timezone.utc).isoformat()),
        )
        c.commit()
        result = catalog.transition(c, cap_id, "GENERATION_VERIFIED")
        assert result["to_state"] == "GENERATION_VERIFIED"
    finally:
        c.execute("DELETE FROM capability_health_probes WHERE capability_id=?", (cap_id,))
        c.commit()
        _cleanup(c, cap_id)
        c.close()


def test_generation_verified_gate_uses_the_most_recent_tier2_probe_not_the_first():
    """An older FAILED probe followed by a newer PASSING one must allow the
    transition -- the gate must order by probed_at, not just check "any
    probe exists" or "the first one inserted."."""
    import datetime as _dt

    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "IMPLEMENTED")
        older = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=1)).isoformat()
        newer = _dt.datetime.now(_dt.timezone.utc).isoformat()
        c.execute(
            "INSERT INTO capability_health_probes(capability_id, tier, passed, checks_json, failure_reason, "
            "rounds_run, probed_at) VALUES (?,'TIER2',0,'{}','older real failure',100,?)",
            (cap_id, older),
        )
        c.execute(
            "INSERT INTO capability_health_probes(capability_id, tier, passed, checks_json, failure_reason, "
            "rounds_run, probed_at) VALUES (?,'TIER2',1,'{}',NULL,100,?)",
            (cap_id, newer),
        )
        c.commit()
        result = catalog.transition(c, cap_id, "GENERATION_VERIFIED")
        assert result["to_state"] == "GENERATION_VERIFIED"
    finally:
        c.execute("DELETE FROM capability_health_probes WHERE capability_id=?", (cap_id,))
        c.commit()
        _cleanup(c, cap_id)
        c.close()


def test_public_enabled_transition_rejected_when_registry_drifted_since_implemented(monkeypatch):
    """Simulates a real drift scenario: a capability reached HUMAN_APPROVED
    with a valid registry entry, then the entry was removed/renamed (e.g. an
    adapter refactor) before release -- PUBLIC_ENABLED must catch this even
    though IMPLEMENTED's own gate passed earlier."""
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    cap_id = f"TEST_{uuid.uuid4().hex[:12]}"
    try:
        _make_test_row(c, cap_id, "HUMAN_APPROVED", runtime_adapter_module="tools.director_v02.catalog")
        # deliberately no registry.CAPABILITY_REGISTRY entry registered --
        # simulates the drifted/removed state
        with pytest.raises(catalog.InvalidTransitionError, match="registry"):
            catalog.transition(c, cap_id, "PUBLIC_ENABLED")
    finally:
        _cleanup(c, cap_id)
        c.close()
