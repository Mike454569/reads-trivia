"""Reliability-design Phase 1 -- corrected feasibility vocabulary tests.

Proves the new vocabulary is real, mapped correctly, and additive: existing
assess() behavior for every real request is byte-for-byte unchanged (the
explicit Phase 1 requirement), while the new catalog_status diagnostic
field is correctly populated and never claims SUPPORTED for a capability
that isn't actually LEGACY_PUBLIC_PENDING_REVALIDATION/PUBLIC_ENABLED in
the catalog.
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


def test_catalog_support_statuses_are_the_seven_approved_terms():
    from tools.director_v02 import feasibility

    assert feasibility.CATALOG_SUPPORT_STATUSES == {
        "SUPPORTED", "VERIFIED_NOT_RELEASED", "IMPLEMENTED_NOT_VERIFIED",
        "DATA_EXISTS_UNVERIFIED", "UNDERSTOOD_NOT_IMPLEMENTED",
        "INSUFFICIENT_COVERAGE", "TEMPORARILY_UNAVAILABLE",
    }


def test_implemented_but_unreleased_is_never_called_unsupported_mechanic():
    """The explicit correction: HUMAN_APPROVED/GENERATION_VERIFIED map to
    VERIFIED_NOT_RELEASED, never to a generic 'unsupported' label."""
    from tools.director_v02.feasibility import _CATALOG_STATE_TO_VOCAB

    assert _CATALOG_STATE_TO_VOCAB["HUMAN_APPROVED"] == "VERIFIED_NOT_RELEASED"
    assert _CATALOG_STATE_TO_VOCAB["GENERATION_VERIFIED"] == "VERIFIED_NOT_RELEASED"
    assert "UNSUPPORTED" not in _CATALOG_STATE_TO_VOCAB["HUMAN_APPROVED"]


def test_catalog_status_for_real_legacy_capability_is_supported():
    from tools.director_v02 import feasibility

    status = feasibility.catalog_status_for("guess", "NFL_DRAFT", "DRAFTED_BY")
    assert status == "SUPPORTED"


def test_catalog_status_for_unknown_triple_is_none():
    from tools.director_v02 import feasibility

    status = feasibility.catalog_status_for("guess", "NOT_A_REAL_DOMAIN", "NOT_A_REAL_PREDICATE")
    assert status is None


def test_assess_support_status_unchanged_for_real_supported_request():
    """Preserve existing runtime behavior -- explicit Phase 1 requirement."""
    from tools.director_v02 import feasibility

    r = feasibility.assess(
        "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him."
    )
    assert r["support_status"] == "SUPPORTED"
    # Phase 2 correction: catalog_status is the RAW internal state, kept
    # separate from user-facing support_status -- never a duplicate of it.
    assert r["catalog_status"] == "LEGACY_PUBLIC_PENDING_REVALIDATION"
    assert r["catalog_vocabulary_status"] == "SUPPORTED"


def test_assess_support_status_unchanged_for_real_unsupported_request():
    from tools.director_v02 import feasibility

    r = feasibility.assess("Make me an NFL trivia game about players favorite foods.")
    assert r["support_status"] == "UNKNOWN"
    assert r["catalog_status"] is None


def test_assess_support_status_unchanged_for_real_missing_data_request():
    from tools.director_v02 import feasibility

    r = feasibility.assess("Make me an NFL trivia game about injuries.")
    assert r["support_status"] == "MISSING_DATA"
    assert r["catalog_status"] is None


def test_assess_never_raises_when_catalog_lookup_fails(monkeypatch):
    """The diagnostic cross-check is defensively wrapped -- a catalog lookup
    failure must degrade to catalog_status=None, never break a real
    feasibility response."""
    from tools.director_v02 import catalog, feasibility

    def boom(*args, **kwargs):
        raise RuntimeError("simulated catalog failure")

    monkeypatch.setattr(catalog, "get_capability_by_triple", boom)
    r = feasibility.assess(
        "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him."
    )
    assert r["support_status"] == "SUPPORTED"  # unaffected
    assert r["catalog_status"] is None  # diagnostic degraded, not the real response
    assert r["catalog_vocabulary_status"] is None


def test_raw_catalog_state_for_real_legacy_capability_is_the_actual_lifecycle_state():
    """Phase 2 correction, tested directly: raw_catalog_state_for() exposes
    the real internal state, distinct from the mapped vocabulary term."""
    from tools.director_v02 import feasibility

    assert feasibility.raw_catalog_state_for("guess", "NFL_DRAFT", "DRAFTED_BY") == "LEGACY_PUBLIC_PENDING_REVALIDATION"
    assert feasibility.catalog_status_for("guess", "NFL_DRAFT", "DRAFTED_BY") == "SUPPORTED"


def test_all_21_legacy_capabilities_resolve_to_supported_via_catalog_status_for():
    from tools.director_v02 import catalog, feasibility

    c = engine_bootstrap.connect()
    try:
        rows = catalog.list_capabilities(c, verification_status="LEGACY_PUBLIC_PENDING_REVALIDATION")
    finally:
        c.close()
    assert len(rows) == 21
    for row in rows:
        status = feasibility.catalog_status_for(row["mechanic"], row["domain"], row["relationship_predicate"])
        assert status == "SUPPORTED", f"{row['capability_id']} should resolve to SUPPORTED, got {status}"
