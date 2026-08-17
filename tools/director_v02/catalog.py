"""Capability catalog -- read API + strict lifecycle-transition enforcement.

Reliability-design Phase 1. This module is the ONLY place that is allowed
to change a capability_catalog row's verification_status -- every other
module (feasibility.py, the future Creator Intelligence layer) reads
through here, never writes verification_status directly.

The whole point of this catalog (see capability_catalog_schema.py's module
docstring for the real incident it exists to prevent) is that SUPPORTED can
never again be claimed from registry presence alone. That guarantee is only
real if state transitions are enforced in exactly one place, not scattered
across every caller.
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

# The real forward progression. LEGACY_PUBLIC_PENDING_REVALIDATION is
# deliberately NOT a key here -- it is never entered via transition(), only
# via the one-time backfill migration (capability_catalog_schema.py). Its
# own forward path re-enters the normal graph at STRUCTURALLY_VALIDATED,
# reflecting that a grandfathered capability still needs the SAME real
# re-validation work (identity resolution, coverage, tie/ambiguity rules
# measured and recorded) as anything new -- it does not skip ahead.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "DISCOVERED": frozenset({"DATA_PRESENT", "BLOCKED"}),
    "DATA_PRESENT": frozenset({"STRUCTURALLY_VALIDATED", "BLOCKED"}),
    "STRUCTURALLY_VALIDATED": frozenset({"IMPLEMENTED", "BLOCKED"}),
    "IMPLEMENTED": frozenset({"GENERATION_VERIFIED", "BLOCKED"}),
    "GENERATION_VERIFIED": frozenset({"HUMAN_APPROVED", "BLOCKED"}),
    "HUMAN_APPROVED": frozenset({"PUBLIC_ENABLED", "BLOCKED"}),
    "PUBLIC_ENABLED": frozenset({"BLOCKED"}),
    "LEGACY_PUBLIC_PENDING_REVALIDATION": frozenset({"STRUCTURALLY_VALIDATED", "BLOCKED"}),
    "BLOCKED": frozenset({
        "DISCOVERED", "DATA_PRESENT", "STRUCTURALLY_VALIDATED", "IMPLEMENTED",
        "GENERATION_VERIFIED", "HUMAN_APPROVED",
    }),  # a human/automated reset decides which state to resume from; never straight back to PUBLIC_ENABLED
        # without repassing HUMAN_APPROVED first.
}

VALID_STATES = frozenset(ALLOWED_TRANSITIONS.keys())


class InvalidTransitionError(ValueError):
    pass


class CapabilityNotFoundError(ValueError):
    pass


def get_capability(c, capability_id: str) -> dict | None:
    row = c.execute("SELECT * FROM capability_catalog WHERE capability_id=?", (capability_id,)).fetchone()
    return dict(row) if row else None


def get_capability_by_triple(c, mechanic: str, domain: str, predicate: str) -> dict | None:
    row = c.execute(
        "SELECT * FROM capability_catalog WHERE mechanic=? AND domain=? AND relationship_predicate=?",
        (mechanic, domain, predicate),
    ).fetchone()
    return dict(row) if row else None


_REGISTERABLE_METADATA_COLUMNS = frozenset({
    "input_entity_type", "input_scoping_fields", "output_entity_type",
    "source_tables", "source_columns", "required_joins",
    "canonical_identity_fields", "identity_resolution_method", "identity_resolution_rate",
    "season_coverage_min", "season_coverage_max", "season_coverage_notes",
    "team_or_school_coverage", "player_coverage", "game_coverage",
    "source_id", "refresh_dataset_key", "freshness_category", "freshness_notes",
    "tie_rule", "ambiguity_rule", "eligible_answer_rule", "distractor_scoping_rule",
    "min_candidate_pool_size", "known_limitations",
})


def register_new_capability(c, *, mechanic: str, domain: str, predicate: str,
                             runtime_adapter_module: str, compiler_support: str = "HAND_WRITTEN",
                             **metadata) -> str:
    """Registers a brand-new capability at DISCOVERED -- the real entry
    point into the lifecycle graph for a capability that has never existed
    before (as opposed to backfill_legacy_capabilities()'s one-time import
    of pre-existing production capabilities). Unlike the legacy backfill,
    this accepts real relationship metadata up front (source tables,
    identity/season/tie/ambiguity/distractor rules) -- a new capability has
    no excuse for the NULL scoping fields Phase 2 found on every legacy row.

    `compiler_support` should be "COMPILER_GENERATED" for an adapter built
    via tools/director_v02/compiler.py's compile_adapter(), "HAND_WRITTEN"
    otherwise -- an honest, checkable distinction, not decoration.

    Raises ValueError if a row for this (mechanic, domain, predicate) triple
    already exists -- never silently overwrites or reuses one."""
    capability_id = f"{domain}__{predicate}"
    existing = get_capability_by_triple(c, mechanic, domain, predicate)
    if existing is not None:
        raise ValueError(f"capability already registered for {(mechanic, domain, predicate)!r}: {existing['capability_id']!r}")

    unknown_keys = set(metadata) - _REGISTERABLE_METADATA_COLUMNS
    if unknown_keys:
        raise ValueError(f"unknown metadata field(s): {sorted(unknown_keys)}")

    columns = ["capability_id", "version", "mechanic", "domain", "relationship_predicate",
               "verification_status", "human_review_status", "compiler_support",
               "runtime_adapter_module", "public_availability", "created_at", "updated_at"]
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    values = [capability_id, 1, mechanic, domain, predicate,
              "DISCOVERED", None, compiler_support,
              runtime_adapter_module, "PRIVATE", now, now]

    for key, value in metadata.items():
        columns.append(key)
        values.append(json.dumps(value) if key == "known_limitations" else value)

    placeholders = ",".join("?" for _ in values)
    c.execute(f"INSERT INTO capability_catalog({','.join(columns)}) VALUES ({placeholders})", values)
    c.commit()
    return capability_id


def list_capabilities(c, *, verification_status: str | None = None) -> list[dict]:
    if verification_status is not None:
        rows = c.execute(
            "SELECT * FROM capability_catalog WHERE verification_status=? ORDER BY capability_id",
            (verification_status,),
        ).fetchall()
    else:
        rows = c.execute("SELECT * FROM capability_catalog ORDER BY capability_id").fetchall()
    return [dict(r) for r in rows]


def _gate_registry_consistency(c, capability_id: str) -> dict:
    """Gates entry into IMPLEMENTED and PUBLIC_ENABLED: registry.py must
    have exactly one entry for this capability's (mechanic, domain,
    predicate) triple, and its runtime_adapter_module must actually import.
    Re-checked at PUBLIC_ENABLED (not just IMPLEMENTED) as a final
    drift-safety net -- the registry can drift between when a capability was
    first implemented and when it's later approved for release."""
    return verify_registry_consistency(capability_id)


