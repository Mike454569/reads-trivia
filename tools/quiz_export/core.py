"""Shared export orchestrator.

Ties safety, candidate evaluation, contract validation, duplicate
detection, serialization, and audit stats together. Contains zero
football-domain logic -- every domain-specific decision is delegated to the
adapter passed in. See QUIZ_EXPORT_FRAMEWORK_REFACTOR_PLAN.md for the
adapter interface this expects.

Critical: the per-candidate loop below does NOT decide check order --
adapter.evaluate() owns that entirely, because preserving each domain's
exact original sequence of RNG draws is required for byte-identical output
(see the refactor plan's "RNG call order must be preserved exactly" note).
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from . import audit, contract, duplicates, engine, serializer


def run_export(adapter, *, seed: str | None = None, target_count: int | None = None,
                out_path: Path | None = None, id_start: int | None = None,
                raw_rows_override: list | None = None) -> dict:
    """raw_rows_override: opt-in escape hatch, default None (preserves existing behavior for
    every current caller byte-for-byte -- re-verified after this was added). When provided,
    skips adapter.fetch_ordered_candidates() and evaluates this list instead -- e.g. so a
    caller can source candidates from a Director-parsed spec via game_factory.generate_candidates()
    directly rather than the adapter's own hardcoded spec, while still reusing the adapter's
    proven per-candidate evaluate()/safety_check() logic. See tools/game_director_v01.py."""
    seed = seed if seed is not None else adapter.SEED
    target_count = target_count if target_count is not None else adapter.TARGET_COUNT
    out_path = out_path if out_path is not None else adapter.OUT_PATH
    id_start = id_start if id_start is not None else adapter.ID_START

    c = engine.connect()
    safety = adapter.safety_check(c)
    raw_rows = raw_rows_override if raw_rows_override is not None else adapter.fetch_ordered_candidates(c, seed)
    considered = len(raw_rows)

    rejected_counts: Counter = Counter()
    accepted: list[dict] = []
    guard = duplicates.DuplicateGuard(track_entity=getattr(adapter, "TRACK_ENTITY", True))
    rng = engine.seeded(f"{seed}:distractors")

    for raw in raw_rows:
        result = adapter.evaluate(c, raw, rng, guard)
        if isinstance(result, str):
            rejected_counts[result] += 1
            continue
        result["id"] = id_start + len(accepted)
        accepted.append(result)
        entity_key = result.get("_audit", {}).get("entity_key")
        guard.record(result["question"], entity_key)

    c.close()

    exported = accepted[:target_count]
    shortfall_reason = None
    if len(exported) < target_count:
        shortfall_reason = adapter.shortfall_reason(len(accepted), considered, target_count)

    contract_failures = contract.validate_all(exported, adapter.CATEGORY)
    dup_questions = duplicates.find_duplicates(exported, lambda q: q["question"])
    dup_ids = duplicates.find_duplicates(exported, lambda q: q["id"])

    serializer.write_quiz_js(out_path, adapter.GLOBAL_NAME, adapter.header_lines(seed), exported)

    funnel_stats = audit.build_base_funnel_stats(
        seed=seed, considered=considered, rejected_counts=rejected_counts,
        accepted=accepted, exported=exported, contract_failures=contract_failures,
        dup_questions=dup_questions, dup_ids=dup_ids,
    )
    funnel_stats["shortfall_reason"] = shortfall_reason
    funnel_stats["safety"] = safety
    funnel_stats.update(adapter.extra_funnel_fields(accepted, exported))

    return {
        "accepted": accepted,
        "exported": exported,
        "funnel_stats": funnel_stats,
        "considered": considered,
        "rejected_counts": rejected_counts,
        "out_path": out_path,
    }


def print_summary(result: dict) -> None:
    fs = result["funnel_stats"]
    print(f"Considered: {result['considered']}")
    print(f"Rejected: {sum(result['rejected_counts'].values())}")
    print(f"Accepted (passed all checks): {len(result['accepted'])}")
    print(f"Exported: {len(result['exported'])}")
    if fs.get("shortfall_reason"):
        print(f"SHORTFALL: {fs['shortfall_reason']}")
    print(f"Contract failures: {len(fs['contract_failures'])}")
    print(f"Wrote {result['out_path']}")
