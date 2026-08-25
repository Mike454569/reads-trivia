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
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PACKAGE = REPO_ROOT / "generated_games" / "director-v04-player-from-clues.json"
OUTPUT_JS = REPO_ROOT / "data" / "player-from-clues-v01.js"

sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402


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


def _fetch_fame_data(c, player_ids: list[str]) -> dict[str, dict]:
    """Real per-player fame signals -- Pro Bowl count, All-Pro count, HOF
    status, first-round draft status -- pulled directly from this Engine's
    own real tables (nfl_pro_bowl_selections/nfl_all_pro_selections/
    nfl_hof_inductees, all keyed by the same PFR:XxxYy00 player_id draft_facts
    already uses; draft_facts.draft_pick_overall itself). This is the fix for
    a real, reported gameplay problem: the OLD difficulty signal (candidates
    remaining before the final clue) measured how STRUCTURALLY narrow a
    clue chain was, not whether the player is someone a casual fan would
    actually recognize -- a career long-snapper with a rare draft-year/
    college combination could score as "Easy" under that signal while being
    genuinely obscure. Real fame data is a direct, honest proxy for
    recognizability instead."""
    placeholders = ",".join("?" for _ in player_ids)
    fame: dict[str, dict] = {pid: {"pro_bowls": 0, "all_pros": 0, "hof": False, "draft_pick_overall": None} for pid in player_ids}

    for pid, count in c.execute(
        f"SELECT player_id, COUNT(*) FROM nfl_pro_bowl_selections WHERE player_id IN ({placeholders}) GROUP BY player_id",
        player_ids,
    ).fetchall():
        fame[pid]["pro_bowls"] = count
    for pid, count in c.execute(
        f"SELECT player_id, COUNT(*) FROM nfl_all_pro_selections WHERE player_id IN ({placeholders}) GROUP BY player_id",
        player_ids,
    ).fetchall():
        fame[pid]["all_pros"] = count
    for (pid,) in c.execute(
        f"SELECT player_id FROM nfl_hof_inductees WHERE is_player=1 AND player_id IN ({placeholders})",
        player_ids,
    ).fetchall():
        fame[pid]["hof"] = True
    for pid, pick in c.execute(
        f"SELECT player_key, draft_pick_overall FROM draft_facts WHERE player_key IN ({placeholders})",
        player_ids,
    ).fetchall():
        fame[pid]["draft_pick_overall"] = pick
    return fame


def _difficulty_band_for_fame(fame: dict) -> str:
    """Real fame-based difficulty: HOF or 3+ Pro Bowls or any All-Pro
    selection is genuinely recognizable to a casual fan (Easy); 1-2 Pro
    Bowls or a real first-round draft pick (overall <= 32) is a real but
    less universally known player (Medium); everyone else is a real role
    player/journeyman a casual fan is unlikely to know by name alone
    (Hard) -- never relabeled Easy just because their clue chain happened
    to narrow quickly."""
    if fame["hof"] or fame["pro_bowls"] >= 3 or fame["all_pros"] >= 1:
        return "Easy"
    if fame["pro_bowls"] >= 1 or (fame["draft_pick_overall"] is not None and fame["draft_pick_overall"] <= 32):
        return "Medium"
    return "Hard"


def convert_puzzle(puzzle: dict, fame: dict) -> dict:
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
        "difficultyBand": _difficulty_band_for_fame(fame[puzzle["answer"]["player_id"]]),
    }


def convert(package: dict, fame_by_player: dict) -> dict:
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
        "puzzles": [convert_puzzle(p, fame_by_player) for p in package["puzzles"]],
    }


def main() -> None:
    package = json.loads(SOURCE_PACKAGE.read_text(encoding="utf-8"))
    player_ids = sorted({p["answer"]["player_id"] for p in package["puzzles"]})
    c = engine.connect()
    fame_by_player = _fetch_fame_data(c, player_ids)
    c.close()
    browser_data = convert(package, fame_by_player)

    lines = [
        "// AUTO-GENERATED -- do not hand-edit.",
        "// Produced by tools/export_player_from_clues_frontend.py from",
        f"// {SOURCE_PACKAGE.relative_to(REPO_ROOT)} (package_id {browser_data['packageId']}).",
        "// Pure reshaping of the already-QA'd Engine package -- no facts added, removed, or",
        "// reordered (decade/difficultyBand are the one addition: decade from the source package's own",
        "// career_span clue, difficultyBand from real Engine fame data -- Pro Bowl/All-Pro/HOF/first-round",
        "// draft status -- looked up per answer player, per this script's own _decade_for_puzzle()/",
        "// _difficulty_band_for_fame()). Re-run the script after regenerating the source package to",
        "// refresh this file.",
        "window.PLAYER_FROM_CLUES_V01 = " + json.dumps(browser_data, indent=2, ensure_ascii=False) + ";",
    ]
    OUTPUT_JS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_JS.relative_to(REPO_ROOT)} -- {browser_data['puzzleCount']} puzzles.")


if __name__ == "__main__":
    main()
