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


def list_capabilities(c, *, verification_status: str | None = None) -> list[dict]:
    if verification_status is not None:
        rows = c.execute(
            "SELECT * FROM capability_catalog WHERE verification_status=? ORDER BY capability_id",
            (verification_status,),
        ).fetchall()
    else:
        rows = c.execute("SELECT * FROM capability_catalog ORDER BY capability_id").fetchall()
    return [dict(r) for r in rows]


def transition(c, capability_id: str, to_state: str, *, reason: str | None = None) -> dict:
    """The one and only way a capability's verification_status may change.
    Raises InvalidTransitionError (never silently clamps or guesses) if
    `to_state` is not reachable from the row's current state -- this is the
    real enforcement mechanism, not just documentation of intended states."""
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
