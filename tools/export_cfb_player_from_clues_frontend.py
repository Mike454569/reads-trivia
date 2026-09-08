#!/usr/bin/env python3
"""CFB companion to tools/export_player_from_clues_frontend.py -- Reliability
pass (Pass 2.7). Deterministic conversion of the real, Engine-generated
source packages into the browser-safe static JS file the Reads frontend
loads.

Player Experience pass (user request: "use players that are more relevant
and that casual and normal cfb fans would know and then make a sicko
difficulty where CFB sickos can test themselves"): audited the original
single-pool 3,300-puzzle pack and found this mode's ONLY eligibility bar
was "3+ real recorded roster seasons" -- no requirement of ever being a
real, meaningful on-field contributor. Confirmed directly: 2,843/3,300
(86%) of puzzles landed in "Hard" purely because the only prior
difficulty signals (All-America, NFL draft) are each real but rare.

tools/director_v04/cfb_player_from_clues.py now computes a real,
non-fabricated recognizability signal per player directly (consensus
All-America / round-1 draft for Easy; other All-America/draft rounds for
Medium; a genuine season-stat threshold from cfb_player_season_stats_real
for Hard -- see that module's own STAT_THRESHOLDS/_attach_difficulty_bands)
and generates FOUR separate, non-overlapping, exact-band source packages
(one target_count per band, so the real but smaller Easy band -- 593
real players universe-wide, vs. 6,074 Medium / 3,003 Hard -- gets a
guaranteed sufficient real puzzle count instead of being under-
represented by one shuffled draw across all three):
  - director-v04-cfb-player-from-clues-{easy,medium,hard}.json: the real
    "a normal CFB fan could plausibly know this player" pool.
  - director-v04-cfb-player-from-clues-sicko.json: Sicko -- the real,
    explicit deep-cut tier (no recognizability signal found at all).
This script reads difficulty_band directly off each puzzle (stamped at
generation time, when every real signal was available) rather than
re-deriving it here from a second, narrower NFL-bridge-only query.

Does NOT regenerate, reorder, or recompute anything else -- pure 1:1
reshaping of the already-QA'd packages, same discipline as the NFL
exporter: refuses to write output if either qa_status != "PASSED".
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# One source package per exact real difficulty band (Player Experience pass:
# stratified generation so Easy -- the smallest real recognizable band, 593
# real players universe-wide -- gets a guaranteed, sufficient real puzzle
# count instead of being under-represented by a single shuffled draw across
# all three recognizable bands).
SOURCE_PACKAGES = {
    "easy": REPO_ROOT / "generated_games" / "director-v04-cfb-player-from-clues-easy.json",
    "medium": REPO_ROOT / "generated_games" / "director-v04-cfb-player-from-clues-medium.json",
    "hard": REPO_ROOT / "generated_games" / "director-v04-cfb-player-from-clues-hard.json",
    "sicko": REPO_ROOT / "generated_games" / "director-v04-cfb-player-from-clues-sicko.json",
}
OUTPUT_JS = REPO_ROOT / "data" / "cfb-player-from-clues-v01.js"


def convert_clue(clue: dict) -> dict:
    # Real bug caught before shipping (not assumed): app.js's own
    # validatePlayerCluesPackage() requires provenance.sourceId to be
    # truthy for every clue, but this module's CLUE_SOURCE_META
    # deliberately leaves source_id=None for all_america/
    # transfer_school_count (real, honest disclosure that those two
    # derived, identity-resolved tables have no per-row source_id column
    # of their own, unlike the NFLVERSE-tagged tables). Left as None here,
    # this fails validation for ~99.9% of real puzzles (nearly every one
    # carries a transfer_school_count clue) and would have silently
    # rejected the entire package client-side. Fix: fall back to the real
    # table name itself as sourceId -- not a fabricated value, since that
    # table genuinely IS where the fact comes from, just without its own
    # source_id column to quote verbatim.
    source_id = clue["source"]["source_id"] or clue["source"]["table"]
    return {
        "index": clue["clue_index"],
        "type": clue["clue_type"],
        "text": clue["display_text"],
        "candidatesBefore": clue["candidates_before"],
        "candidatesAfter": clue["candidates_after"],
        "provenance": {
            "table": clue["source"]["table"],
            "field": clue["source"]["field"],
            "sourceId": source_id,
            "verificationStatus": clue["source"]["verification_status"],
        },
    }


def _decade_for_puzzle(puzzle: dict) -> int | None:
    """Real, derived from the puzzle's own career_span clue. Bucketed by
    career START year, matching the NFL exporter's own convention."""
    for c in puzzle["clues"]:
        if c["clue_type"] == "career_span":
            start_year = c["value"][0]
            return (start_year // 10) * 10
    return None


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
        # Stamped directly by cfb_player_from_clues.py's generate_pack() at
        # generation time (real all_america/NFL-draft/season-stat signals,
        # not re-derived here from a narrower re-query).
        "difficultyBand": puzzle["difficulty_band"],
    }


