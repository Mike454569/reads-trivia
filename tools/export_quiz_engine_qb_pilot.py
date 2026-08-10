#!/usr/bin/env python3
"""Reads Engine v4 -> NFL Quiz static export adapter, Pilot Domain #2: QB/season.

Standalone exporter, independent of tools/export_quiz_engine_pilot*.py (the
Draft Pilot exporters) -- no shared code, no shared output paths. This file
proves the Engine -> static-export architecture generalizes to a second,
materially different domain (QB season starts, not draft picks) without
touching the Draft Pilot's logic or output at all.

Mechanic: "Which NFL team did QB X play for in season Y?" -- chosen over
the alternatives evaluated in QB_SEASON_ENGINE_COVERAGE_REPORT.md because it
reuses the exact same, already-audited team-resolution and distractor logic
from the Draft Pilot (team_aliases, season-matched), with the lowest new
logic surface of any viable predicate.

Game Factory has no built-in QB/season predicate (confirmed by reading
game_factory.py/game_factory_legacy.py in full and querying
game_factory_capabilities), so this exporter queries qb_team_seasons
directly -- the same verified, 100% SOURCE_BACKED/NFLVERSE_DATA table Engine
itself uses for its own pre-existing `qb_season` puzzle_catalog mode. This
script does not call any Engine HTTP server.

Difficulty is NOT invented: every accepted candidate must have a matching,
eligible row in Engine's own pre-existing `qb_season` puzzle_catalog mode
(joined on qb_source_id + season), and that row's Engine-computed
difficulty_band is what gets mapped to Easy/Medium/Hard. Candidates without
a matching Engine-scored row are rejected rather than assigned a
self-invented difficulty.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ENGINE_DIR = Path("/Users/micahnichols/Downloads/Reads_Football_Data_Engine_v4.0")
sys.path.insert(0, str(ENGINE_DIR))
import game_factory as gf  # only used for .connect() / .seeded() -- Engine's own DB/RNG helpers

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "data" / "quiz-engine-qb-pilot.js"
FUNNEL_STATS_PATH = REPO_ROOT / "tools" / "backups" / "qb_pilot_funnel_stats.json"

SEED = "reads-quiz-engine-qb-pilot-v1"
TARGET_COUNT = 100
ID_START = 300000  # distinct from Draft Pilot v1 (100000s) and v2 (200000s)

DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}
CATEGORY = "Passing Records & QB Trivia"  # existing Reads Quiz category, verbatim
REQUIRED_SOURCE = "NFLVERSE_DATA"

# QB identity is unresolved for these 7 qb_source_id values: each has more
# than one distinct qb_name across its qb_team_seasons rows -- typos/format
# variants for most, but 00-0034577 mixes rows for two different real
# people (Kyle Allen and Cam Newton) and 00-0035228 has one corrupted
# ("Taysom Kyler Murray") row. See QB_SEASON_ENGINE_COVERAGE_REPORT.md.
# Every row for every one of these IDs is excluded, not just the bad row.
IDENTITY_INCONSISTENT_QB_IDS = {
    "00-0017200", "00-0033869", "00-0034577", "00-0035228",
    "00-0035289", "00-0036355", "00-0039917",
}


def resolve_franchise(c, team_code: str, season: int):
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE team_code=? AND ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (team_code, season, season),
    ).fetchall()
    if len(rows) == 0:
        return None, "TEAM_UNRESOLVED"
    if len(rows) > 1:
        return None, "TEAM_AMBIGUOUS"
    return {"franchise_id": rows[0]["franchise_id"], "full_name": rows[0]["full_name"]}, None


def teams_active_in_season(c, season: int) -> dict:
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (season, season),
    ).fetchall()
    return {r["franchise_id"]: r["full_name"] for r in rows}


def check_production_safety(c) -> dict:
    """No data_coverage domain row exists for QB starts (see coverage
    report), so the gate is the row-level check applied to every candidate
    below, plus a one-time confirmation the source itself is approved."""
    src = c.execute(
        "SELECT source_id, source_name, approved_for_import FROM sources WHERE source_id=?",
        (REQUIRED_SOURCE,),
    ).fetchone()
    if not src or not src["approved_for_import"]:
        raise SystemExit(f"ABORT: source {REQUIRED_SOURCE} is not approved_for_import.")
    total = c.execute("SELECT COUNT(*) FROM qb_team_seasons").fetchone()[0]
    clean = c.execute(
        "SELECT COUNT(*) FROM qb_team_seasons WHERE verification_status='SOURCE_BACKED' AND source_id=?",
        (REQUIRED_SOURCE,),
    ).fetchone()[0]
    if clean != total:
        raise SystemExit(
            f"ABORT: qb_team_seasons has {total - clean} row(s) that are not "
            f"SOURCE_BACKED/{REQUIRED_SOURCE}; this script assumed uniform provenance."
        )
    return {
        "source_id": src["source_id"], "source_name": src["source_name"],
        "approved_for_import": bool(src["approved_for_import"]),
        "qb_team_seasons_total_rows": total,
        "qb_team_seasons_verified_rows": clean,
    }


def main():
    c = gf.connect()
    safety = check_production_safety(c)

    # Multi-team-in-one-season QBs: "which team" has no single correct
    # answer for these, so every row belonging to such a (qb_source_id,
    # season) pair is excluded up front.
    multi_team_pairs = {
        (r["qb_source_id"], r["season"])
        for r in c.execute(
            "SELECT qb_source_id, season FROM qb_team_seasons "
            "GROUP BY qb_source_id, season HAVING COUNT(DISTINCT team_code) > 1"
        )
    }

    all_rows = c.execute(
        "SELECT season, team_code, qb_source_id, qb_name, starts_observed, "
        "verification_status, source_id FROM qb_team_seasons "
        "ORDER BY qb_source_id, season, team_code"
    ).fetchall()

    # Deterministic shuffle so the accepted/exported set isn't biased toward
    # 1999 (the start of ORDER BY qb_source_id, season) -- same seeded-RNG
    # pattern the Draft Pilot uses for candidate ordering.
    rng_order = gf.seeded(SEED)
    all_rows = list(all_rows)
    rng_order.shuffle(all_rows)

    considered = len(all_rows)
    rejected_counts = Counter()
    accepted = []
    seen_player_ids = set()
    seen_questions = set()

    rng = gf.seeded(f"{SEED}:distractors")

    for row in all_rows:
        if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
            rejected_counts["ROW_NOT_VERIFIED"] += 1
            continue

        qb_id = row["qb_source_id"]

        if qb_id in IDENTITY_INCONSISTENT_QB_IDS:
            rejected_counts["UNRESOLVED_QB_IDENTITY"] += 1
            continue

        if (qb_id, row["season"]) in multi_team_pairs:
            rejected_counts["MULTIPLE_PLAUSIBLE_ANSWERS_MIDSEASON_TRADE"] += 1
            continue

        if qb_id in seen_player_ids:
            rejected_counts["DUPLICATE_PLAYER"] += 1
            continue

        season = row["season"]
        correct, err = resolve_franchise(c, row["team_code"], season)
        if err:
            rejected_counts[err] += 1
            continue

        # Engine-computed difficulty: require a matching, eligible row in
        # Engine's own pre-existing qb_season puzzle_catalog mode. No
        # difficulty is invented for rows that lack one.
        diff_row = c.execute(
            "SELECT difficulty_score, difficulty_band FROM puzzle_catalog "
            "WHERE mode_id='qb_season' AND source_entity_id=? AND season=? "
            "AND eligible=1 AND verification_status='SOURCE_BACKED' AND source_id=?",
            (qb_id, season, REQUIRED_SOURCE),
        ).fetchone()
        if not diff_row:
            rejected_counts["NO_ENGINE_DIFFICULTY_AVAILABLE"] += 1
            continue

        pool = teams_active_in_season(c, season)
        pool.pop(correct["franchise_id"], None)
        if len(pool) < 3:
            rejected_counts["INSUFFICIENT_DISTRACTORS"] += 1
            continue
        distractor_ids = rng.sample(sorted(pool.keys()), 3)
        distractor_names = [pool[fid] for fid in distractor_ids]

        options = [correct["full_name"]] + distractor_names
        if len(set(options)) != 4:
            rejected_counts["DUPLICATE_OPTIONS"] += 1
            continue

        question = f"Which NFL team did {row['qb_name']} play for in the {season} season?"
        if question in seen_questions:
            rejected_counts["DUPLICATE_QUESTION"] += 1
            continue

        order = list(range(4))
        rng.shuffle(order)
        shuffled_options = [options[i] for i in order]
        correct_index = shuffled_options.index(correct["full_name"])
        if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct["full_name"]:
            rejected_counts["INVALID_CORRECT_INDEX"] += 1
            continue

        band = diff_row["difficulty_band"]
        if band not in DIFFICULTY_MAP:
            rejected_counts["UNKNOWN_DIFFICULTY_BAND"] += 1
            continue
        difficulty = DIFFICULTY_MAP[band]

        starts = row["starts_observed"]
        notes = f"{row['qb_name']} made {starts} start{'s' if starts != 1 else ''} for the {correct['full_name']} in {season}."

        accepted.append(
            {
                "id": ID_START + len(accepted),
                "category": CATEGORY, "difficulty": difficulty, "question": question,
                "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
                "_audit": {
                    "qb_source_id": qb_id, "qb_name": row["qb_name"], "team_code": row["team_code"],
                    "season": season, "starts_observed": starts,
                    "franchise_id": correct["franchise_id"], "correct_answer_text": correct["full_name"],
                    "difficulty_score": diff_row["difficulty_score"], "difficulty_band": band,
                    "verification_status": row["verification_status"], "source_id": row["source_id"],
                },
            }
        )
        seen_player_ids.add(qb_id)
        seen_questions.add(question)

    c.close()

    exported = accepted[:TARGET_COUNT]
    accepted_but_not_exported = max(0, len(accepted) - len(exported))
    shortfall_reason = None
    if len(exported) < TARGET_COUNT:
        shortfall_reason = (
            f"Only {len(accepted)} candidates passed every validation rule across the full "
            f"{considered}-row qb_team_seasons table; exported the maximum available "
            f"({len(exported)}) rather than loosen any rule to reach 100."
        )

    contract_failures = []
    for q in exported:
        keys = set(q.keys()) - {"_audit"}
        if keys != {"id", "category", "difficulty", "question", "options", "correctIndex", "notes"}:
            contract_failures.append((q["id"], "unexpected key set")); continue
        if not isinstance(q["id"], int):
            contract_failures.append((q["id"], "id not int"))
        if q["category"] != CATEGORY:
            contract_failures.append((q["id"], "category not the approved existing category"))
        if q["difficulty"] not in ("Easy", "Medium", "Hard"):
            contract_failures.append((q["id"], "difficulty not in Easy/Medium/Hard"))
        if not isinstance(q["question"], str) or not q["question"].strip():
            contract_failures.append((q["id"], "empty question"))
        if not isinstance(q["options"], list) or len(q["options"]) != 4 or len(set(q["options"])) != 4:
            contract_failures.append((q["id"], "options not exactly 4 unique strings"))
        if not (isinstance(q["correctIndex"], int) and 0 <= q["correctIndex"] <= 3):
            contract_failures.append((q["id"], "correctIndex out of range"))
        elif q["options"][q["correctIndex"]] != q["_audit"]["correct_answer_text"]:
            contract_failures.append((q["id"], "correctIndex does not point at the verified correct answer"))
        if not isinstance(q["notes"], str):
            contract_failures.append((q["id"], "notes not a string"))

    dup_questions = [t for t, n in Counter(q["question"] for q in exported).items() if n > 1]
    dup_players = [p for p, n in Counter(q["_audit"]["qb_source_id"] for q in exported).items() if n > 1]
    dup_ids = [i for i, n in Counter(q["id"] for q in exported).items() if n > 1]

    write_output_js(exported)

    by_category = Counter(q["category"] for q in exported)
    by_difficulty = Counter(q["difficulty"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    franchises = sorted(set(q["_audit"]["franchise_id"] for q in exported))

    funnel_stats = {
        "seed": SEED, "target_count": TARGET_COUNT,
        "safety": safety,
        "considered": considered,
        "rejected_counts": dict(rejected_counts),
        "total_rejected": sum(rejected_counts.values()),
        "accepted_total": len(accepted),
        "exported_count": len(exported),
        "accepted_but_not_exported": accepted_but_not_exported,
        "shortfall_reason": shortfall_reason,
        "category_distribution": dict(by_category),
        "difficulty_distribution": dict(by_difficulty),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_franchises": len(franchises),
        "unique_qbs": len(set(q["_audit"]["qb_source_id"] for q in exported)),
        "dup_questions": dup_questions, "dup_players": dup_players, "dup_ids": dup_ids,
        "contract_failures": contract_failures,
        "contract_passed": len(contract_failures) == 0,
        "identity_inconsistent_qb_ids_excluded": sorted(IDENTITY_INCONSISTENT_QB_IDS),
        "multi_team_season_pairs_excluded": len(multi_team_pairs),
    }
    FUNNEL_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FUNNEL_STATS_PATH.write_text(json.dumps(funnel_stats, indent=2), encoding="utf-8")

    print(f"Considered: {considered}")
    print(f"Rejected: {sum(rejected_counts.values())}")
    print(f"Accepted (passed all checks): {len(accepted)}")
    print(f"Exported: {len(exported)}")
    if shortfall_reason:
        print(f"SHORTFALL: {shortfall_reason}")
    print(f"Contract failures: {len(contract_failures)}")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {FUNNEL_STATS_PATH}")


def write_output_js(exported: list[dict]):
    clean = [
        {
            "id": q["id"], "category": q["category"], "difficulty": q["difficulty"],
            "question": q["question"], "options": q["options"],
            "correctIndex": q["correctIndex"], "notes": q["notes"],
        }
        for q in exported
    ]
    header = (
        "// AUTO-GENERATED PILOT FILE -- do not hand-edit.\n"
        "// Produced by tools/export_quiz_engine_qb_pilot.py from Reads Football Data\n"
        "// Engine v4.0 (qb_team_seasons + team_aliases, direct query -- Game Factory has\n"
        "// no built-in QB/season predicate). Pilot Domain #2, independent of the Draft\n"
        "// Pilot exporters (tools/export_quiz_engine_pilot.py / _v2.py).\n"
        "// Deterministic seed: \"" + SEED + "\". Rerunning the exporter against an\n"
        "// unchanged database reproduces this file byte-for-byte.\n"
        "//\n"
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or\n"
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_QB_PILOT, distinct\n"
        "// from window.QUIZ_DATA and both Draft Pilot globals, so it cannot collide\n"
        "// with any of them even if loaded by mistake.\n"
        "//\n"
        "// See QUIZ_ENGINE_QB_PILOT_REPORT.md for the full audit trail.\n"
        "window.QUIZ_DATA_ENGINE_QB_PILOT = "
    )
    body = json.dumps(clean, indent=2, ensure_ascii=False)
    OUT_PATH.write_text(header + body + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