def _gate_passing_tier2_probe(c, capability_id: str) -> dict:
    """Gates entry into GENERATION_VERIFIED: a real Tier-2 (100-round)
    certification probe (health_probe.py, Phase 2) must exist for this
    capability and have passed. This is the literal meaning of
    GENERATION_VERIFIED -- claiming it without a passing behavioral probe on
    record is exactly the "labeled SUPPORTED but generation returned Load
    failed" failure mode this whole catalog exists to prevent."""
    row = c.execute(
        "SELECT passed, failure_reason, probed_at FROM capability_health_probes "
        "WHERE capability_id=? AND tier='TIER2' ORDER BY probed_at DESC LIMIT 1",
        (capability_id,),
    ).fetchone()
    if row is None:
        return {"ok": False, "reason": "no Tier-2 certification probe has ever been run for this capability"}
    if not row["passed"]:
        return {"ok": False, "reason": f"latest Tier-2 probe ({row['probed_at']}) failed: {row['failure_reason']}"}
    return {"ok": True, "capability_id": capability_id, "probed_at": row["probed_at"]}


# Gated by destination state, not by (from_state, to_state) pair -- the
# invariant is about what the destination state MEANS, regardless of which
# allowed path was used to reach it (e.g. a reset from BLOCKED straight back
# to IMPLEMENTED must satisfy the same real check as the first time).
_TRANSITION_GATES = {
    "IMPLEMENTED": _gate_registry_consistency,
    "GENERATION_VERIFIED": _gate_passing_tier2_probe,
    "PUBLIC_ENABLED": _gate_registry_consistency,
}


