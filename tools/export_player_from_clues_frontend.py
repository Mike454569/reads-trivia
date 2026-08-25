#!/usr/bin/env python3
"""Director v0.5, Step 3 -- deterministic conversion of the already-approved
`generated_games/director-v04-player-from-clues.json` into a browser-safe
static JS file the Reads frontend can load with a plain <script> tag.

Does NOT regenerate, reorder, or recompute anything -- pure 1:1
reshaping of the already-QA'd package into a smaller, browser-facing
field set. If the source package's `qa_status` is not "PASSED", this
script refuses to write output rather than ship an unvalidated package
into the frontend.

Deliberately drops fields the browser has no use for during normal
gameplay (the full `funnel`, `qa_checks_performed` prose, full
`production_safety`/`engine_version` dicts, `_diagnostics`) while
preserving everything Step 3 explicitly requires: puzzle IDs, ordered
clues, the answer entity, provenance (kept, for development/debugging --
just not rendered during normal play, per Step 6), difficulty, and QA
status.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PACKAGE = REPO_ROOT / "generated_games" / "director-v04-player-from-clues.json"
OUTPUT_JS = REPO_ROOT / "data" / "player-from-clues-v01.js"


def convert_clue(clue: dict) -> dict:
    return {
        "index": clue["clue_index"],
        "type": clue["clue_type"],
        "text": clue["display_text"],
        "candidatesBefore": clue["candidates_before"],
        "candidatesAfter": clue["candidates_after"],
        "provenance": {
            "table": clue["source"]["table"],
            "field": clue["source"]["field"],
            "sourceId": clue["source"]["source_id"],
            "verificationStatus": clue["source"]["verification_status"],
        },
    }


def _decade_for_puzzle(puzzle: dict) -> int | None:
    """Real, derived from the puzzle's own `career_span` clue (present on
    every puzzle in a real generation run -- confirmed directly against a
    600-puzzle sample before adding this, unlike `draft_year`, which only
    ~1/3 of puzzles carry). Bucketed by the CAREER START year, never
    invented -- a puzzle whose player has no career_span clue at all (only
    possible in principle, never observed) is left undecaded rather than
    guessed."""
    for c in puzzle["clues"]:
        if c["clue_type"] == "career_span":
            start_year = c["value"][0]
            return (start_year // 10) * 10
    return None


def _difficulty_band_for_puzzle(puzzle: dict) -> str:
    """Real, derived difficulty signal: how many candidates remained after
    the SECOND-TO-LAST clue (i.e. before the one clue that finally narrows
    to the unique answer). A puzzle where that number is small was already
    nearly solved before its final clue (an easier, more distinguishing
    profile); a puzzle where many candidates remained needed its very last
    clue to do most of the work (a harder, more generic profile). Real
    measured distribution across a 600-puzzle sample: median 3, 75th
    percentile 5 -- thresholds below picked directly from that distribution,
    not arbitrary round numbers."""
    second_to_last = puzzle["clues"][-2]["candidates_after"]
    if second_to_last <= 2:
        return "Easy"
    if second_to_last <= 5:
        return "Medium"
    return "Hard"


def convert_puzzle(puzzle: dict) -> dict:
    return {
        "id": puzzle["puzzle_id"],
        "answer": {
            "playerId": puzzle["answer"]["player_id"],
            "displayName": puzzle["answer"]["display_name"],
        },
        "clues": [convert_clue(c) for c in puzzle["clues"]],
        "finalCandidateCount": puzzle["final_candidate_count"],
        "qaStatus": puzzle["qa_status"],
        "decade": _decade_for_puzzle(puzzle),
        "difficultyBand": _difficulty_band_for_puzzle(puzzle),
    }


def convert(package: dict) -> dict:
    if package.get("qa_status") != "PASSED":
        raise SystemExit(
            f"ABORT: source package qa_status is {package.get('qa_status')!r}, not PASSED -- "
            f"refusing to export an unvalidated package to the frontend."
        )
    puzzle_ids = [p["puzzle_id"] for p in package["puzzles"]]
    if len(set(puzzle_ids)) != len(puzzle_ids):
        raise SystemExit("ABORT: duplicate puzzle_id found in source package.")
    for p in package["puzzles"]:
        if p["final_candidate_count"] != 1:
            raise SystemExit(f"ABORT: puzzle {p['puzzle_id']} has final_candidate_count != 1.")
        if len(p["clues"]) < 3:
            raise SystemExit(f"ABORT: puzzle {p['puzzle_id']} has fewer than 3 clues.")

    return {
        "packageId": package["package_id"],
        "packageVersion": package["package_version"],
        "mechanic": package["mechanic"],
        "gameTitle": package["game_title"],
        "gameInstructions": package["game_instructions"],
        "generatedAt": package["generated_at"],
        "qaStatus": package["qa_status"],
        "puzzleCount": package["puzzle_count"],
        "puzzles": [convert_puzzle(p) for p in package["puzzles"]],
    }


def main() -> None:
    package = json.loads(SOURCE_PACKAGE.read_text(encoding="utf-8"))
    browser_data = convert(package)

    lines = [
        "// AUTO-GENERATED -- do not hand-edit.",
        "// Produced by tools/export_player_from_clues_frontend.py from",
        f"// {SOURCE_PACKAGE.relative_to(REPO_ROOT)} (package_id {browser_data['packageId']}).",
        "// Pure reshaping of the already-QA'd Engine package -- no facts added, removed, or",
        "// reordered (decade/difficultyBand are the one addition: both derived directly from",
        "// fields the source package already contains, per this script's own _decade_for_puzzle()/",
        "// _difficulty_band_for_puzzle()). Re-run the script after regenerating the source package",
        "// to refresh this file.",
        "window.PLAYER_FROM_CLUES_V01 = " + json.dumps(browser_data, indent=2, ensure_ascii=False) + ";",
    ]
    OUTPUT_JS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_JS.relative_to(REPO_ROOT)} -- {browser_data['puzzleCount']} puzzles.")


if __name__ == "__main__":
    main()
