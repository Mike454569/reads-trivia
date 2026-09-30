"""Reads 100-format audit helpers.

This module exists to keep three different concepts from being conflated:

* format: a genuinely different player interaction/presentation contract.
* public mode: a playable league/data implementation of a format.
* presentation alias: an alternate name/skin over the exact same backend.

The 100-format target is intentionally measured against distinct formats, never
NFL/CFB variants, public-mode aliases, or duplicate Creator cards.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Mapping

AUDIT_TARGET_DISTINCT_FORMATS = 100

# Exact known aliases discovered by the September 30, 2026 final format audit.
# Keep these explicit: a duplicate is never silently waved through.
FORMAT_PRESENTATION_ALIASES: dict[str, str] = {
    "CHAIN_REACTION": "SIX_DEGREES",
}

# Same rule at the public-mode layer. The alias remains callable for old links
# and saved state, but it is not discoverable and cannot count as a new format.
PUBLIC_MODE_ALIASES: dict[str, str] = {
    "chain_reaction_cfb_nfl": "six_degrees_cfb_nfl",
}

_REQUIRED_FORMAT_FIELDS = frozenset({
    "format_id", "display_name", "description", "supported_mechanics",
    "mechanic_family", "interaction_model", "validation_rules",
    "answer_schema", "generation_schema", "qa_requirements",
    "mobile_verified", "creator_selectable", "production_status",
})


def _duplicates(values: list[str]) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = defaultdict(list)
    for index, value in enumerate(values):
        positions[value].append(index)
    return {value: indexes for value, indexes in positions.items() if len(indexes) > 1}


def audit_format_registry(registry: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Return an honest, machine-readable format inventory.

    This function does not import the public Gateway, so it is safe for light
    registry/unit tests and tooling that does not have the Engine database.
    """
    if registry is None:
        from tools.director_v02.visual_templates import VISUAL_TEMPLATE_REGISTRY
        registry = VISUAL_TEMPLATE_REGISTRY

    ids = list(registry)
    missing_fields: dict[str, list[str]] = {}
    bad_identity: list[str] = []
    mobile_unverified: list[str] = []
    creator_hidden: list[str] = []
    statuses: Counter[str] = Counter()

    for format_id, entry in registry.items():
        missing = sorted(_REQUIRED_FORMAT_FIELDS.difference(entry))
        if missing:
            missing_fields[format_id] = missing
        if entry.get("format_id") != format_id:
            bad_identity.append(format_id)
        if entry.get("mobile_verified") is not True:
            mobile_unverified.append(format_id)
        if entry.get("creator_selectable") is not True:
            creator_hidden.append(format_id)
        statuses[str(entry.get("production_status", "MISSING"))] += 1

    aliases_present = {
        alias: canonical
        for alias, canonical in FORMAT_PRESENTATION_ALIASES.items()
        if alias in registry and canonical in registry
    }
    distinct_ids = [format_id for format_id in ids if format_id not in aliases_present]

    display_names = [str(registry[format_id].get("display_name", "")) for format_id in ids]
    duplicate_display_names = _duplicates(display_names)

    return {
        "target_distinct_formats": AUDIT_TARGET_DISTINCT_FORMATS,
        "registered_format_count": len(ids),
        "presentation_alias_count": len(aliases_present),
        "distinct_format_count": len(distinct_ids),
        "target_gap": max(0, AUDIT_TARGET_DISTINCT_FORMATS - len(distinct_ids)),
        "distinct_format_ids": distinct_ids,
        "presentation_aliases": aliases_present,
        "production_status_counts": dict(statuses),
        "mobile_verified_count": len(ids) - len(mobile_unverified),
        "mobile_unverified": mobile_unverified,
        "creator_selectable_count": len(ids) - len(creator_hidden),
        "creator_hidden": creator_hidden,
        "missing_required_fields": missing_fields,
        "bad_format_identity": bad_identity,
        "duplicate_display_names": duplicate_display_names,
    }


def audit_public_modes(modes: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Audit public modes without pretending each league/data variant is a format."""
    if modes is None:
        from gateway.services.public_mechanics import PUBLIC_MECHANIC_MODES
        modes = PUBLIC_MECHANIC_MODES

    backend_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    undiscoverable: list[str] = []
    missing_contract: dict[str, list[str]] = {}

    for mode_id, entry in modes.items():
        required = {"competition", "taxonomy_id", "variant", "title", "instructions", "kind", "gen_kwargs"}
        missing = sorted(required.difference(entry))
        if missing:
            missing_contract[mode_id] = missing
        taxonomy = str(entry.get("taxonomy_id", ""))
        variant = str(entry.get("variant", ""))
        backend_groups[(taxonomy, variant)].append(mode_id)
        if entry.get("discoverable", True) is not True:
            undiscoverable.append(mode_id)

    duplicate_backends = {
        f"{taxonomy}::{variant}": ids
        for (taxonomy, variant), ids in backend_groups.items()
        if len(ids) > 1
    }

    unclassified_duplicate_modes: dict[str, list[str]] = {}
    for backend_key, ids in duplicate_backends.items():
        canonicals = {PUBLIC_MODE_ALIASES.get(mode_id, mode_id) for mode_id in ids}
        if len(canonicals) != 1:
            unclassified_duplicate_modes[backend_key] = ids

    return {
        "public_mode_count": len(modes),
        "unique_backend_count": len(backend_groups),
        "duplicate_backend_count": len(duplicate_backends),
        "duplicate_backends": duplicate_backends,
        "presentation_aliases": dict(PUBLIC_MODE_ALIASES),
        "undiscoverable_modes": sorted(undiscoverable),
        "missing_required_fields": missing_contract,
        "unclassified_duplicate_backends": unclassified_duplicate_modes,
    }


def audit_snapshot() -> dict[str, Any]:
    """Combined snapshot used by CI/reporting."""
    formats = audit_format_registry()
    public_modes = audit_public_modes()
    return {
        "formats": formats,
        "public_modes": public_modes,
        "passes_integrity_gate": (
            not formats["missing_required_fields"]
            and not formats["bad_format_identity"]
            and not public_modes["missing_required_fields"]
            and not public_modes["unclassified_duplicate_backends"]
        ),
        # This is deliberately separate from integrity. Reads can be internally
        # honest/clean while still having work left before the 100-format goal.
        "reached_100_distinct_formats": formats["distinct_format_count"] >= AUDIT_TARGET_DISTINCT_FORMATS,
    }
