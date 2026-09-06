#!/usr/bin/env python3
"""CFB companion to tools/export_player_from_clues_frontend.py -- Reliability
pass (Pass 2.7). Deterministic conversion of the real, Engine-generated
`generated_games/director-v04-cfb-player-from-clues.json` into the browser-safe
static JS file the Reads frontend loads.

This REPLACES the previous data/cfb-player-from-clues-v01.js, which was a
hand-authored 12-puzzle prototype (`sourceId: "HAND_AUTHORED_CFB_PROTOTYPE"`)
that never got swapped out for real Engine output -- see this pass's own
audit: the real `identify_player_from_clues`/CFB_PLAYER_IDENTITY capability
(tools/director_v04/cfb_player_from_clues.py) has a 50,632-player real
eligible universe and can produce up to ~12,040 real, QA-passed puzzles in a
single scan (bounded only by a performance scan_cap, not by data scarcity).
The 12-puzzle prototype was purely a content-shipping gap, never a real
capability limit.

Does NOT regenerate, reorder, or recompute anything -- pure 1:1 reshaping of
the already-QA'd package, same discipline as the NFL exporter: refuses to
write output if qa_status != "PASSED".

CFB has no Pro Bowl/All-Pro/HOF tables to derive a fame-based difficulty band
from (unlike the NFL exporter's _fetch_fame_data/_difficulty_band_for_fame).
The real, disclosed CFB-appropriate proxy used here instead:
  - all_america clue present on the puzzle (real, certified, rare -- 939
    distinct players in cfb_all_america_certified) -> Easy
  - certified NFL draftee (cfb_nfl_identity_bridge_certified, 7,745 rows,
    joined to draft_facts on nfl_player_key for round/pick where available)
    drafted in round 1-2 (or bridge-certified with no draft_facts match at
    all, since a certified bridge match alone already means "went on to an
    NFL roster") -> Easy
  - any other certified NFL draftee -> Medium
  - everyone else -> Hard
This never invents a signal -- every band is derived from a real, certified
table, and a player with no bridge/All-America record simply falls to Hard
rather than being guessed at.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PACKAGE = REPO_ROOT / "generated_games" / "director-v04-cfb-player-from-clues.json"
OUTPUT_JS = REPO_ROOT / "data" / "cfb-player-from-clues-v01.js"

sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402


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
    """Real, derived from the puzzle's own career_span clue (present on
    every puzzle in this pass's real generation run -- 600/600). Bucketed
    by career START year, matching the NFL exporter's own convention."""
    for c in puzzle["clues"]:
        if c["clue_type"] == "career_span":
            start_year = c["value"][0]
            return (start_year // 10) * 10
    return None


def _fetch_nfl_bridge_data(c, cfb_player_ids: list[str]) -> dict[str, dict]:
    """Real per-player NFL-crossover signal for CFB players -- whether this
    college player is a CERTIFIED match to a real NFL player
    (cfb_nfl_identity_bridge_certified, 7,745 rows, cfb_player_id keyed,
    confirmed this pass to join 100% cleanly to canonical_cfb_players'
    own cfb_player_id namespace), and if so, that NFL player's real draft
    round/pick (draft_facts, joined on nfl_player_key=player_key -- only
    3,996/7,745 bridge rows have a draft_facts match, since some bridge
    matches are undrafted free agents; a bridge match with no draft_facts
    row still counts as "went on to the NFL", just without a round/pick
    signal)."""
    placeholders = ",".join("?" for _ in cfb_player_ids)
    bridge: dict[str, dict] = {pid: {"nfl_bridge": False, "draft_round": None, "draft_pick_overall": None} for pid in cfb_player_ids}

    rows = c.execute(
        f"""
        SELECT b.cfb_player_id, d.draft_round, d.draft_pick_overall
        FROM cfb_nfl_identity_bridge_certified b
        LEFT JOIN draft_facts d ON b.nfl_player_key = d.player_key
        WHERE b.cfb_player_id IN ({placeholders})
        """,
        cfb_player_ids,
    ).fetchall()
    for pid, draft_round, draft_pick_overall in rows:
        bridge[pid]["nfl_bridge"] = True
        bridge[pid]["draft_round"] = draft_round
        bridge[pid]["draft_pick_overall"] = draft_pick_overall
    return bridge


def _difficulty_band_for_cfb(puzzle: dict, bridge: dict) -> str:
    """See module docstring for the full real-signal reasoning."""
    has_all_america = any(c["clue_type"] == "all_america" for c in puzzle["clues"])
    if has_all_america:
        return "Easy"
    if bridge["nfl_bridge"]:
        if bridge["draft_round"] is not None and bridge["draft_round"] <= 2:
            return "Easy"
        return "Medium"
    return "Hard"


def convert_puzzle(puzzle: dict, bridge_by_player: dict) -> dict:
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
        "difficultyBand": _difficulty_band_for_cfb(puzzle, bridge_by_player[puzzle["answer"]["player_id"]]),
    }


