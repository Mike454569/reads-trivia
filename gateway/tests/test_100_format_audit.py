"""Final 100-format audit/cleanup regression tests."""
from __future__ import annotations

from tools.director_v02.format_audit import (
    AUDIT_TARGET_DISTINCT_FORMATS,
    FORMAT_PRESENTATION_ALIASES,
    PUBLIC_MODE_ALIASES,
    audit_format_registry,
    audit_public_modes,
)


def test_format_inventory_is_honest_and_machine_readable():
    audit = audit_format_registry()
    assert audit["target_distinct_formats"] == AUDIT_TARGET_DISTINCT_FORMATS == 100
    assert audit["registered_format_count"] >= audit["distinct_format_count"]
    assert audit["registered_format_count"] == (
        audit["distinct_format_count"] + audit["presentation_alias_count"]
    )
    assert audit["target_gap"] == max(0, 100 - audit["distinct_format_count"])
    assert not audit["missing_required_fields"]
    assert not audit["bad_format_identity"]
    assert not audit["alias_metadata_errors"]


def test_chain_reaction_is_explicit_alias_not_fake_new_format():
    audit = audit_format_registry()
    assert FORMAT_PRESENTATION_ALIASES["CHAIN_REACTION"] == "SIX_DEGREES"
    assert audit["presentation_aliases"]["CHAIN_REACTION"] == "SIX_DEGREES"
    assert "CHAIN_REACTION" not in audit["distinct_format_ids"]
    assert "SIX_DEGREES" in audit["distinct_format_ids"]


def test_public_backend_duplicates_are_classified_and_not_discoverable_twice():
    from gateway.services import public_mechanics as pm

    audit = audit_public_modes(pm.PUBLIC_MECHANIC_MODES)
    assert not audit["missing_required_fields"]
    assert not audit["unclassified_duplicate_backends"]
    assert not audit["public_alias_errors"]
    assert PUBLIC_MODE_ALIASES["chain_reaction_cfb_nfl"] == "six_degrees_cfb_nfl"
    assert "chain_reaction_cfb_nfl" in audit["undiscoverable_modes"]

    listed = {entry["mode"] for entry in pm.list_public_mechanic_modes()}
    assert "six_degrees_cfb_nfl" in listed
    assert "chain_reaction_cfb_nfl" not in listed


def test_mobile_gaps_are_visible_not_silently_counted_as_verified():
    audit = audit_format_registry()
    assert audit["mobile_verified_count"] + len(audit["mobile_unverified"]) == audit["registered_format_count"]


def test_alias_metadata_is_locked_to_registry_truth():
    from tools.director_v02 import visual_templates as vt

    audit = audit_format_registry(vt.VISUAL_TEMPLATE_REGISTRY)
    alias_entry = vt.VISUAL_TEMPLATE_REGISTRY["CHAIN_REACTION"]
    assert alias_entry["presentation_alias_of"] == "SIX_DEGREES"
    assert alias_entry["counts_as_distinct_format"] is False
    assert alias_entry["creator_selectable"] is False
    assert audit["presentation_alias_count"] == 1