def transition(c, capability_id: str, to_state: str, *, reason: str | None = None) -> dict:
    """The one and only way a capability's verification_status may change.
    Raises InvalidTransitionError (never silently clamps or guesses) if
    `to_state` is not reachable from the row's current state -- this is the
    real enforcement mechanism, not just documentation of intended states.

    Phase 2: transitions into IMPLEMENTED, GENERATION_VERIFIED, and
    PUBLIC_ENABLED are additionally gated by _TRANSITION_GATES -- a real,
    automated check, not just a graph-reachability rule. Rows already
    sitting in these states (including every LEGACY_PUBLIC_PENDING_REVALIDATION
    row's PUBLIC_ENABLED-equivalent public_availability, and every capability
    the Phase 1 backfill already placed at PUBLIC_ENABLED) are untouched --
    these gates only apply to NEW transition() calls going forward, matching
    "preserve existing public behavior"."""
    if to_state not in VALID_STATES:
        raise InvalidTransitionError(f"{to_state!r} is not a valid lifecycle state")

    row = get_capability(c, capability_id)
    if row is None:
        raise CapabilityNotFoundError(f"no capability_catalog row for {capability_id!r}")

    current = row["verification_status"]
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if to_state not in allowed:
        raise InvalidTransitionError(
            f"{capability_id}: {current!r} -> {to_state!r} is not an allowed transition "
            f"(allowed from {current!r}: {sorted(allowed)})"
        )

    gate = _TRANSITION_GATES.get(to_state)
    if gate is not None:
        gate_result = gate(c, capability_id)
        if not gate_result["ok"]:
            raise InvalidTransitionError(
                f"{capability_id}: cannot transition {current!r} -> {to_state!r} -- {gate_result['reason']}"
            )

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    c.execute(
        "UPDATE capability_catalog SET verification_status=?, updated_at=? WHERE capability_id=?",
        (to_state, now, capability_id),
    )
    c.commit()
    return {"capability_id": capability_id, "from_state": current, "to_state": to_state,
            "reason": reason, "transitioned_at": now}


def verify_registry_consistency(capability_id: str) -> dict:
    """Phase-1 scoped subset of the full drift check (revision 3, §4): for
    a single capability, confirms exactly one registry.py entry matches its
    (mechanic, domain, predicate) triple and that its recorded
    runtime_adapter_module is actually importable. Required before any
    future transition to PUBLIC_ENABLED (not yet wired as an enforced gate
    in transition() itself -- that requires the liveness probe from Phase 2
    to be meaningful; Phase 1 only adds this as a callable, tested check)."""
    import importlib

    from tools.director_v02 import registry

    c = engine_bootstrap.connect()
    try:
        row = get_capability(c, capability_id)
    finally:
        c.close()
    if row is None:
        return {"ok": False, "reason": f"no catalog row for {capability_id!r}"}

    triple = (row["mechanic"], row["domain"], row["relationship_predicate"])
    matches = [k for k in registry.CAPABILITY_REGISTRY if k == triple]
    if len(matches) == 0:
        return {"ok": False, "reason": f"no registry.py entry for {triple!r}"}
    if len(matches) > 1:
        return {"ok": False, "reason": f"{len(matches)} registry.py entries for {triple!r} -- must be exactly one"}

    module_path = row["runtime_adapter_module"]
    if not module_path:
        return {"ok": False, "reason": "no runtime_adapter_module recorded"}
    try:
        importlib.import_module(module_path)
    except Exception as e:
        return {"ok": False, "reason": f"runtime_adapter_module {module_path!r} not importable: {e!r}"}

    return {"ok": True, "capability_id": capability_id, "triple": triple, "runtime_adapter_module": module_path}
