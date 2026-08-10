#!/usr/bin/env python3
"""Generate the production NFL Draft History Engine data file.

Runs the already-approved Draft adapter through the shared tools/quiz_export
framework -- the exact same pipeline that produced data/quiz-engine-pilot-v2.js
and the Draft slice of data/quiz-engine-mixed-pilot.js -- with the permanent
Engine ID namespace (500000+) reserved for production use. No question is
hand-written or hand-edited; this script only calls the existing adapter and
serializes its output.

Output: data/quiz-engine-draft-production.js, window.QUIZ_DATA_ENGINE_DRAFT.
Same seed as every other Draft export ("reads-quiz-engine-pilot-v1"), so the
100 questions are expected to be identical (content-wise) to
quiz-engine-pilot-v2.js and the mixed pack's Draft slice -- only the ID range
and file/global name are production-specific. This is verified, not assumed
-- see the generated report.

Does not modify the Draft adapter, the shared framework, or any other
existing Engine output file.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.quiz_export import core, contract
from tools.quiz_export.adapters import draft

OUT_PATH = draft.engine.DATA_DIR / "quiz-engine-draft-production.js"
GLOBAL_NAME = "QUIZ_DATA_ENGINE_DRAFT"
ID_START = 500000  # permanent Engine namespace, matching the mixed pack's Draft slice
TARGET_COUNT = 100


def header_lines(seed: str) -> list[str]:
    return [
        "// PRODUCTION Engine data file -- do not hand-edit.",
        "// Produced by tools/generate_quiz_engine_draft_production.py, which runs the",
        "// already-approved Draft domain adapter (tools/quiz_export/adapters/draft.py)",
        "// through the shared tools/quiz_export framework. Same content pipeline as",
        "// data/quiz-engine-pilot-v2.js and the Draft slice of",
        "// data/quiz-engine-mixed-pilot.js -- this file exists so production can load a",
        "// single, clearly-named, namespaced Draft data file independent of those two.",
        "//",
        f"// Deterministic seed: \"{seed}\". Rerunning this script against an unchanged",
        "// database reproduces this file byte-for-byte.",
        "//",
        "// ID namespace: 500000-500099 -- the permanent Engine content range, reserved",
        "// so these can never collide with data/quiz.js's hand-authored IDs (1-533) or",
        "// any future hand-authored addition (policy: hand-authored content stays under",
        "// 100000; each Engine domain gets its own reserved 100000 block).",
        "//",
        "// See QUIZ_ENGINE_PRODUCTION_ROLLOUT_REPORT.md for the full rollout audit.",
    ]


def main():
    result = core.run_export(
        draft,
        out_path=OUT_PATH,
        id_start=ID_START,
        target_count=TARGET_COUNT,
    )
    # run_export already validated the contract and wrote OUT_PATH once using
    # the adapter's own default GLOBAL_NAME/header (needed since run_export's
    # interface always writes as part of the pipeline). Overwrite with the
    # production-specific global name and header -- same `exported` list,
    # same already-validated content, only the presentation differs.
    from tools.quiz_export import serializer
    serializer.write_quiz_js(OUT_PATH, GLOBAL_NAME, header_lines(draft.SEED), result["exported"])

    core.print_summary(result)
    fs = result["funnel_stats"]
    print(f"Contract failures: {len(fs['contract_failures'])}")
    print(f"Category: {fs['category_distribution']}")
    print(f"Difficulty: {fs['difficulty_distribution']}")
    print(f"Wrote {OUT_PATH} as window.{GLOBAL_NAME}")
    return result


if __name__ == "__main__":
    main()
