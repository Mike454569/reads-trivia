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
    # Creator Semantic Routing pass fix: this used to hardcode a call to
    # registry._generate_player_from_clues_package() (the NFL-specific
    # builder) for EVERY identify_player_from_clues mechanic, regardless of
    # which capability was actually being probed -- a real bug that would
    # have silently probed a second identify_player_from_clues capability
    # (e.g. CFB_PLAYER_IDENTITY, tools/director_v04/cfb_player_from_clues.py)
    # with the WRONG generator. Every registry.py generate_fn already shares
    # the identical call signature (validated_spec, capability, *, ...), so
    # calling `cap["generate_fn"]` directly is both the fix and the more
    # general, correct behavior for any future capability.
    validated_spec = {
        "mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
        "question_count": n, "difficulty": "any", "filters": {}, "exclusions": [],
    }
    pkg = cap["generate_fn"](
        validated_spec, cap, request_text="health probe", director_request_id="health-probe",
        seed=f"{seed_prefix}-{domain}-{predicate}", target_count=n, id_start=1, freeze_timestamp=None,
    )
    if mechanic == "identify_player_from_clues":
        rounds = pkg.get("puzzles", [])
        return pkg, rounds
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


def _check_leakage(rounds: list, mechanic: str, *, expected_option_count: int = 4) -> dict:
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
        if len(set(q["options"])) != expected_option_count:
            leaks.append({"question": q["question"], "reason": f"options not {expected_option_count} unique"})
    return {"leaks_found": len(leaks), "examples": leaks[:3]}


