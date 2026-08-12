#!/usr/bin/env python3
"""Generate the production NFL Game Results Engine data file.

App-Wide Engine Migration operation: proves newly-ingested game data
(tools/data_refresh/nfl_games_refresh.py's real, automatically-refreshed
`games` table) can become real, playable Quiz content, not just live
Gateway API responses -- the same pregenerated-static-file pattern
tools/generate_quiz_engine_draft_production.py already established, so
Quiz never waits on live generation between questions (Section H).

Runs the real, registered NFL_GAME_RESULT/WON_GAME adapter
(tools/quiz_export/adapters/nfl_game_result.py) through the shared
tools/quiz_export framework. No question is hand-written; this script
only calls the existing adapter and serializes its real output.

Output: data/quiz-engine-game-result-production.js,
window.QUIZ_DATA_ENGINE_GAME_RESULT. Re-running this against a refreshed
`games` table (new games ingested by the daily production refresh) picks
up real new content automatically -- this script has no season-specific
logic of its own.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.quiz_export import core, serializer
from tools.quiz_export.adapters import nfl_game_result

OUT_PATH = nfl_game_result.engine.DATA_DIR / "quiz-engine-game-result-production.js"
GLOBAL_NAME = "QUIZ_DATA_ENGINE_GAME_RESULT"
SEED = "reads-quiz-engine-game-result-production-v1"
ID_START = 660000  # matches registry.py's pipeline_id_start for NFL_GAME_RESULT/WON_GAME
TARGET_COUNT = 300  # real accepted pool is 6,484 (see registry.py's known_limitations) -- a
                     # substantial, varied slice, not the whole pool, matching every other pilot's scale


def header_lines(seed: str) -> list[str]:
    return [
        "// PRODUCTION Engine data file -- do not hand-edit.",
        "// Produced by tools/generate_quiz_engine_game_result_production.py, which runs the",
        "// already-registered NFL_GAME_RESULT/WON_GAME adapter",
        "// (tools/quiz_export/adapters/nfl_game_result.py) through the shared",
        "// tools/quiz_export framework, against tools/data_refresh/nfl_games_refresh.py's",
        "// real, automatically-refreshed `games` table.",
        "//",
        f'// Deterministic seed: "{seed}". Rerunning this script against the SAME games',
        "// table state reproduces this file byte-for-byte; rerunning after a real daily",
        "// refresh (new games ingested) picks up real new content automatically -- this",
        "// script has no season-specific logic of its own.",
        "//",
        "// ID namespace: 660000-660299 -- matches registry.py's pipeline_id_start for this",
        "// domain, the permanent Engine content range reserved so these can never collide",
        "// with data/quiz.js's hand-authored IDs or any other Engine domain's block.",
        "//",
        "// See READS_APP_WIDE_ENGINE_MIGRATION_REPORT.md for the full audit trail.",
    ]


def main():
    result = core.run_export(
        nfl_game_result,
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
