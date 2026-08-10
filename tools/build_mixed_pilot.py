#!/usr/bin/env python3
"""Build the 300-question mixed Engine pack (Step 5 of the framework refactor).

Runs all three domain adapters through the shared quiz_export framework --
NOT a concatenation of the existing per-domain .js files -- and combines
their outputs into a single new export. Each domain's slice reuses that
domain's own original seed (reads-quiz-engine-pilot-v1 /
reads-quiz-engine-qb-pilot-v1 / reads-quiz-engine-championship-award-pilot-v1),
so the underlying 100-question selection per domain is expected to be the
existing pilots' own selection, just re-numbered into the mixed pack's own
ID range: Draft 500000-500099, QB 500100-500199, Championship 500200-500299.

Does not touch data/quiz-engine-pilot-v2.js, quiz-engine-qb-pilot.js, or
quiz-engine-championship-award-pilot.js -- each adapter's per-domain
generation here writes to a throwaway temp path, discarded after its
`exported` list is captured; only the combined mixed file is written for
real.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.quiz_export import core, engine, contract, duplicates, serializer, audit
from tools.quiz_export.adapters import draft, qb_season, championship

OUT_PATH = engine.DATA_DIR / "quiz-engine-mixed-pilot.js"
FUNNEL_STATS_PATH = engine.BACKUPS_DIR / "mixed_pilot_funnel_stats.json"
GLOBAL_NAME = "QUIZ_DATA_ENGINE_MIXED_PILOT"
TARGET_PER_DOMAIN = 100

DOMAIN_SLICES = [
    ("draft", draft, 500000),
    ("qb_season", qb_season, 500100),
    ("championship", championship, 500200),
]


def header_lines():
    return [
        "// AUTO-GENERATED MIXED ENGINE PACK -- do not hand-edit.",
        "// Produced by tools/build_mixed_pilot.py via the shared tools/quiz_export",
        "// framework, running the Draft, QB/Season, and Championship/Postseason",
        "// domain adapters through one shared pipeline (not a concatenation of the",
        "// three existing per-domain pilot files).",
        "//",
        "// 100 questions per domain, each domain's slice using that domain's own",
        "// original deterministic seed. ID ranges: Draft 500000-500099,",
        "// QB/Season 500100-500199, Championship/Postseason 500200-500299.",
        "//",
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or",
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_MIXED_PILOT,",
        "// distinct from window.QUIZ_DATA and every other pilot global.",
        "//",
        "// See QUIZ_ENGINE_MIXED_PILOT_REPORT.md for the full audit trail.",
    ]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        per_domain = {}
        for name, adapter, id_start in DOMAIN_SLICES:
            result = core.run_export(
                adapter,
                out_path=tmp_dir / f"{name}.js",
                id_start=id_start,
                target_count=TARGET_PER_DOMAIN,
            )
            per_domain[name] = result
            print(f"--- {name} (mixed slice, id_start={id_start}) ---")
            core.print_summary(result)

    combined = []
    for name, adapter, id_start in DOMAIN_SLICES:
        combined.extend(per_domain[name]["exported"])

    # Global (cross-domain) contract validation -- each record checked
    # against ITS OWN domain's approved category, not one shared constant.
    contract_failures = []
    for name, adapter, id_start in DOMAIN_SLICES:
        contract_failures.extend(contract.validate_all(per_domain[name]["exported"], adapter.CATEGORY))

    dup_questions = duplicates.find_duplicates(combined, lambda q: q["question"])
    dup_ids = duplicates.find_duplicates(combined, lambda q: q["id"])

    serializer.write_quiz_js(OUT_PATH, GLOBAL_NAME, header_lines(), combined)

    summary = {
        "target_total": 3 * TARGET_PER_DOMAIN,
        "exported_total": len(combined),
        "by_domain": {
            name: {
                "considered": per_domain[name]["considered"],
                "rejected": sum(per_domain[name]["rejected_counts"].values()),
                "accepted": len(per_domain[name]["accepted"]),
                "exported": len(per_domain[name]["exported"]),
                "id_range": [id_start, id_start + TARGET_PER_DOMAIN - 1],
                "rejected_counts": dict(per_domain[name]["rejected_counts"]),
            }
            for name, adapter, id_start in DOMAIN_SLICES
        },
        "dup_questions_cross_domain": dup_questions,
        "dup_ids_cross_domain": dup_ids,
        "contract_failures": contract_failures,
        "contract_passed": len(contract_failures) == 0,
    }
    audit.write_json(FUNNEL_STATS_PATH, summary)

    print()
    print(f"Combined exported: {len(combined)} / {3 * TARGET_PER_DOMAIN}")
    print(f"Cross-domain duplicate questions: {len(dup_questions)}")
    print(f"Cross-domain duplicate IDs: {len(dup_ids)}")
    print(f"Contract failures: {len(contract_failures)}")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {FUNNEL_STATS_PATH}")

    return per_domain, combined


if __name__ == "__main__":
    main()
