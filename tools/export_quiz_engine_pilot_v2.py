#!/usr/bin/env python3
"""Reads Engine v4 -> NFL Quiz static export adapter (Pilot v2, 100 questions).

Same deterministic pipeline as tools/export_quiz_engine_pilot.py (Pilot v1):
same seed, same DRAFTED_BY/guess spec, same production-safety gate, same
per-candidate QA/rejection rules, same category and difficulty mappings. No
validation rule is loosened. The only functional difference from v1 is the
export target (100 instead of 50) and the output paths -- this run happens
after 30 team_aliases rows were widened (see TEAM_ALIAS_SAFE_FIX_CHANGELOG.md),
so more of the same candidate pool now resolves to a verified franchise.

Writes data/quiz-engine-pilot-v2.js (does NOT touch data/quiz-engine-pilot.js)
and a machine-readable funnel-stats JSON consumed by the separate v1-vs-v2
comparison report builder. Does not modify app.js, index.html, data/quiz.js,
styles, or wire anything into the running app.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ENGINE_DIR = Path("/Users/micahnichols/Downloads/Reads_Football_Data_Engine_v4.0")
sys.path.insert(0, str(ENGINE_DIR))
import game_factory as gf  # Engine's own compile/feasibility/generate/QA logic

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "data" / "quiz-engine-pilot-v2.js"
FUNNEL_STATS_PATH = REPO_ROOT / "tools" / "backups" / "pilot_v2_funnel_stats.json"

SEED = "reads-quiz-engine-pilot-v1"  # unchanged from v1, per instructions
TARGET_COUNT = 100
CANDIDATE_LIMIT = 500  # unchanged from v1; the alias fix alone is enough to clear 100 (verified below)

ID_START = 200000  # distinct from v1's 100000-100049 range and quiz.js's 1-533 range

DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}
CATEGORY_MAP = {"DRAFTED_BY": "NFL Draft History"}
REQUIRED_DOMAIN = "NFL_DRAFT"
REQUIRED_SOURCE = "NFLVERSE_DATA"


def check_production_safety(c) -> dict:
    cov = c.execute(
        "SELECT domain_id,competition_id,dataset_name,coverage_start,coverage_end,"
        "completeness,production_safe,source_id FROM data_coverage WHERE domain_id=?",
        (REQUIRED_DOMAIN,),
    ).fetchone()
    if not cov or not cov["production_safe"]:
        raise SystemExit(f"ABORT: {REQUIRED_DOMAIN} is not marked production_safe in data_coverage.")
    src = c.execute(
        "SELECT source_id,source_name,approved_for_import FROM sources WHERE source_id=?",
        (cov["source_id"],),
    ).fetchone()
    if not src or not src["approved_for_import"]:
        raise SystemExit(f"ABORT: source {cov['source_id']} is not approved_for_import.")
    return {
        "domain_id": cov["domain_id"], "competition_id": cov["competition_id"],
        "dataset_name": cov["dataset_name"], "coverage_start": cov["coverage_start"],
        "coverage_end": cov["coverage_end"], "completeness": cov["completeness"],
        "production_safe": bool(cov["production_safe"]), "source_id": src["source_id"],
        "source_name": src["source_name"], "approved_for_import": bool(src["approved_for_import"]),
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


def main():
    c = gf.connect()
    safety = check_production_safety(c)

    spec = {
        "description": "which team drafted this nfl player",
        "competition_id": "NFL", "mechanic": "guess",
        "entity_type": "nfl_player", "relationship_predicate": "DRAFTED_BY",
        "object_type": "team", "answer_type": "team", "group_size": 4, "filters": {},
    }
    feas = gf.feasibility(spec)
    if feas["status"] != "SUPPORTED":
        raise SystemExit(f"ABORT: Engine feasibility() returned {feas['status']}, not SUPPORTED.")

    rows, feas2 = gf.generate_candidates(spec, limit=CANDIDATE_LIMIT, seed=SEED)

    considered = len(rows)
    rejected_counts = Counter()
    accepted = []
    seen_player_ids = set()
    seen_questions = set()

    rng = gf.seeded(f"{SEED}:distractors")

    for payload, diff, amb, sources in rows:
        issues = gf.qa_candidate(payload)
        if any(i["severity"] == "ERROR" for i in issues):
            rejected_counts[f"ENGINE_QA_{issues[0]['issue_type']}"] += 1
            continue

        entity_id = payload["entity"]["id"]

        if entity_id in seen_player_ids:
            rejected_counts["DUPLICATE_PLAYER"] += 1
            continue

        row = c.execute(
            "SELECT draft_team,draft_season,player_name,verification_status,source_id "
            "FROM draft_facts WHERE player_key=?",
            (entity_id,),
        ).fetchone()
        if not row:
            rejected_counts["ROW_NOT_FOUND"] += 1
            continue
        if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
            rejected_counts["ROW_NOT_VERIFIED"] += 1
            continue
        if row["draft_team"] != payload["answer_id"]:
            rejected_counts["ANSWER_MISMATCH"] += 1
            continue

        season = row["draft_season"]
        if season is None:
            rejected_counts["MISSING_SEASON"] += 1
            continue

        correct, err = resolve_franchise(c, row["draft_team"], season)
        if err:
            rejected_counts[err] += 1
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

        question = f"Which NFL team drafted {row['player_name']}?"
        if question in seen_questions:
            rejected_counts["DUPLICATE_QUESTION"] += 1
            continue

        order = list(range(4))
        rng.shuffle(order)
        shuffled_options = [options[i] for i in order]
        correct_index = shuffled_options.index(correct["full_name"])

        band = gf.band(diff)
        difficulty = DIFFICULTY_MAP[band]
        category = CATEGORY_MAP["DRAFTED_BY"]

        accepted.append(
            {
                "id": ID_START + len(accepted),
                "category": category, "difficulty": difficulty, "question": question,
                "options": shuffled_options, "correctIndex": correct_index, "notes": "",
                "_audit": {
                    "player_key": entity_id, "player_name": row["player_name"],
                    "draft_team_code": row["draft_team"], "draft_season": season,
                    "franchise_id": correct["franchise_id"], "correct_answer_text": correct["full_name"],
                    "difficulty_score": round(diff, 4), "difficulty_band": band,
                    "source_table": sources[0] if sources else None,
                    "verification_status": row["verification_status"], "source_id": row["source_id"],
                    "engine_qa_issues": issues,
                },
            }
        )
        seen_player_ids.add(entity_id)
        seen_questions.add(question)

    c.close()

    exported = accepted[:TARGET_COUNT]
    accepted_but_not_exported = max(0, len(accepted) - len(exported))
    shortfall_reason = None
    if len(exported) < TARGET_COUNT:
        shortfall_reason = (
            f"Only {len(accepted)} candidates passed every validation rule within a "
            f"{CANDIDATE_LIMIT}-candidate deterministic sample; exported the maximum "
            f"available ({len(exported)}) rather than loosen any rule to reach 100."
        )

    contract_failures = []
    for q in exported:
        keys = set(q.keys()) - {"_audit"}
        if keys != {"id", "category", "difficulty", "question", "options", "correctIndex", "notes"}:
            contract_failures.append((q["id"], "unexpected key set")); continue
        if not isinstance(q["id"], int):
            contract_failures.append((q["id"], "id not int"))
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

    dup_questions = [t for t, n in Counter(q["question"] for q in exported).items() if n > 1]
    dup_players = [p for p, n in Counter(q["_audit"]["player_key"] for q in exported).items() if n > 1]
    dup_ids = [i for i, n in Counter(q["id"] for q in exported).items() if n > 1]

    write_output_js(exported)

    by_category = Counter(q["category"] for q in exported)
    by_difficulty = Counter(q["difficulty"] for q in exported)
    seasons = [q["_audit"]["draft_season"] for q in exported]
    franchises = sorted(set(q["_audit"]["franchise_id"] for q in exported))

    funnel_stats = {
        "seed": SEED,
        "candidate_limit": CANDIDATE_LIMIT,
        "target_count": TARGET_COUNT,
        "safety": safety,
        "feasibility": {"status": feas["status"], "estimated_candidates": feas["estimated_candidates"],
                         "reason": feas["reason"], "source_table": feas.get("source_table")},
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
        "unique_players": len(set(q["_audit"]["player_key"] for q in exported)),
        "dup_questions": dup_questions,
        "dup_players": dup_players,
        "dup_ids": dup_ids,
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
        "// AUTO-GENERATED PILOT V2 FILE -- do not hand-edit.\n"
        "// Produced by tools/export_quiz_engine_pilot_v2.py from Reads Football Data\n"
        "// Engine v4.0 (game_factory.py, DRAFTED_BY predicate, guess mechanic), after\n"
        "// the 30 SAFE_FIX_AVAILABLE team_aliases corrections in\n"
        "// TEAM_ALIAS_SAFE_FIX_CHANGELOG.md were applied.\n"
        "// Deterministic seed: \"" + SEED + "\". Rerunning the exporter against an\n"
        "// unchanged database reproduces this file byte-for-byte.\n"
        "//\n"
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or\n"
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_PILOT_V2, a\n"
        "// distinct global from window.QUIZ_DATA and window.QUIZ_DATA_ENGINE_PILOT\n"
        "// (Pilot v1), so it cannot collide with either even if loaded by mistake.\n"
        "//\n"
        "// See QUIZ_ENGINE_PILOT_V2_REPORT.md for the full v1-vs-v2 audit trail.\n"
        "window.QUIZ_DATA_ENGINE_PILOT_V2 = "
    )
    body = json.dumps(clean, indent=2, ensure_ascii=False)
    OUT_PATH.write_text(header + body + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