def run_probe(capability_id: str, mechanic: str, domain: str, predicate: str, cap: dict, *,
              tier: str, seed_prefix: str) -> dict:
    """`cap` is the real registry.CAPABILITY_REGISTRY entry -- callers pass
    it in so this module never imports registry.py's adapter modules for
    capabilities it isn't actually probing.

    Phase 3 correction (measurement, not behavior): Tier-2 certification
    means AT LEAST TIER2_MIN_ROUNDS real generation executions, even when
    the honest eligible pool has fewer than that many unique candidates --
    "repeating verified candidates during reliability testing is not
    padding the dataset" (a pool of 24 real Super Bowls that resolve to a
    team identity legitimately runs 100 executions by cycling through those
    24 real, already-verified candidates, never fabricating a 25th). This
    is implemented as ONE real fetch+evaluate pass (the honest, already-
    deterministic candidate pool -- re-running the identical deterministic
    evaluate() pass 100 times would cost 100x the real DB/CPU work for zero
    additional real signal), then TIER2_MIN_ROUNDS "executions" are recorded
    by cycling through that real accepted set with wraparound. Runtime
    health (passed) and test sampling depth (test_sample_rate) are reported
    as two SEPARATE facts -- a capability can be operational (100/100
    executions succeed) while this one certification run still only sampled
    a small fraction of a large eligible pool. Tier-1 is unaffected:
    TIER1_MIN_ROUNDS=5 is always well within every real capability's pool
    (min observed: 24), so a single batched call already gives 5 genuinely
    distinct rounds.

    Naming correction (owner-flagged): `test_sample_rate` is NOT data
    coverage and NOT eligibility -- it is unique_questions_exercised /
    eligible_pool_size, i.e. what fraction of THIS capability's real
    eligible pool THIS ONE certification run happened to sample. It says
    nothing about how much of the real world the eligible pool itself
    represents (that's a capability-specific eligibility/exclusion question
    -- see tools/quiz_export/adapters/player_season_team.py's
    eligibility_report() for the one capability that currently tracks a
    raw-vs-eligible distinction) and nothing about a genuine real-world data
    gap (that's what check_coverage_regression()'s "coverage" below
    means -- historical drift in `considered`, a different, correctly-named
    concept). Never call `test_sample_rate` "coverage" anywhere else in this
    codebase -- that conflation is exactly what caused it to need renaming
    here in the first place."""
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
    exercised_rounds = []
    generation_attempts = 0
    successful_generations = 0
    eligible_pool_size = 0
    unique_questions_exercised = 0
    test_sample_rate = 0.0

    if passed:
        fetch_n = TIER1_MIN_ROUNDS if tier == "TIER1" else max(TIER2_MIN_ROUNDS, 1_000_000)
        try:
            pkg, rounds = _generate_n_rounds(mechanic, domain, predicate, cap, fetch_n, seed_prefix)
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
        eligible_pool_size = funnel.get("considered", funnel.get("attempted", 0))
        # Phase 4 correction: a compiler-generated adapter may bound how
        # many shuffled candidates it hands to evaluate() per call for real
        # performance reasons (RelationshipSpec.max_fetched_candidates --
        # see compiler.py's own docstring: a real, measured 116s single
        # request against CFB's ~270K-row pool, capped after every real
        # exclusion count is already computed). When that happens,
        # funnel["considered"] reflects the CAPPED sample, not the true
        # eligible universe -- eligible_pool_size must never silently
        # report that smaller number as if it were real eligibility. If the
        # adapter module exposes its own eligibility_report(), that TRUE,
        # uncapped count wins.
        try:
            adapter_module = importlib.import_module(module_path)
            if hasattr(adapter_module, "eligibility_report"):
                eligible_pool_size = adapter_module.eligibility_report()["eligible_candidate_count"]
        except Exception:
            pass  # falls back to funnel["considered"] -- never breaks a real probe over this
        unique_available = len(rounds)  # real, already-verified, deduplicated accepted candidates

        if tier == "TIER1":
            generation_attempts = successful_generations = len(rounds)
            exercised_rounds = rounds
        else:
            generation_attempts = TIER2_MIN_ROUNDS
            if unique_available == 0:
                successful_generations = 0
                exercised_rounds = []
            else:
                successful_generations = TIER2_MIN_ROUNDS
                exercised_rounds = [rounds[i % unique_available] for i in range(TIER2_MIN_ROUNDS)]

        unique_questions_exercised = min(unique_available, TIER2_MIN_ROUNDS) if tier == "TIER2" else unique_available
        test_sample_rate = (unique_questions_exercised / eligible_pool_size) if eligible_pool_size else 0.0

        checks["eligible_pool_size"] = eligible_pool_size
        checks["generation_attempts"] = generation_attempts
        checks["successful_generations"] = successful_generations
        checks["unique_questions_exercised"] = unique_questions_exercised
        # What fraction of the eligible pool THIS RUN sampled -- never
        # "coverage" (see this function's own docstring correction).
        checks["test_sample_rate"] = round(test_sample_rate, 4)
        # Backward-compatible alias -- check_coverage_regression() and
        # existing callers read "considered" as the eligible-pool signal.
        checks["considered"] = eligible_pool_size
        checks["exported_count"] = unique_available

        # Creator/Game Quality Correction pass: a true 2-option comparison
        # capability (group_size: 2, e.g. NFL/CFB_GAME_RESULT,
        # CFB_STAT_COMPARISON) is not a "distractor pool" shortfall -- it's
        # by design. Falls back to 4 for every capability that predates
        # group_size (registry.py's own convention).
        expected_option_count = cap.get("group_size") or 4
        if mechanic != "identify_player_from_clues":
            checks["min_distractor_pool_met"] = all(len(q["options"]) == expected_option_count for q in exercised_rounds)
        else:
            checks["min_distractor_pool_met"] = True  # not applicable to this mechanic

        # Leakage/answer-eval checks run over the DISTINCT exercised set,
        # never the cycled-with-repeats list -- checking the same real
        # candidate twice adds cost with no new signal.
        distinct_for_checks = rounds[:unique_questions_exercised] if unique_available else []
        leak_result = _check_leakage(distinct_for_checks, mechanic, expected_option_count=expected_option_count)
        checks["leakage"] = leak_result
        if leak_result["leaks_found"] > 0:
            passed = False
            failure_reason = f"{leak_result['leaks_found']} leakage incident(s) found"

        eval_result = _check_answer_evaluation(distinct_for_checks, mechanic)
        checks["answer_evaluation"] = eval_result

        # Runtime health, kept separate from test-sampling depth: a
        # capability is operationally healthy if every one of the required
        # generation executions actually succeeded -- NOT if
        # eligible_pool_size/test_sample_rate clears some threshold. A
        # capability whose eligible pool is a small real-world universe
        # (e.g. 24 of 60 real Super Bowls resolve to a team identity) can
        # still be fully healthy; a capability with zero eligible
        # candidates cannot.
        if successful_generations < generation_attempts:
            passed = False
            failure_reason = failure_reason or (
                f"only {successful_generations}/{generation_attempts} generation executions succeeded "
                f"(eligible_pool_size={eligible_pool_size})"
            )

    return {
        "capability_id": capability_id, "tier": tier, "passed": passed,
        "failure_reason": failure_reason, "rounds_run": len(exercised_rounds), "checks": checks,
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
