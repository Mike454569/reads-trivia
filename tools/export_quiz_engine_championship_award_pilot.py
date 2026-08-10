#!/usr/bin/env python3
"""Reads Engine v4 -> NFL Quiz static export adapter, Pilot Domain #3:
Championship / Postseason.

Standalone exporter, independent of the Draft and QB Pilot exporters -- no
shared code, no shared output paths.

Mechanic: "How did team X finish the season-Y NFL postseason?" -- chosen
over "which team won/lost the Super Bowl" because that narrower framing
only has 22 valid rows (one per covered season), far short of the
100-question target. This broader framing has 296 fully-verified rows,
each team-season has *exactly one* recorded outcome (season,team_code is a
primary key on season_standings -- no ties, no co-champions possible by
construction), and it naturally includes the Super Bowl winner/loser cases
as two of its five possible answers. See
CHAMPIONSHIP_AWARD_ENGINE_COVERAGE_REPORT.md for the full predicate
evaluation.

No NFL award table exists anywhere in Engine v4 (confirmed by exhaustive
search) -- award data is CFB-only (cfb_awards, cfb_award_facts) and is not
used here, since that would misrepresent CFB content as NFL trivia.

Game Factory has no championship/award predicate (confirmed against
game_factory_capabilities), so this exporter queries season_standings
directly -- the same verified, 100% SOURCE_BACKED/NFLVERSE_DATA table
Engine itself uses for its own pre-existing `playoff_result` puzzle_catalog
mode. Difficulty is NOT invented: every accepted candidate must have a
matching, eligible row in that pre-existing mode (joined on team_code +
season, with its answer cross-checked to match), exactly the same pattern
used by the QB Pilot for qb_season.
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
OUT_PATH = REPO_ROOT / "data" / "quiz-engine-championship-award-pilot.js"
FUNNEL_STATS_PATH = REPO_ROOT / "tools" / "backups" / "championship_award_pilot_funnel_stats.json"

SEED = "reads-quiz-engine-championship-award-pilot-v1"
TARGET_COUNT = 100
ID_START = 400000  # distinct from 100000s/200000s/300000s used by the prior two pilots

DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}
CATEGORY = "Playoffs & Postseason Moments"  # existing Reads Quiz category, verbatim
REQUIRED_SOURCE = "NFLVERSE_DATA"

# The complete, closed vocabulary of season_standings.playoff_result values.
# Nothing here is invented -- these are literally the only 5 distinct
# strings that appear in that column; this is a label expansion (WC/DV/CC/SB
# are standard NFL postseason round abbreviations), not new content.
OUTCOME_LABELS = {
    "WonSB": "Won the Super Bowl",
    "LostSB": "Lost the Super Bowl",
    "LostCC": "Lost in the Conference Championship",
    "LostDV": "Lost in the Divisional Round",
    "LostWC": "Lost in the Wild Card Round",
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


def check_production_safety(c) -> dict:
    """No data_coverage domain row exists for postseason results (same
    situation as the QB pilot), so the gate is the row-level check applied
    to every candidate, plus a one-time confirmation the source is approved."""
    src = c.execute(
        "SELECT source_id, source_name, approved_for_import FROM sources WHERE source_id=?",
        (REQUIRED_SOURCE,),
    ).fetchone()
    if not src or not src["approved_for_import"]:
        raise SystemExit(f"ABORT: source {REQUIRED_SOURCE} is not approved_for_import.")
    total = c.execute("SELECT COUNT(*) FROM season_standings WHERE playoff_result IS NOT NULL").fetchone()[0]
    clean = c.execute(
        "SELECT COUNT(*) FROM season_standings WHERE playoff_result IS NOT NULL "
        "AND verification_status='SOURCE_BACKED' AND source_id=?",
        (REQUIRED_SOURCE,),
    ).fetchone()[0]
    if clean != total:
        raise SystemExit(
            f"ABORT: season_standings has {total - clean} playoff row(s) that are not "
            f"SOURCE_BACKED/{REQUIRED_SOURCE}; this script assumed uniform provenance."
        )
    return {
        "source_id": src["source_id"], "source_name": src["source_name"],
        "approved_for_import": bool(src["approved_for_import"]),
        "season_standings_playoff_rows_total": total,
        "season_standings_playoff_rows_verified": clean,
    }


def main():
    c = gf.connect()
    safety = check_production_safety(c)

    all_rows = c.execute(
        "SELECT season, team_code, wins, losses, ties, playoff_result, "
        "verification_status, source_id FROM season_standings "
        "WHERE playoff_result IS NOT NULL ORDER BY season, team_code"
    ).fetchall()

    # Deterministic shuffle so the exported set isn't biased toward 2002
    # (the start of ORDER BY season, team_code) -- same seeded-RNG pattern
    # used by the Draft and QB pilots for candidate ordering.
    rng_order = gf.seeded(SEED)
    all_rows = list(all_rows)
    rng_order.shuffle(all_rows)

    considered = len(all_rows)
    rejected_counts = Counter()
    accepted = []
    seen_questions = set()

    rng = gf.seeded(f"{SEED}:distractors")

    for row in all_rows:
        if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
            rejected_counts["ROW_NOT_VERIFIED"] += 1
            continue

        outcome = row["playoff_result"]
        if outcome not in OUTCOME_LABELS:
            rejected_counts["UNKNOWN_OUTCOME_LABEL"] += 1
            continue

        season = row["season"]
        franchise, err = resolve_franchise(c, row["team_code"], season)
        if err:
            rejected_counts[err] += 1
            continue

        # Engine-computed difficulty: require a matching, eligible row in
        # Engine's own pre-existing playoff_result puzzle_catalog mode, and
        # cross-check its stored answer against season_standings itself
        # rather than trusting the join alone.
        diff_row = c.execute(
            "SELECT difficulty_score, difficulty_band, payload_json FROM puzzle_catalog "
            "WHERE mode_id='playoff_result' AND source_entity_id=? AND season=? "
            "AND eligible=1 AND verification_status='SOURCE_BACKED' AND source_id=?",
            (row["team_code"], season, REQUIRED_SOURCE),
        ).fetchone()
        if not diff_row:
            rejected_counts["NO_ENGINE_DIFFICULTY_AVAILABLE"] += 1
            continue
        engine_answer = json.loads(diff_row["payload_json"]).get("answer")
        if engine_answer != outcome:
            rejected_counts["DIFFICULTY_SOURCE_MISMATCH"] += 1
            continue

        correct_label = OUTCOME_LABELS[outcome]
        other_labels = [lab for code, lab in OUTCOME_LABELS.items() if code != outcome]
        distractor_labels = rng.sample(other_labels, 3)

        options = [correct_label] + distractor_labels
        if len(set(options)) != 4:
            rejected_counts["DUPLICATE_OPTIONS"] += 1
            continue

        question = f"How did the {franchise['full_name']} finish the {season} NFL season?"
        if question in seen_questions:
            rejected_counts["DUPLICATE_QUESTION"] += 1
            continue

        order = list(range(4))
        rng.shuffle(order)
        shuffled_options = [options[i] for i in order]
        correct_index = shuffled_options.index(correct_label)
        if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_label:
            rejected_counts["INVALID_CORRECT_INDEX"] += 1
            continue

        band = diff_row["difficulty_band"]
        if band not in DIFFICULTY_MAP:
            rejected_counts["UNKNOWN_DIFFICULTY_BAND"] += 1
            continue
        difficulty = DIFFICULTY_MAP[band]

        wins, losses, ties = row["wins"], row["losses"], row["ties"]
        if wins is None or losses is None:
            rejected_counts["MISSING_RECORD"] += 1
            continue
        record = f"{wins}-{losses}" + (f"-{ties}" if ties else "")
        notes = f"The {franchise['full_name']} went {record} in {season} and {correct_label[0].lower()}{correct_label[1:]}."

        accepted.append(
            {
                "id": ID_START + len(accepted),
                "category": CATEGORY, "difficulty": difficulty, "question": question,
                "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
                "_audit": {
                    "team_code": row["team_code"], "season": season, "record": record,
                    "playoff_result": outcome, "franchise_id": franchise["franchise_id"],
                    "correct_answer_text": correct_label,
                    "difficulty_score": diff_row["difficulty_score"], "difficulty_band": band,
                    "verification_status": row["verification_status"], "source_id": row["source_id"],
                },
            }
        )
        seen_questions.add(question)

    c.close()

    exported = accepted[:TARGET_COUNT]
    accepted_but_not_exported = max(0, len(accepted) - len(exported))
    shortfall_reason = None
    if len(exported) < TARGET_COUNT:
        shortfall_reason = (
            f"Only {len(accepted)} candidates passed every validation rule across the full "
            f"{considered}-row season_standings playoff pool; exported the maximum available "
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
    dup_ids = [i for i, n in Counter(q["id"] for q in exported).items() if n > 1]
    dup_team_seasons = [
        ts for ts, n in Counter((q["_audit"]["team_code"], q["_audit"]["season"]) for q in exported).items() if n > 1
    ]

    write_output_js(exported)

    by_category = Counter(q["category"] for q in exported)
    by_difficulty = Counter(q["difficulty"] for q in exported)
    by_outcome = Counter(q["_audit"]["playoff_result"] for q in exported)
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
        "outcome_distribution": dict(by_outcome),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_franchises": len(franchises),
        "dup_questions": dup_questions, "dup_ids": dup_ids,
        "dup_team_seasons": [list(x) for x in dup_team_seasons],
        "contract_failures": contract_failures,
        "contract_passed": len(contract_failures) == 0,
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
        "// Produced by tools/export_quiz_engine_championship_award_pilot.py from Reads\n"
        "// Football Data Engine v4.0 (season_standings.playoff_result, direct query --\n"
        "// Game Factory has no championship/award predicate). Pilot Domain #3,\n"
        "// independent of the Draft and QB Pilot exporters.\n"
        "// Deterministic seed: \"" + SEED + "\". Rerunning the exporter against an\n"
        "// unchanged database reproduces this file byte-for-byte.\n"
        "//\n"
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or\n"
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_CHAMPIONSHIP_AWARD_PILOT,\n"
        "// distinct from window.QUIZ_DATA and every other pilot global, so it cannot\n"
        "// collide with any of them even if loaded by mistake.\n"
        "//\n"
        "// See QUIZ_ENGINE_CHAMPIONSHIP_AWARD_PILOT_REPORT.md for the full audit trail.\n"
        "window.QUIZ_DATA_ENGINE_CHAMPIONSHIP_AWARD_PILOT = "
    )
    body = json.dumps(clean, indent=2, ensure_ascii=False)
    OUT_PATH.write_text(header + body + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