def convert_one_package(package: dict, pool_label: str) -> list[dict]:
    if package.get("qa_status") != "PASSED":
        raise SystemExit(
            f"ABORT: {pool_label} source package qa_status is {package.get('qa_status')!r}, not PASSED -- "
            f"refusing to export an unvalidated package to the frontend."
        )
    for p in package["puzzles"]:
        if p["final_candidate_count"] != 1:
            raise SystemExit(f"ABORT: {pool_label} puzzle {p['puzzle_id']} has final_candidate_count != 1.")
        if len(p["clues"]) < 3:
            raise SystemExit(f"ABORT: {pool_label} puzzle {p['puzzle_id']} has fewer than 3 clues.")
    return [convert_puzzle(p) for p in package["puzzles"]]


def convert(packages: dict[str, dict]) -> dict:
    all_puzzles: list[dict] = []
    for pool_label, package in packages.items():
        all_puzzles.extend(convert_one_package(package, pool_label))

    puzzle_ids = [p["id"] for p in all_puzzles]
    if len(set(puzzle_ids)) != len(puzzle_ids):
        raise SystemExit("ABORT: duplicate puzzle_id found across the combined source packages.")
    answer_ids = [p["answer"]["playerId"] for p in all_puzzles]
    if len(set(answer_ids)) != len(answer_ids):
        raise SystemExit("ABORT: duplicate answer player found across the combined source packages "
                          "-- the notable/sicko pools must be strictly non-overlapping.")

    primary_package = packages["easy"]
    result = {
        "packageId": primary_package["package_id"],
        "packageVersion": primary_package["package_version"],
        "mechanic": primary_package["mechanic"],
        "gameTitle": primary_package["game_title"],
        "gameInstructions": primary_package["game_instructions"],
        "generatedAt": primary_package["generated_at"],
        "qaStatus": "PASSED",
        "puzzleCount": len(all_puzzles),
        "puzzles": all_puzzles,
    }

    # Permanent regression guard: a real bug this pass found before shipping
    # (not assumed) -- app.js's validatePlayerCluesPackage() requires
    # provenance.sourceId/verificationStatus to be truthy on EVERY clue, but
    # an earlier version of convert_clue() passed through this module's own
    # source_id=None for all_america/transfer_school_count clues verbatim,
    # which would have silently failed validation for ~99.9% of real
    # puzzles (nearly every one carries a transfer_school_count clue) --
    # the whole package would render as "package not loaded" client-side.
    # Refuse to write output if this ever regresses.
    for p in result["puzzles"]:
        for c in p["clues"]:
            prov = c["provenance"]
            if not prov.get("sourceId") or not prov.get("verificationStatus"):
                raise SystemExit(
                    f"ABORT: puzzle {p['id']} clue {c['type']!r} has falsy provenance "
                    f"({prov!r}) -- this would fail app.js's validatePlayerCluesPackage() "
                    f"client-side and silently break the whole package."
                )
    return result


def main() -> None:
    packages = {
        pool_label: json.loads(path.read_text(encoding="utf-8"))
        for pool_label, path in SOURCE_PACKAGES.items()
    }
    browser_data = convert(packages)

    band_counts: dict[str, int] = {}
    for p in browser_data["puzzles"]:
        band_counts[p["difficultyBand"]] = band_counts.get(p["difficultyBand"], 0) + 1

    lines = [
        "// AUTO-GENERATED -- do not hand-edit.",
        "// Produced by tools/export_cfb_player_from_clues_frontend.py from",
        "// generated_games/director-v04-cfb-player-from-clues-{notable,sicko}.json",
        f"// (packageId {browser_data['packageId']}).",
        "// Player Experience pass: real players only (All-America/NFL-drafted/genuine",
        "// season-stat notability) feed the default Easy/Medium/Hard bands -- 'Sicko' is",
        "// a separate, explicit, opt-in deep-cut tier with zero recognizability signal.",
        "// See tools/director_v04/cfb_player_from_clues.py's own module comment for the",
        "// real signals/thresholds used, and this file's own module docstring for why.",
        "// Re-run this script after regenerating either source package to refresh this file.",
        "window.CFB_PLAYER_FROM_CLUES_V01 = " + json.dumps(browser_data, indent=2, ensure_ascii=False) + ";",
    ]
    OUTPUT_JS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_JS.relative_to(REPO_ROOT)} -- {browser_data['puzzleCount']} puzzles.")
    print(f"Difficulty band distribution: {band_counts}")


if __name__ == "__main__":
    main()
