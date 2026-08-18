"""Reliability-design Phase 1 -- catalog schema + backfill tests.

Confirms the real migration already run against this Engine produced the
right shape: every real registered capability backfilled exactly once,
with LEGACY_PUBLIC_PENDING_REVALIDATION (never HUMAN_APPROVED -- these are
grandfathered, not newly certified) and PUBLIC_ENABLED availability
(preserving today's real, unchanged behavior). Also proves the migration
itself is idempotent -- re-running it must never duplicate or overwrite an
existing row.
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


def test_capability_catalog_table_exists_with_expected_columns():
    c = engine_bootstrap.connect()
    try:
        cols = {r["name"] for r in c.execute("PRAGMA table_info(capability_catalog)").fetchall()}
    finally:
        c.close()
    for required in (
        "capability_id", "mechanic", "domain", "relationship_predicate",
        "verification_status", "human_review_status", "public_availability",
        "runtime_adapter_module", "compiler_support",
    ):
        assert required in cols


def test_every_registered_capability_has_exactly_one_catalog_row():
    from tools.director_v02 import registry

    c = engine_bootstrap.connect()
    try:
        rows = c.execute("SELECT mechanic, domain, relationship_predicate FROM capability_catalog").fetchall()
    finally:
        c.close()
    catalog_triples = {(r["mechanic"], r["domain"], r["relationship_predicate"]) for r in rows}
    assert len(rows) == len(catalog_triples), "duplicate catalog rows for the same triple"
    assert catalog_triples == set(registry.CAPABILITY_REGISTRY.keys())


def test_legacy_capabilities_are_not_marked_human_approved():
    """The explicit correction from the approved design: grandfathered
    capabilities must never be silently claimed as newly certified."""
    c = engine_bootstrap.connect()
    try:
        bad = c.execute(
            "SELECT capability_id FROM capability_catalog WHERE human_review_status='APPROVED'"
        ).fetchall()
        legacy_rows = c.execute(
            "SELECT capability_id, verification_status, human_review_status FROM capability_catalog "
            "WHERE verification_status='LEGACY_PUBLIC_PENDING_REVALIDATION'"
        ).fetchall()
    finally:
        c.close()
    assert not bad
    assert len(legacy_rows) == 21, f"expected 21 real backfilled legacy capabilities, found {len(legacy_rows)}"
    for row in legacy_rows:
        assert row["human_review_status"] == "LEGACY_GRANDFATHERED"


def test_legacy_capabilities_preserve_public_availability():
    """Preserve existing runtime behavior: end-user availability is
    unchanged for the 21 real, already-live capabilities."""
    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT public_availability FROM capability_catalog "
            "WHERE verification_status='LEGACY_PUBLIC_PENDING_REVALIDATION'"
        ).fetchall()
    finally:
        c.close()
    assert rows
    assert all(r["public_availability"] == "PUBLIC_ENABLED" for r in rows)


def test_no_coverage_fields_were_fabricated_on_backfill():
    """Explicit anti-fabrication check: coverage/resolution-rate fields must
    be NULL for every backfilled row, never a guessed placeholder number."""
    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT identity_resolution_rate, season_coverage_min, season_coverage_max "
            "FROM capability_catalog WHERE verification_status='LEGACY_PUBLIC_PENDING_REVALIDATION'"
        ).fetchall()
    finally:
        c.close()
    for row in rows:
        assert row["identity_resolution_rate"] is None
        assert row["season_coverage_min"] is None
        assert row["season_coverage_max"] is None


def test_migration_backfill_is_idempotent():
    from tools.data_refresh.capability_catalog_schema import backfill_legacy_capabilities

    c = engine_bootstrap.connect()
    try:
        before_count = c.execute("SELECT COUNT(*) FROM capability_catalog").fetchone()[0]
        result = backfill_legacy_capabilities(c)
        c.commit()
        after_count = c.execute("SELECT COUNT(*) FROM capability_catalog").fetchone()[0]
    finally:
        c.close()
    assert result["inserted"] == 0
    assert result["skipped_existing"] == before_count
    assert after_count == before_count


def test_mechanic_taxonomy_seeded_with_seven_templates_honest_pipeline_support_flags():
    """Phase 1 seeded 6 templates with only 2 genuinely pipeline-supported
    (the other 4 honest placeholders, never fabricated as built). Phase 6
    (Mechanic Execution Framework) added the 7th (POSITION_LINEUP_GRID,
    formalizing the pre-existing lineup-board visual templates) and built
    real, tested generators for all 4 former placeholders -- so all 7 are
    now honestly creator_pipeline_supported AND template_status=
    PRODUCTION_READY (see tools/director_v04/{matching,sorting,elimination,
    higher_lower}.py and mechanic_engine.py)."""
    c = engine_bootstrap.connect()
    try:
        rows = c.execute("SELECT taxonomy_id, creator_pipeline_supported, template_status FROM mechanic_taxonomy").fetchall()
    finally:
        c.close()
    by_id = {r["taxonomy_id"]: r["creator_pipeline_supported"] for r in rows}
    status_by_id = {r["taxonomy_id"]: r["template_status"] for r in rows}
    assert len(by_id) == 7
    for taxonomy_id in ("MULTIPLE_CHOICE_SINGLE_FACT", "PROGRESSIVE_CLUE_IDENTIFY", "MATCHING",
                         "SORTING_TIMELINE", "HIGHER_LOWER_STREAK", "ELIMINATION_SURVIVAL", "POSITION_LINEUP_GRID"):
        assert by_id[taxonomy_id] == 1
        assert status_by_id[taxonomy_id] == "PRODUCTION_READY"