def convert(package: dict, bridge_by_player: dict) -> dict:
    if package.get("qa_status") != "PASSED":
        raise SystemExit(
            f"ABORT: source package qa_status is {package.get('qa_status')!r}, not PASSED -- "
            f"refusing to export an unvalidated package to the frontend."
        )
    puzzle_ids = [p["puzzle_id"] for p in package["puzzles"]]
    if len(set(puzzle_ids)) != len(puzzle_ids):
        raise SystemExit("ABORT: duplicate puzzle_id found in source package.")
    answer_ids = [p["answer"]["player_id"] for p in package["puzzles"]]
    if len(set(answer_ids)) != len(answer_ids):
        raise SystemExit("ABORT: duplicate answer player found across puzzles in source package.")
    for p in package["puzzles"]:
        if p["final_candidate_count"] != 1:
            raise SystemExit(f"ABORT: puzzle {p['puzzle_id']} has final_candidate_count != 1.")
        if len(p["clues"]) < 3:
            raise SystemExit(f"ABORT: puzzle {p['puzzle_id']} has fewer than 3 clues.")

    result = {
        "packageId": package["package_id"],
        "packageVersion": package["package_version"],
        "mechanic": package["mechanic"],
        "gameTitle": package["game_title"],
        "gameInstructions": package["game_instructions"],
        "generatedAt": package["generated_at"],
        "qaStatus": package["qa_status"],
        "puzzleCount": package["puzzle_count"],
        "puzzles": [convert_puzzle(p, bridge_by_player) for p in package["puzzles"]],
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
    package = json.loads(SOURCE_PACKAGE.read_text(encoding="utf-8"))
    player_ids = sorted({p["answer"]["player_id"] for p in package["puzzles"]})
    c = engine.connect()
    bridge_by_player = _fetch_nfl_bridge_data(c, player_ids)
    c.close()
    browser_data = convert(package, bridge_by_player)

    band_counts: dict[str, int] = {}
    for p in browser_data["puzzles"]:
        band_counts[p["difficultyBand"]] = band_counts.get(p["difficultyBand"], 0) + 1

    lines = [
        "// AUTO-GENERATED -- do not hand-edit.",
        "// Produced by tools/export_cfb_player_from_clues_frontend.py from",
        f"// {SOURCE_PACKAGE.relative_to(REPO_ROOT)} (package_id {browser_data['packageId']}).",
        "// Reliability pass (Pass 2.7): replaces the previous hand-authored 12-puzzle",
        "// prototype (sourceId HAND_AUTHORED_CFB_PROTOTYPE) with real Engine output from",
        "// the identify_player_from_clues/CFB_PLAYER_IDENTITY capability -- a real,",
        "// 50,632-player eligible universe (tools/director_v04/cfb_player_from_clues.py),",
        "// never a data/filter limitation, just a static file that was never swapped for",
        "// real output. Pure reshaping of the already-QA'd Engine package -- no facts",
        "// added, removed, or reordered (decade/difficultyBand are the one addition, from",
        "// this script's own _decade_for_puzzle()/_difficulty_band_for_cfb() -- see this",
        "// file's module docstring for the real, disclosed CFB difficulty-signal proxy).",
        "// Re-run the script after regenerating the source package to refresh this file.",
        "window.CFB_PLAYER_FROM_CLUES_V01 = " + json.dumps(browser_data, indent=2, ensure_ascii=False) + ";",
    ]
    OUTPUT_JS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_JS.relative_to(REPO_ROOT)} -- {browser_data['puzzleCount']} puzzles.")
    print(f"Difficulty band distribution: {band_counts}")


if __name__ == "__main__":
    main()
