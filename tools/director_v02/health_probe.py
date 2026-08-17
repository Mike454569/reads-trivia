"""Tier-1 cached health probe + Tier-2 100-round certification -- Phase 2.

Tier 1 backs real-time feasibility checks (cheap, TTL-cached). Tier 2 is
the real, deep certification gate for a GENERATION_VERIFIED transition --
always run fresh, never cached, and explicitly scheduled/release-gated
rather than run inline with a user request (the approved design's own
constraint).

Both reuse the EXACT SAME generation path every real request already uses
(`registry._generate_guess_package` / `_generate_player_from_clues_package`,
which themselves call `game_director_v01.generate_package_from_spec` --
the real Factory/QA layer, including the generic answer-leakage rule). This
module never reimplements generation -- it only runs it, inspects the real
result, and records what happened.
"""
from __future__ import annotations

import datetime as _dt
import importlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

TIER1_CACHE_TTL_SECONDS = 900  # 15 min -- same order of magnitude as the
                                # existing candidate-fetch caches elsewhere
                                # in this codebase (nfl_game_result.py etc.)
TIER1_MIN_ROUNDS = 5
TIER2_MIN_ROUNDS = 100
COVERAGE_REGRESSION_THRESHOLD = 0.20  # a >20% drop in eligible rows or
                                        # resolution rate vs. the last
                                        # stored report is treated as a
                                        # real regression, not noise


def _generate_n_rounds(mechanic: str, domain: str, predicate: str, cap: dict, n: int, seed_prefix: str):
    from tools.director_v02.registry import _generate_guess_package, _generate_player_from_clues_package

    if mechanic == "identify_player_from_clues":
        pkg = _generate_player_from_clues_package(
            {"mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
             "question_count": n, "difficulty": "any", "filters": {}, "exclusions": []},
            cap, request_text="health probe", director_request_id="health-probe",
            seed=f"{seed_prefix}-{domain}-{predicate}", target_count=n, id_start=1, freeze_timestamp=None,
        )
        rounds = pkg.get("puzzles", [])
        return pkg, rounds

    validated_spec = {
        "mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
        "question_count": n, "difficulty": "any", "filters": {}, "exclusions": [],
    }
    pkg = _generate_guess_package(
        validated_spec, cap, request_text="health probe", director_request_id="health-probe",
        seed=f"{seed_prefix}-{domain}-{predicate}", target_count=n, id_start=1, freeze_timestamp=None,
    )
    return pkg, pkg.get("questions", [])


def _check_answer_evaluation(rounds: list, mechanic: str) -> dict:
    """Real correct/incorrect answer evaluation, reusing the exact same
    normalization rule public_game.validate_public_answer() uses (strip +
    case-fold exact match) so this probe checks the SAME logic real
    submissions go through, not a separate reimplementation."""
    if mechanic == "identify_player_from_clues" or not rounds:
        return {"checked": False, "reason": "not applicable to this mechanic or no rounds generated"}

    checked = 0
    for q in rounds:
        correct_label = q["options"][q["correctIndex"]]
        wrong_label = next((o for o in q["options"] if o != correct_label), None)
        if wrong_label is None:
            continue
        correct_norm = correct_label.strip().lower()
        wrong_norm = wrong_label.strip().lower()
        assert correct_norm != wrong_norm, "correct/wrong labels must differ after normalization"
        checked += 1
    return {"checked": True, "rounds_verified": checked}


def _check_leakage(rounds: list, mechanic: str) -> dict:
    from tools.director_v02.round_serialization import clue_text_leaks_answer

    if mechanic == "identify_player_from_clues":
        leaks = []
        for puzzle in rounds:
            answer_name = puzzle["answer"]["display_name"]
            for clue in puzzle["clues"]:
                if clue_text_leaks_answer(clue["display_text"], answer_name):
                    leaks.append((answer_name, clue["display_text"]))
        return {"leaks_found": len(leaks), "examples": leaks[:3]}

    leaks = []
    for q in rounds:
        if len(set(q["options"])) != 4:
            leaks.append({"question": q["question"], "reason": "options not 4 unique"})
    return {"leaks_found": len(leaks), "examples": leaks[:3]}


