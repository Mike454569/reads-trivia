"""Funnel/audit statistics: shared shape, domain-specific extras merged in."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def build_base_funnel_stats(
    *, seed, considered, rejected_counts: Counter, accepted, exported,
    contract_failures, dup_questions, dup_ids,
) -> dict:
    by_category = Counter(q["category"] for q in exported)
    by_difficulty = Counter(q["difficulty"] for q in exported)
    return {
        "seed": seed,
        "considered": considered,
        "rejected_counts": dict(rejected_counts),
        "total_rejected": sum(rejected_counts.values()),
        "accepted_total": len(accepted),
        "exported_count": len(exported),
        "accepted_but_not_exported": max(0, len(accepted) - len(exported)),
        "category_distribution": dict(by_category),
        "difficulty_distribution": dict(by_difficulty),
        "dup_questions": dup_questions,
        "dup_ids": dup_ids,
        "contract_failures": contract_failures,
        "contract_passed": len(contract_failures) == 0,
    }


def write_json(path: Path, stats: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
