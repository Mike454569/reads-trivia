"""Certification runner for deep-lore delivery before public promotion."""
from __future__ import annotations

from collections import Counter

from tools.director_v02.package_contract import validate_package_contract

from .lore_package import build_package

BANDS = ("easy", "medium", "hard")


def certify(*, seeds_per_band=10, target_count=3):
    seeds_per_band = max(1, min(int(seeds_per_band), 100))
    target_count = max(1, min(int(target_count), 25))

    counts = Counter()
    failures = []
    examples = []

    for band in BANDS:
        for i in range(seeds_per_band):
            seed = f"deep-lore-cert:{band}:{i}"
            try:
                package = build_package(
                    seed=seed,
                    target_count=target_count,
                    difficulty=band,
                )
            except Exception as exc:
                counts[f"{band}:EXCEPTION"] += 1
                failures.append({
                    "band": band,
                    "seed": seed,
                    "reason": type(exc).__name__ + ":" + str(exc),
                })
                continue

            violations = validate_package_contract(package)
            if package.get("qa_status") != "PASSED":
                violations.append("qa_status was not PASSED")
            if package.get("question_count", 0) < target_count:
                violations.append(
                    f"shortfall: requested {target_count}, got {package.get('question_count', 0)}"
                )

            for q in package.get("questions") or []:
                options = q.get("options") or []
                answer = str(q.get("answer") or "")
                if len(options) != 4:
                    violations.append(f"{q.get('id')}: expected exactly four options")
                if options.count(answer) != 1:
                    violations.append(f"{q.get('id')}: answer does not appear exactly once")
                clues = q.get("clues") or []
                if len(clues) < 3:
                    violations.append(f"{q.get('id')}: fewer than three clues")
                copy = " ".join([str(q.get("question") or "")] + [str(x) for x in clues]).casefold()
                if any(term in copy for term in (
                    "verified chain", "structured fact", "subject of event",
                    "selected by rarity rules", "strangest verified moment",
                )):
                    violations.append(f"{q.get('id')}: robotic/internal wording leaked")

            if violations:
                counts[f"{band}:FAILED"] += 1
                failures.append({
                    "band": band,
                    "seed": seed,
                    "violations": violations,
                })
            else:
                counts[f"{band}:PASSED"] += 1
                if len(examples) < 9:
                    q = package["questions"][0]
                    examples.append({
                        "band": band,
                        "package_id": package["package_id"],
                        "question": q["question"],
                        "clues": q["clues"],
                        "options": q["options"],
                    })

    passed = sum(counts[f"{band}:PASSED"] for band in BANDS)
    expected = seeds_per_band * len(BANDS)
    return {
        "status": "PASSED" if passed == expected and not failures else "FAILED",
        "expected_packages": expected,
        "passed_packages": passed,
        "counts": dict(counts),
        "failures": failures[:50],
        "examples": examples,
        "public_promotion_ready": passed == expected and not failures,
    }


def main():
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-per-band", type=int, default=10)
    ap.add_argument("--target-count", type=int, default=3)
    args = ap.parse_args()
    print(json.dumps(
        certify(
            seeds_per_band=args.seeds_per_band,
            target_count=args.target_count,
        ),
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