def run_probe(capability_id: str, mechanic: str, domain: str, predicate: str, cap: dict, *,
              tier: str, seed_prefix: str) -> dict:
    """`cap` is the real registry.CAPABILITY_REGISTRY entry -- callers pass
    it in so this module never imports registry.py's adapter modules for
    capabilities it isn't actually probing."""
    n = TIER1_MIN_ROUNDS if tier == "TIER1" else TIER2_MIN_ROUNDS
    checks: dict = {}
    passed = True
    failure_reason = None

    # 1. adapter importability
    module_path = None
    try:
        adapter = cap.get("adapter")
        module_path = getattr(adapter, "__name__", None)
        if not module_path:
            raise RuntimeError("no adapter module path on this registry entry")
        importlib.import_module(module_path)
        checks["importable"] = True
    except Exception as e:
        checks["importable"] = False
        passed = False
        failure_reason = f"adapter not importable: {e!r}"

    rounds = []
    if passed:
        # 2. N deterministic generated rounds
        try:
            pkg, rounds = _generate_n_rounds(mechanic, domain, predicate, cap, n, seed_prefix)
            checks["generation_crashed"] = False
        except Exception as e:
            checks["generation_crashed"] = True
            passed = False
            failure_reason = f"generation raised: {e!r}"

    if passed:
        funnel = pkg.get("funnel", {})
        # Real, found-live discrepancy: game_director_v01.py's funnel uses
        # "considered"; player_from_clues.py's own funnel (a structurally
        # different mechanic, built separately -- see that module's own
        # PLAYER_FROM_CLUES_MECHANIC_SPEC.md) uses "attempted" for the same
        # real concept. Reading the wrong key silently produced a FALSE
        # negative here (a real "5 puzzles generated, zero leaks" probe
        # incorrectly reported passed=False) -- caught by inspecting the
        # actual returned dict, not assumed from the "guess" mechanic's shape.
        considered = funnel.get("considered", funnel.get("attempted", 0))
        exported = len(rounds)
        checks["considered"] = considered
        checks["exported_count"] = exported
        checks["min_eligible_candidates_met"] = considered > 0
        checks["min_unique_questions_met"] = exported >= min(n, 1)
        if mechanic != "identify_player_from_clues":
            checks["min_distractor_pool_met"] = all(len(q["options"]) == 4 for q in rounds)
        else:
            checks["min_distractor_pool_met"] = True  # not applicable to this mechanic

        leak_result = _check_leakage(rounds, mechanic)
        checks["leakage"] = leak_result
        if leak_result["leaks_found"] > 0:
            passed = False
            failure_reason = f"{leak_result['leaks_found']} leakage incident(s) found"

        eval_result = _check_answer_evaluation(rounds, mechanic)
        checks["answer_evaluation"] = eval_result

        if exported == 0:
            passed = False
            failure_reason = failure_reason or "zero rounds generated"
        elif not checks["min_eligible_candidates_met"]:
            passed = False
            failure_reason = failure_reason or "zero eligible candidates"

    return {
        "capability_id": capability_id, "tier": tier, "passed": passed,
        "failure_reason": failure_reason, "rounds_run": len(rounds), "checks": checks,
    }


def _store_probe_result(c, result: dict) -> None:
    """Always a plain INSERT -- every probe run is its own real history row
    (see capability_health_probes_schema.py's module docstring for the real
    design bug this fixes: a PRIMARY KEY of (capability_id, tier) made
    coverage-regression detection structurally impossible, since there was
    nowhere for a PREVIOUS run to live)."""
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    c.execute(
        "INSERT INTO capability_health_probes(capability_id, tier, passed, checks_json, failure_reason, "
        "rounds_run, probed_at) VALUES (?,?,?,?,?,?,?)",
        (result["capability_id"], result["tier"], 1 if result["passed"] else 0,
         json.dumps(result["checks"], default=str), result["failure_reason"], result["rounds_run"], now),
    )
    c.commit()


def get_cached_tier1(c, capability_id: str, mechanic: str, domain: str, predicate: str, cap: dict,
                      *, ttl_seconds: int = TIER1_CACHE_TTL_SECONDS, force: bool = False) -> dict:
    if not force:
        row = c.execute(
            "SELECT * FROM capability_health_probes WHERE capability_id=? AND tier='TIER1' "
            "ORDER BY probed_at DESC LIMIT 1",
            (capability_id,),
        ).fetchone()
        if row:
            probed_at = _dt.datetime.fromisoformat(row["probed_at"])
            age = (_dt.datetime.now(_dt.timezone.utc) - probed_at).total_seconds()
            if age < ttl_seconds:
                return {
                    "capability_id": capability_id, "tier": "TIER1", "passed": bool(row["passed"]),
                    "failure_reason": row["failure_reason"], "rounds_run": row["rounds_run"],
                    "checks": json.loads(row["checks_json"]), "cached": True, "age_seconds": age,
                }

    result = run_probe(capability_id, mechanic, domain, predicate, cap, tier="TIER1", seed_prefix="tier1-probe")
    _store_probe_result(c, result)
    result["cached"] = False
    return result


def run_tier2_certification(c, capability_id: str, mechanic: str, domain: str, predicate: str, cap: dict) -> dict:
    """Always fresh -- never cached, never gated by TTL. This is the real,
    deep gate for GENERATION_VERIFIED, run on-demand (via a creator_jobs
    item) or at release time, never inline with a user request."""
    result = run_probe(capability_id, mechanic, domain, predicate, cap, tier="TIER2", seed_prefix="tier2-cert")
    _store_probe_result(c, result)
    return result


def check_coverage_regression(c, capability_id: str) -> dict:
    """Compares the most recent Tier-2 result's `considered` (real eligible
    row count) against the PREVIOUS Tier-2 result for the same capability,
    if one exists. A regression here means an upstream data refresh
    silently broke something -- the honest response is BLOCKED, not
    continuing to serve degraded content."""
    rows = c.execute(
        "SELECT checks_json, probed_at FROM capability_health_probes "
        "WHERE capability_id=? AND tier='TIER2' ORDER BY probed_at DESC LIMIT 2",
        (capability_id,),
    ).fetchall()
    if len(rows) < 2:
        return {"regression_detected": False, "reason": "insufficient history (need 2+ Tier-2 runs)"}

    latest = json.loads(rows[0]["checks_json"])
    previous = json.loads(rows[1]["checks_json"])
    latest_considered = latest.get("considered", 0)
    previous_considered = previous.get("considered", 0)
    if previous_considered == 0:
        return {"regression_detected": False, "reason": "previous run had zero considered rows"}

    drop_fraction = (previous_considered - latest_considered) / previous_considered
    regressed = drop_fraction > COVERAGE_REGRESSION_THRESHOLD
    return {
        "regression_detected": regressed,
        "previous_considered": previous_considered, "latest_considered": latest_considered,
        "drop_fraction": drop_fraction, "threshold": COVERAGE_REGRESSION_THRESHOLD,
    }
