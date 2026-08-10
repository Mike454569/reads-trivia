#!/usr/bin/env python3
"""Director v0.1 -- the smallest genuinely-working pipeline from a natural-language
game request to a verified, structured, playable GeneratedGamePackage.

    natural language -> Director parse -> feasibility -> Game Factory -> strong QA
    -> GeneratedGamePackage

Deliberately narrow, per GAME_DIRECTOR_PRODUCTION_INTEGRATION_PLAN.md's "smallest
possible milestone" recommendation:

  - Reuses game_director.interpret() UNCHANGED -- the one part of the existing
    "AI Game Director" prototype that's genuinely working. game_director.py,
    game_director_api.py, and game_factory.py are not modified by this file.
  - Never calls game_director.publish() (confirmed broken -- calls a nonexistent
    game_factory.build_mode()) or game_director.preview()'s own thin
    _candidate_qa(). QA authority here is game_factory.qa_candidate() (Engine's
    real QA) plus the same shared validators already proven across three
    approved pilots (tools/quiz_export/contract.py etc.).
  - Only ever produces a package for mechanic == "guess", and only for a
    predicate that already has a proven Reads adapter registered in
    ADAPTER_REGISTRY below (today: just DRAFTED_BY, reusing
    tools/quiz_export/adapters/draft.py exactly as built for the three
    approved pilots). This is a registry to extend, not a generic football
    query engine to build.
  - Never writes into data/*.js, never touches puzzle_catalog, never starts a
    server, never calls out to any LLM.

See GENERATED_GAME_PACKAGE_SCHEMA.md for the full package shape.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import audit, contract, duplicates, engine, serializer  # noqa: E402
from tools.quiz_export.adapters import draft as draft_adapter  # noqa: E402

# Director v0.7, Part D: ENGINE_DIR now comes from tools.quiz_export.engine
# (single source of truth, overridable via READS_ENGINE_DIR -- see that
# module's docstring) instead of a second hardcoded copy of the same path.
# engine.py's own import already put ENGINE_DIR on sys.path, so this
# `import game_director` finds it too without a redundant insert.
ENGINE_DIR = engine.ENGINE_DIR
import game_director as GD  # noqa: E402  existing, UNMODIFIED prototype -- only .interpret() is reused
# NOTE: this module no longer imports game_factory directly (as of Director
# v0.3) -- candidate generation is delegated entirely to each adapter's own
# `fetch_ordered_candidates(c, seed)` (see generate_package_from_spec()
# below), which for Game-Factory-backed adapters (draft.py) calls into
# game_factory itself, and for direct-query adapters (qb_season.py,
# championship.py) does not touch it at all. game_factory.py itself remains
# completely unmodified either way.

PACKAGE_SCHEMA_VERSION = "0.1"
ID_START = 600000  # new, previously-unused Engine ID block -- 100000s/200000s/300000s/400000s/500000s are taken

# Which Director-recognized predicates already have a proven Reads adapter.
# Deliberately narrow -- extending this registry (not writing a generic query
# engine) is exactly how a second domain should be added later.
ADAPTER_REGISTRY = {
    "DRAFTED_BY": draft_adapter,
}

# Exactly which checks this pipeline runs, in order -- recorded verbatim into
# every package so nobody has to guess what "QA'd" means here.
QA_CHECKS_PERFORMED = [
    "game_director.interpret() -> game_factory.feasibility() must be SUPPORTED",
    "spec.mechanic must be 'guess' (only mechanic with a Reads-renderable adapter today)",
    "spec.relationship_predicate must be a registered, previously-proven adapter",
    "adapter.safety_check() -- production-safety gate (data_coverage / row-level provenance)",
    "game_factory.qa_candidate() -- Engine's own candidate QA (missing-answer, duplicate-label checks)",
    "adapter row-level identity/provenance check (verification_status + approved source_id)",
    "season-aware franchise/team identity resolution (team_aliases, including the Pilot #1 safe-fix corrections)",
    "distractor construction restricted to real, season-matched Engine data (never arbitrary names)",
    "duplicate-entity guard (no player repeated within one package)",
    "duplicate-question guard",
    "contract validation: exactly 4 unique options",
    "contract validation: correctIndex points at the verified correct answer",
    "contract validation: category is an existing Reads Quiz category",
    "contract validation: difficulty in {Easy, Medium, Hard}",
    "contract validation: notes is a string (never invented flavor text)",
    "duplicate-ID check across the exported package",
]
# quality_intelligence.py was NOT used to build this package. Its own output
# tables (puzzle_quality_audits, mode_quality_metrics, qa_truth_claims, etc.)
# are empty in this database -- see GAME_DIRECTOR_PRODUCTION_INTEGRATION_PLAN.md
# -- so claiming its certification here would be false. If a future milestone
# wires it in, it must appear in this list only once actually executed.


def interpret_and_gate(request_text: str) -> dict:
    """Reuses game_director.interpret() (unmodified) for the parse + feasibility
    step, then applies this milestone's two hard gates. Never raises for an
    unsupported request -- always returns a structured result."""
    parsed = GD.interpret(request_text)  # writes to game_director_requests, as designed
    spec = parsed["spec"]
    feas = parsed["feasibility"]
    result = {
        "request_text": request_text,
        "director_request_id": parsed["request_id"],
        "parsed_spec": spec,
        "feasibility": feas,
    }
    if feas.get("status") != "SUPPORTED":
        result["gate_status"] = "BLOCKED_INFEASIBLE"
        result["gate_reason"] = feas.get("reason") or f"feasibility status was {feas.get('status')}"
        return result
    if spec.get("mechanic") != "guess":
        result["gate_status"] = "BLOCKED_MECHANIC_NOT_SUPPORTED"
        result["gate_reason"] = (
            f"mechanic '{spec.get('mechanic')}' has no Reads-renderable adapter yet "
            f"(only 'guess' does in v0.1 -- see GAME_DIRECTOR_PRODUCTION_INTEGRATION_PLAN.md)"
        )
        return result
    predicate = spec.get("relationship_predicate")
    adapter = ADAPTER_REGISTRY.get(predicate)
    if not adapter:
        result["gate_status"] = "BLOCKED_NO_ADAPTER"
        result["gate_reason"] = (
            f"predicate '{predicate}' has no registered Reads adapter yet "
            f"(registered: {sorted(ADAPTER_REGISTRY)})"
        )
        return result
    result["gate_status"] = "READY"
    result["adapter_module"] = adapter.__name__
    return result


def _engine_version_fingerprint(c) -> dict:
    """Identifies which Engine data this package was generated against.

    Originally this hashed the raw .sqlite file. That was discovered to be
    NON-deterministic across two back-to-back runs of the exact same request:
    game_director.interpret() itself writes a row to game_director_requests as
    part of its normal (unmodified) logging behavior, which changes the
    on-disk file bytes between the "before interpret()" and "after interpret()"
    read -- so a whole-file hash captured incidental logging activity, not
    actual changes to the football data. A raw file hash is fundamentally the
    wrong tool here: it can't distinguish "the draft data changed" from "some
    unrelated table got a new row." Fixed by fingerprinting only the specific,
    stable facts that actually describe the data this package was built from:
    the Engine's own semantic version and row counts for the tables this
    request's adapter reads. These do not change from a read-only interpret()
    call, so two runs of the same request now produce an identical fingerprint.
    """
    database_version = c.execute("SELECT value FROM meta WHERE key = 'database_version'").fetchone()
    return {
        "database_version": database_version[0] if database_version else None,
        "draft_facts_row_count": c.execute("SELECT COUNT(*) FROM draft_facts").fetchone()[0],
        "team_aliases_row_count": c.execute("SELECT COUNT(*) FROM team_aliases").fetchone()[0],
    }


def generate_package_from_spec(spec: dict, adapter, *, request_text: str, director_request_id: str,
                                seed: str, target_count: int = 25, id_start: int = ID_START,
                                freeze_timestamp: str | None = None,
                                difficulty_filter: str | None = None,
                                package_version: str = PACKAGE_SCHEMA_VERSION,
                                qa_checks_performed: list[str] | None = None,
                                extra_package_fields: dict | None = None) -> dict:
    """The shared generation/QA/package-construction core, factored out of
    v0.1's `generate_package()` so a v0.2+ caller with its OWN way of
    obtaining a validated spec (e.g. an LLM translator) can reuse the exact
    same deterministic generation and QA path -- not a copy of it. This is
    the only function that touches the Engine database for candidate
    generation; every caller (v0.1's regex path, v0.2's LLM-translator path)
    funnels through here.

    `difficulty_filter`: None or "any" means no filtering (v0.1's exact
    original behavior). Any other value in {"easy","medium","hard"} keeps
    only already-computed, already-QA'd candidates whose natural
    `difficulty` matches -- this NEVER changes what a candidate's difficulty
    IS, it only selects among candidates that already passed every other
    check, so it adds no new trust surface.

    `extra_package_fields`: merged into the returned package dict (appended
    after `_diagnostics`) -- lets a caller like v0.2 attach its own
    provenance (e.g. `translator`) without this function needing to know
    about v0.2 at all. None/empty changes nothing about v0.1's output.
    """
    c = engine.connect()
    safety = adapter.safety_check(c)
    engine_version_fingerprint = _engine_version_fingerprint(c)

    # Candidate sourcing is delegated ENTIRELY to the adapter -- exactly the
    # same `adapter.fetch_ordered_candidates(c, seed)` interface
    # `tools/quiz_export/core.py`'s `run_export()` already uses for every
    # pilot. This was changed from an earlier version of this function that
    # called `game_factory.generate_candidates(spec, ...)` directly: that
    # only works for a predicate Game Factory itself knows about (true for
    # DRAFTED_BY, where draft.py's own `fetch_ordered_candidates()` is
    # ITSELF a thin wrapper around that same Game Factory call using an
    # identical spec -- empirically verified byte-identical raw_rows, see
    # GAME_DIRECTOR_V03_REPORT.md). It is NOT true for QB/Season or
    # Championship, which have no Game Factory predicate at all and query
    # Engine tables directly. Delegating to the adapter uniformly is both
    # more correct (works for every adapter, not just Game-Factory-backed
    # ones) and more honest about where candidates actually come from.
    raw_rows = adapter.fetch_ordered_candidates(c, seed)
    considered = len(raw_rows)

    rejected_counts: Counter = Counter()
    accepted: list[dict] = []
    guard = duplicates.DuplicateGuard(track_entity=getattr(adapter, "TRACK_ENTITY", True))
    rng = engine.seeded(f"{seed}:distractors")

    for raw in raw_rows:
        result = adapter.evaluate(c, raw, rng, guard)  # reused verbatim -- same function proven in 3 pilots
        if isinstance(result, str):
            rejected_counts[result] += 1
            continue
        result["id"] = id_start + len(accepted)
        accepted.append(result)
        entity_key = result.get("_audit", {}).get("entity_key")
        guard.record(result["question"], entity_key)

    c.close()

    accepted_for_export = accepted
    if difficulty_filter and difficulty_filter != "any":
        accepted_for_export = [q for q in accepted if q["difficulty"].lower() == difficulty_filter.lower()]
        rejected_counts["DIFFICULTY_FILTER_MISMATCH"] = len(accepted) - len(accepted_for_export)

    exported = accepted_for_export[:target_count]
    shortfall_reason = None
    if len(exported) < target_count:
        filter_clause = f" matching difficulty '{difficulty_filter}'" if difficulty_filter and difficulty_filter != "any" else ""
        shortfall_reason = (
            f"Only {len(accepted_for_export)} candidates{filter_clause} passed every validation rule within a "
            f"{draft_adapter.CANDIDATE_LIMIT}-candidate deterministic sample; exported the "
            f"maximum available ({len(accepted_for_export)}) rather than loosen any rule to reach {target_count}."
        )

    contract_failures = contract.validate_all(exported, adapter.CATEGORY)
    dup_questions = duplicates.find_duplicates(exported, lambda q: q["question"])
    dup_ids = duplicates.find_duplicates(exported, lambda q: q["id"])

    funnel = {
        "considered": considered,
        "rejected_counts": dict(rejected_counts),
        "accepted_total": len(accepted),
        "exported_count": len(exported),
        "target_count": target_count,
        "shortfall_reason": shortfall_reason,
    }

    questions = []
    for q in exported:
        a = q["_audit"]
        questions.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "correctIndex": q["correctIndex"],
            "answer": q["options"][q["correctIndex"]],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "notes": q["notes"],
            "source_ids": {
                "player_key": a.get("player_key"),
                "draft_team_code": a.get("draft_team_code"),
                "draft_season": a.get("draft_season"),
                "franchise_id": a.get("franchise_id"),
            },
            "provenance": {
                "verification_status": a.get("verification_status"),
                "source_id": a.get("source_id"),
                "difficulty_score": a.get("difficulty_score"),
                "difficulty_band": a.get("difficulty_band"),
                "engine_qa_issues": a.get("engine_qa_issues"),
            },
        })

    by_difficulty = Counter(q["difficulty"] for q in questions)
    package_id = "GGP:" + hashlib.sha256(
        f"{request_text}|{seed}|{spec.get('relationship_predicate')}".encode()
    ).hexdigest()[:24]

    package = {
        "package_id": package_id,
        "package_version": package_version,
        "requested_description": request_text,
        "director_request_id": director_request_id,
        "parsed_spec": spec,
        "mechanic": spec.get("mechanic"),
        "game_title": f"{adapter.CATEGORY}: Guess the {str(spec.get('object_type') or 'Answer').capitalize()}",
        "game_instructions": (
            f"You'll be shown a fact from {adapter.CATEGORY}. "
            f"Pick the correct {spec.get('object_type') or 'answer'} from four options."
        ),
        "generated_at": freeze_timestamp or datetime.now(timezone.utc).isoformat(),
        "engine_version": {
            "db_path": str(ENGINE_DIR / "reads_football_v4.0.sqlite"),
            **engine_version_fingerprint,
        },
        "source_domains": [safety.get("domain_id")] if "domain_id" in safety else [safety.get("source_id")],
        "production_safety": safety,
        "qa_status": "PASSED" if not contract_failures else "FAILED",
        "qa_checks_performed": qa_checks_performed if qa_checks_performed is not None else QA_CHECKS_PERFORMED,
        "difficulty_distribution": dict(by_difficulty),
        "question_count": len(questions),
        "questions": questions,
        "funnel": funnel,
        "review_status": "UNREVIEWED",
        "_diagnostics": {
            "contract_failures": contract_failures,
            "dup_questions": dup_questions,
            "dup_ids": dup_ids,
            "seed": seed,
        },
    }
    if extra_package_fields:
        package.update(extra_package_fields)
    return package


def generate_package(request_text: str, *, seed: str, target_count: int = 25,
                      id_start: int = ID_START, freeze_timestamp: str | None = None) -> dict:
    """Returns the full GeneratedGamePackage dict, or a small BLOCKED_* result
    dict if the request doesn't clear the gates (never raises, never fakes support).

    v0.1's original regex-based path: `interpret_and_gate()` for the parse
    step, then `generate_package_from_spec()` for everything after. Source
    candidates from the ACTUAL Director-parsed spec (not the adapter's own
    hardcoded _SPEC) -- confirmed identical in content for this milestone's
    chosen request (see GAME_DIRECTOR_V01_REPORT.md), but using the real
    parsed spec means any request-specific filters are genuinely honored,
    not silently dropped.
    """
    gate = interpret_and_gate(request_text)
    if gate["gate_status"] != "READY":
        return {
            "package_id": None,
            "status": gate["gate_status"],
            "reason": gate["gate_reason"],
            "director_request_id": gate["director_request_id"],
            "parsed_spec": gate["parsed_spec"],
            "feasibility": gate["feasibility"],
        }

    adapter = ADAPTER_REGISTRY[gate["parsed_spec"]["relationship_predicate"]]
    spec = gate["parsed_spec"]

    return generate_package_from_spec(
        spec, adapter,
        request_text=request_text, director_request_id=gate["director_request_id"],
        seed=seed, target_count=target_count, id_start=id_start, freeze_timestamp=freeze_timestamp,
    )


def write_package(path: Path, package: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(package, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Director v0.1 -- generate one GeneratedGamePackage")
    ap.add_argument("request", help="Natural-language game request")
    ap.add_argument("--seed", default="director-v01-drafted-by-guess")
    ap.add_argument("--count", type=int, default=25)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pkg = generate_package(a.request, seed=a.seed, target_count=a.count)
    if a.out:
        write_package(Path(a.out), pkg)
        print(f"Wrote {a.out}")
    print(json.dumps({k: v for k, v in pkg.items() if k != "questions"}, indent=2, default=str)[:3000])


if __name__ == "__main__":
    main()
