#!/usr/bin/env python3
"""Reads Engine v4 -> NFL Quiz static export adapter (pilot, 50 questions).

Standalone offline script. Imports the Reads Football Data Engine v4.0
Python modules directly (game_factory.py + its underlying QA / data-access
logic) and calls them in-process -- it never starts or calls any of the
Engine's HTTP servers (api_server.py, production_api.py, etc).

Output is data/quiz-engine-pilot.js, matching the existing window.QUIZ_DATA
object contract used by data/quiz.js, but exported under a different global
(window.QUIZ_DATA_ENGINE_PILOT) so it cannot collide with or shadow the real
quiz data while it remains unwired from the running app.

This script does not modify app.js, index.html, data/quiz.js, styles, or any
other existing application file.

Predicate: DRAFTED_BY (NFL player -> drafting team), Game Factory's `guess`
mechanic. Backed by draft_facts (domain NFL_DRAFT, production_safe=1, source
NFLVERSE_DATA, all rows verification_status=SOURCE_BACKED). Team-code ->
franchise resolution (for both the correct answer and the 3 distractor
options) goes through the Engine's own team_aliases table, which is only
season-aware from 2002 onward -- candidates whose (draft_team, draft_season)
can't be resolved to exactly one franchise there are rejected outright. That
2002+ floor is a byproduct of this verification step, not a chosen cutoff.
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
OUT_PATH = REPO_ROOT / "data" / "quiz-engine-pilot.js"
REPORT_PATH = REPO_ROOT / "QUIZ_ENGINE_PILOT_REPORT.md"

SEED = "reads-quiz-engine-pilot-v1"
TARGET_COUNT = 50
CANDIDATE_LIMIT = 500  # deterministic overfetch; audited in full, not just until 50 hit

ID_START = 100000  # existing quiz.js uses ids 1-533; this range can never collide

DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}

# Explicit Engine predicate -> existing Reads Quiz category mapping.
# Right-hand values are verbatim strings already present in data/quiz.js;
# nothing here introduces a new frontend category.
CATEGORY_MAP = {
    "DRAFTED_BY": "NFL Draft History",
}

REQUIRED_DOMAIN = "NFL_DRAFT"
REQUIRED_SOURCE = "NFLVERSE_DATA"


def check_production_safety(c) -> dict:
    """Row-independent, table-level production-safety gate. Aborts the whole
    run (not a per-candidate reject) if either check fails, since every
    candidate below depends on both."""
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
        "domain_id": cov["domain_id"],
        "competition_id": cov["competition_id"],
        "dataset_name": cov["dataset_name"],
        "coverage_start": cov["coverage_start"],
        "coverage_end": cov["coverage_end"],
        "completeness": cov["completeness"],
        "production_safe": bool(cov["production_safe"]),
        "source_id": src["source_id"],
        "source_name": src["source_name"],
        "approved_for_import": bool(src["approved_for_import"]),
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
    """franchise_id -> full_name for every team on record in that season."""
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (season, season),
    ).fetchall()
    out = {}
    for r in rows:
        out[r["franchise_id"]] = r["full_name"]
    return out


def main():
    c = gf.connect()
    safety = check_production_safety(c)

    spec = {
        "description": "which team drafted this nfl player",
        "competition_id": "NFL",
        "mechanic": "guess",
        "entity_type": "nfl_player",
        "relationship_predicate": "DRAFTED_BY",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "filters": {},
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
        # 1. Engine's own QA pass, unmodified.
        issues = gf.qa_candidate(payload)
        if any(i["severity"] == "ERROR" for i in issues):
            rejected_counts[f"ENGINE_QA_{issues[0]['issue_type']}"] += 1
            continue

        entity_id = payload["entity"]["id"]
        entity_label = payload["entity"]["label"]

        if entity_id in seen_player_ids:
            rejected_counts["DUPLICATE_PLAYER"] += 1
            continue

        # 2. Re-fetch the row-level provenance fields (not present on the
        #    guess payload itself) directly from draft_facts.
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

        # 3. Resolve the correct answer to exactly one franchise, season-aware.
        correct, err = resolve_franchise(c, row["draft_team"], season)
        if err:
            rejected_counts[err] += 1
            continue

        # 4. Build the distractor pool: other teams active in that same
        #    season, so no anachronistic or franchise-identity collisions.
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
                "category": category,
                "difficulty": difficulty,
                "question": question,
                "options": shuffled_options,
                "correctIndex": correct_index,
                "notes": "",
                # audit-only fields, stripped before writing quiz-engine-pilot.js
                "_audit": {
                    "player_key": entity_id,
                    "player_name": row["player_name"],
                    "draft_team_code": row["draft_team"],
                    "draft_season": season,
                    "franchise_id": correct["franchise_id"],
                    "correct_answer_text": correct["full_name"],
                    "difficulty_score": round(diff, 4),
                    "difficulty_band": band,
                    "source_table": sources[0] if sources else None,
                    "verification_status": row["verification_status"],
                    "source_id": row["source_id"],
                    "engine_qa_issues": issues,
                },
            }
        )
        seen_player_ids.add(entity_id)
        seen_questions.add(question)

    c.close()

    exported = accepted[:TARGET_COUNT]
    accepted_but_not_exported = max(0, len(accepted) - len(exported))

    # ---- validate every exported object against the QUIZ_DATA contract ----
    contract_failures = []
    for q in exported:
        keys = set(q.keys()) - {"_audit"}
        if keys != {"id", "category", "difficulty", "question", "options", "correctIndex", "notes"}:
            contract_failures.append((q["id"], "unexpected key set"))
            continue
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
            # Independent re-check: the text at correctIndex must equal the
            # franchise name actually resolved for this row via team_aliases,
            # not just "some index in range".
            contract_failures.append((q["id"], "correctIndex does not point at the verified correct answer"))

    # duplicate checks across the exported set
    dup_questions = [
        qtext for qtext, n in Counter(q["question"] for q in exported).items() if n > 1
    ]
    dup_players = [
        pid for pid, n in Counter(q["_audit"]["player_key"] for q in exported).items() if n > 1
    ]
    dup_ids = [i for i, n in Counter(q["id"] for q in exported).items() if n > 1]

    write_output_js(exported)
    write_report(
        safety=safety,
        feas=feas,
        considered=considered,
        rejected_counts=rejected_counts,
        accepted_total=len(accepted),
        exported=exported,
        accepted_but_not_exported=accepted_but_not_exported,
        contract_failures=contract_failures,
        dup_questions=dup_questions,
        dup_players=dup_players,
        dup_ids=dup_ids,
    )

    print(f"Considered: {considered}")
    print(f"Rejected: {sum(rejected_counts.values())}")
    print(f"Accepted (passed all checks): {len(accepted)}")
    print(f"Exported: {len(exported)}")
    print(f"Contract failures: {len(contract_failures)}")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {REPORT_PATH}")


def write_output_js(exported: list[dict]):
    clean = []
    for q in exported:
        clean.append(
            {
                "id": q["id"],
                "category": q["category"],
                "difficulty": q["difficulty"],
                "question": q["question"],
                "options": q["options"],
                "correctIndex": q["correctIndex"],
                "notes": q["notes"],
            }
        )
    header = (
        "// AUTO-GENERATED PILOT FILE -- do not hand-edit.\n"
        "// Produced by tools/export_quiz_engine_pilot.py from Reads Football Data\n"
        "// Engine v4.0 (game_factory.py, DRAFTED_BY predicate, guess mechanic).\n"
        "// Deterministic seed: \"" + SEED + "\". Rerunning the exporter against an\n"
        "// unchanged database reproduces this file byte-for-byte.\n"
        "//\n"
        "// NOT WIRED INTO THE APP: this file is not loaded by index.html or\n"
        "// referenced by app.js. It exposes window.QUIZ_DATA_ENGINE_PILOT, a\n"
        "// distinct global from window.QUIZ_DATA, so it cannot collide with or\n"
        "// shadow the production quiz bank even if it were loaded by mistake.\n"
        "//\n"
        "// See QUIZ_ENGINE_PILOT_REPORT.md for the full audit trail.\n"
        "window.QUIZ_DATA_ENGINE_PILOT = "
    )
    body = json.dumps(clean, indent=2, ensure_ascii=False)
    OUT_PATH.write_text(header + body + ";\n", encoding="utf-8")


def write_report(
    *,
    safety,
    feas,
    considered,
    rejected_counts,
    accepted_total,
    exported,
    accepted_but_not_exported,
    contract_failures,
    dup_questions,
    dup_players,
    dup_ids,
):
    total_rejected = sum(rejected_counts.values())
    by_category = Counter(q["category"] for q in exported)
    by_difficulty = Counter(q["difficulty"] for q in exported)
    seasons = [q["_audit"]["draft_season"] for q in exported]
    franchises = sorted(set(q["_audit"]["franchise_id"] for q in exported))

    lines = []
    lines.append("# Quiz Engine Pilot -- Audit Report")
    lines.append("")
    lines.append(f"Generated by `tools/export_quiz_engine_pilot.py`, seed `{SEED}`.")
    lines.append("Not wired into the running app. Output: `data/quiz-engine-pilot.js`.")
    lines.append("")
    lines.append("## Production-safety gate (checked once, before any candidate generation)")
    lines.append("")
    for k, v in safety.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Engine feasibility check")
    lines.append("")
    lines.append(f"- predicate: `DRAFTED_BY`, mechanic: `guess`")
    lines.append(f"- `game_factory.feasibility()` status: **{feas['status']}**")
    lines.append(f"- estimated candidates (Engine's own estimate): {feas['estimated_candidates']}")
    lines.append(f"- reason: {feas['reason']}")
    lines.append(f"- source table: {feas.get('source_table')}")
    lines.append("")
    lines.append("## Candidate funnel")
    lines.append("")
    lines.append(f"- Candidates considered (raw output of `game_factory.generate_candidates()`, limit={CANDIDATE_LIMIT}): **{considered}**")
    lines.append(f"- Rejected: **{total_rejected}**")
    lines.append(f"- Accepted (passed every check): **{accepted_total}**")
    lines.append(f"- Exported to `quiz-engine-pilot.js` (capped at pilot target): **{len(exported)}**")
    if accepted_but_not_exported:
        lines.append(f"- Accepted but not exported (beyond the {TARGET_COUNT}-question pilot cap): {accepted_but_not_exported}")
    lines.append("")
    lines.append("### Rejection reasons")
    lines.append("")
    if rejected_counts:
        lines.append("| Reason | Count |")
        lines.append("|---|---|")
        for reason, n in rejected_counts.most_common():
            lines.append(f"| {reason} | {n} |")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append(
        "Note: the ~%.0f%% rejection rate is dominated by `TEAM_UNRESOLVED` -- "
        "the Engine's own `team_aliases` team-code resolver only has season-aware "
        "coverage from 2002 onward, so pre-2002 `draft_facts` rows (and a handful "
        "of non-standard historical codes like `STL`/`OAK`/`LARM` outside their "
        "resolvable window) are rejected rather than guessed at. This is a "
        "byproduct of the verification step, not a year cutoff applied by this "
        "script." % (100.0 * total_rejected / max(1, considered))
    )
    lines.append("")
    lines.append("## Exported set breakdown")
    lines.append("")
    lines.append("### Counts by category")
    lines.append("")
    for cat, n in by_category.most_common():
        lines.append(f"- {cat}: {n}")
    lines.append("")
    lines.append("### Counts by difficulty")
    lines.append("")
    for diff, n in by_difficulty.most_common():
        lines.append(f"- {diff}: {n}")
    lines.append("")
    lines.append("### Season range covered")
    lines.append("")
    lines.append(f"- min season: {min(seasons) if seasons else 'n/a'}")
    lines.append(f"- max season: {max(seasons) if seasons else 'n/a'}")
    lines.append(f"- distinct franchises represented: {len(franchises)} / 32")
    lines.append("")
    lines.append("### Source / domain breakdown")
    lines.append("")
    lines.append(f"- domain: `{safety['domain_id']}` (production_safe={safety['production_safe']})")
    lines.append(f"- source: `{safety['source_id']}` ({safety['source_name']}, approved_for_import={safety['approved_for_import']})")
    lines.append(f"- every exported row's underlying `draft_facts` record has verification_status=`SOURCE_BACKED`, source_id=`{REQUIRED_SOURCE}` (checked per-row, not assumed)")
    lines.append(f"- correct-answer and all distractor team names resolved via Engine's `team_aliases` table, season-matched to the player's actual draft year")
    lines.append("")
    lines.append("### Duplicate check")
    lines.append("")
    lines.append(f"- duplicate question text: {len(dup_questions)}" + (f" -- {dup_questions}" if dup_questions else ""))
    lines.append(f"- duplicate player used twice: {len(dup_players)}" + (f" -- {dup_players}" if dup_players else ""))
    lines.append(f"- duplicate id values: {len(dup_ids)}" + (f" -- {dup_ids}" if dup_ids else ""))
    lines.append("")
    lines.append("### QUIZ_DATA contract validation")
    lines.append("")
    if contract_failures:
        lines.append(f"**FAILED** -- {len(contract_failures)} object(s) did not match the contract:")
        for qid, reason in contract_failures:
            lines.append(f"- id {qid}: {reason}")
    else:
        lines.append(
            f"**PASSED** -- all {len(exported)} exported objects have exactly the keys "
            "`id, category, difficulty, question, options, correctIndex, notes`; "
            "`difficulty` in {Easy, Medium, Hard}; `options` has exactly 4 unique "
            "strings; `correctIndex` is a valid 0-3 index pointing at the verified "
            "correct answer; `notes` is `\"\"` for every row (the Engine's "
            "DRAFTED_BY/guess payload has no explanation field, so none was "
            "invented)."
        )
    lines.append("")
    lines.append("## Category mapping table used")
    lines.append("")
    lines.append("| Engine predicate | Reads Quiz category |")
    lines.append("|---|---|")
    for pred, cat in CATEGORY_MAP.items():
        lines.append(f"| `{pred}` | {cat} |")
    lines.append("")
    lines.append("## Difficulty mapping used")
    lines.append("")
    lines.append("| Engine band | Quiz difficulty |")
    lines.append("|---|---|")
    for band, diff in DIFFICULTY_MAP.items():
        lines.append(f"| {band} | {diff} |")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
