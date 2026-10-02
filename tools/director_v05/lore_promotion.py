"""Promotion policy for Deep Lore.

This module never changes public configuration. It only turns a real
certification result into an explicit pass/fail decision operators can inspect
before making a separate code change to expose the mode.
"""
from __future__ import annotations

from .certify_deep_lore_delivery import certify

MIN_PACKAGES_PER_BAND = 10
MIN_QUESTIONS_PER_PACKAGE = 3


def assess_public_promotion(*, seeds_per_band=MIN_PACKAGES_PER_BAND,
                            target_count=MIN_QUESTIONS_PER_PACKAGE):
    report = certify(
        seeds_per_band=seeds_per_band,
        target_count=target_count,
    )

    reasons = []
    expected = int(seeds_per_band) * 3
    if report.get("status") != "PASSED":
        reasons.append("CERTIFICATION_FAILED")
    if report.get("passed_packages") != expected:
        reasons.append("NOT_ALL_PACKAGES_PASSED")
    if report.get("failures"):
        reasons.append("CERTIFICATION_FAILURES_PRESENT")
    if int(seeds_per_band) < MIN_PACKAGES_PER_BAND:
        reasons.append("SAMPLE_TOO_SMALL")
    if int(target_count) < MIN_QUESTIONS_PER_PACKAGE:
        reasons.append("QUESTION_COUNT_TOO_SMALL")

    return {
        "mode": "deep_lore_guess",
        "promotion_ready": not reasons,
        "reasons": reasons,
        "policy": {
            "required_bands": ["easy", "medium", "hard"],
            "minimum_packages_per_band": MIN_PACKAGES_PER_BAND,
            "minimum_questions_per_package": MIN_QUESTIONS_PER_PACKAGE,
            "requires_zero_failures": True,
            "automatic_public_promotion": False,
        },
        "certification": report,
    }


def main():
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-per-band", type=int, default=MIN_PACKAGES_PER_BAND)
    ap.add_argument("--target-count", type=int, default=MIN_QUESTIONS_PER_PACKAGE)
    args = ap.parse_args()

    result = assess_public_promotion(
        seeds_per_band=args.seeds_per_band,
        target_count=args.target_count,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["promotion_ready"] else 1)


if __name__ == "__main__":
    main()
