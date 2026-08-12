#!/usr/bin/env python3
"""Generate the production CFB Game Results Engine data file.

The CFB mirror of tools/generate_quiz_engine_game_result_production.py --
same architecture, same shared tools/quiz_export framework, built on
tools/data_refresh/cfb_games_refresh.py's real, automatically-refreshed
`cfb_games_canonical` table (Section F: prove the same architecture works
for CFB, not a separate CFB content engine).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.quiz_export import core, serializer
from tools.quiz_export.adapters import cfb_game_result

OUT_PATH = cfb_game_result.engine.DATA_DIR / "quiz-engine-cfb-game-result-production.js"
GLOBAL_NAME = "QUIZ_DATA_ENGINE_CFB_GAME_RESULT"
SEED = "reads-quiz-engine-cfb-game-result-production-v1"
ID_START = 670000  # matches registry.py's pipeline_id_start for CFB_GAME_RESULT/WON_GAME
TARGET_COUNT = 300  # real accepted pool is 36,184 (see registry.py) -- a substantial,
                     # varied slice, matching the NFL production file's scale


def header_lines(seed: str) -> list[str]:
    return [
        "// PRODUCTION Engine data file -- do not hand-edit.",
        "// Produced by tools/generate_quiz_engine_cfb_game_result_production.py, which runs",
        "// the already-registered CFB_GAME_RESULT/WON_GAME adapter",
        "// (tools/quiz_export/adapters/cfb_game_result.py) through the shared",
        "// tools/quiz_export framework, against tools/data_refresh/cfb_games_refresh.py's",
        "// real, automatically-refreshed `cfb_games_canonical` table.",
        "//",
        f'// Deterministic seed: "{seed}". Rerunning this script after a real daily',
        "// refresh (new games ingested) picks up real new content automatically.",
        "//",
        "// ID namespace: 670000-670299 -- matches registry.py's pipeline_id_start for this domain.",
        "//",
        "// See READS_APP_WIDE_ENGINE_MIGRATION_REPORT.md for the full audit trail.",
    ]


def main():
    result = core.run_export(
        cfb_game_result,
        seed=SEED,
        out_path=OUT_PATH,
        id_start=ID_START,
        target_count=TARGET_COUNT,
    )
    serializer.write_quiz_js(OUT_PATH, GLOBAL_NAME, header_lines(SEED), result["exported"])

    core.print_summary(result)
    fs = result["funnel_stats"]
    print(f"Contract failures: {len(fs['contract_failures'])}")
    print(f"Category: {fs['category_distribution']}")
    print(f"Difficulty: {fs['difficulty_distribution']}")
    print(f"Wrote {OUT_PATH} as window.{GLOBAL_NAME}")
    return result


if __name__ == "__main__":
    main()
