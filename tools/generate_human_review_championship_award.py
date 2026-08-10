#!/usr/bin/env python3
"""Human review package generator for the Championship/Award Pilot (Pilot
Domain #3).

Reruns the exact same deterministic pipeline as
tools/export_quiz_engine_championship_award_pilot.py to recover the
per-question audit fields (season, team, record, outcome, source/domain)
that the pipeline computes but does not persist into
data/quiz-engine-championship-award-pilot.js. Before writing anything, this
script loads the ACTUAL, already-written output file and asserts the
reconstruction matches it exactly, field by field, for all 100 questions.
If there is any mismatch, it aborts instead of writing a review that could
misrepresent the real output.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ENGINE_DIR = Path("/Users/micahnichols/Downloads/Reads_Football_Data_Engine_v4.0")
sys.path.insert(0, str(ENGINE_DIR))
import game_factory as gf

REPO_ROOT = Path(__file__).resolve().parent.parent
PILOT_JS_PATH = REPO_ROOT / "data" / "quiz-engine-championship-award-pilot.js"
REVIEW_PATH = REPO_ROOT / "QUIZ_ENGINE_CHAMPIONSHIP_AWARD_PILOT_HUMAN_REVIEW.md"

SEED = "reads-quiz-engine-championship-award-pilot-v1"
TARGET_COUNT = 100
ID_START = 400000
DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}
CATEGORY = "Playoffs & Postseason Moments"
REQUIRED_SOURCE = "NFLVERSE_DATA"
OUTCOME_LABELS = {
    "WonSB": "Won the Super Bowl", "LostSB": "Lost the Super Bowl",
    "LostCC": "Lost in the Conference Championship", "LostDV": "Lost in the Divisional Round",
    "LostWC": "Lost in the Wild Card Round",
}


def resolve_franchise(c, team_code, season):
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE team_code=? AND ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (team_code, season, season),
    ).fetchall()
    if len(rows) != 1:
        return None
    return {"franchise_id": rows[0]["franchise_id"], "full_name": rows[0]["full_name"]}


def rebuild():
    c = gf.connect()
    all_rows = c.execute(
        "SELECT season, team_code, wins, losses, ties, playoff_result, "
        "verification_status, source_id FROM season_standings "
        "WHERE playoff_result IS NOT NULL ORDER BY season, team_code"
    ).fetchall()
    rng_order = gf.seeded(SEED)
    all_rows = list(all_rows)
    rng_order.shuffle(all_rows)

    rng = gf.seeded(f"{SEED}:distractors")
    accepted = []
    seen_questions = set()

    for row in all_rows:
        if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
            continue
        outcome = row["playoff_result"]
        if outcome not in OUTCOME_LABELS:
            continue
        season = row["season"]
        franchise = resolve_franchise(c, row["team_code"], season)
        if not franchise:
            continue
        diff_row = c.execute(
            "SELECT difficulty_score, difficulty_band, payload_json FROM puzzle_catalog "
            "WHERE mode_id='playoff_result' AND source_entity_id=? AND season=? "
            "AND eligible=1 AND verification_status='SOURCE_BACKED' AND source_id=?",
            (row["team_code"], season, REQUIRED_SOURCE),
        ).fetchone()
        if not diff_row:
            continue
        if json.loads(diff_row["payload_json"]).get("answer") != outcome:
            continue
        correct_label = OUTCOME_LABELS[outcome]
        other_labels = [lab for code, lab in OUTCOME_LABELS.items() if code != outcome]
        distractor_labels = rng.sample(other_labels, 3)
        options = [correct_label] + distractor_labels
        if len(set(options)) != 4:
            continue
        question = f"How did the {franchise['full_name']} finish the {season} NFL season?"
        if question in seen_questions:
            continue
        order = list(range(4))
        rng.shuffle(order)
        shuffled_options = [options[i] for i in order]
        correct_index = shuffled_options.index(correct_label)
        band = diff_row["difficulty_band"]
        if band not in DIFFICULTY_MAP:
            continue
        wins, losses, ties = row["wins"], row["losses"], row["ties"]
        if wins is None or losses is None:
            continue
        record = f"{wins}-{losses}" + (f"-{ties}" if ties else "")
        notes = f"The {franchise['full_name']} went {record} in {season} and {correct_label[0].lower()}{correct_label[1:]}."

        accepted.append(
            {
                "id": ID_START + len(accepted),
                "category": CATEGORY, "difficulty": DIFFICULTY_MAP[band], "question": question,
                "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
                "team_code": row["team_code"], "season": season, "record": record,
                "playoff_result": outcome, "franchise_id": franchise["franchise_id"],
                "difficulty_score": diff_row["difficulty_score"], "difficulty_band": band,
                "verification_status": row["verification_status"], "source_id": row["source_id"],
            }
        )
        seen_questions.add(question)

    c.close()
    return accepted[:TARGET_COUNT]


def load_persisted_js():
    text = PILOT_JS_PATH.read_text(encoding="utf-8")
    m = re.search(r"window\.QUIZ_DATA_ENGINE_CHAMPIONSHIP_AWARD_PILOT = (.*);\s*\Z", text, re.S)
    if not m:
        raise SystemExit("ABORT: could not parse data/quiz-engine-championship-award-pilot.js")
    return json.loads(m.group(1))


def verify_match(rebuilt, persisted):
    if len(rebuilt) != len(persisted):
        raise SystemExit(f"ABORT: reconstructed {len(rebuilt)} questions but persisted file has {len(persisted)}.")
    contract_keys = {"id", "category", "difficulty", "question", "options", "correctIndex", "notes"}
    for i, (r, p) in enumerate(zip(rebuilt, persisted)):
        r_slim = {k: r[k] for k in contract_keys}
        if r_slim != p:
            raise SystemExit(
                f"ABORT: mismatch at index {i} between reconstructed pipeline and "
                f"persisted data/quiz-engine-championship-award-pilot.js.\n"
                f"reconstructed={r_slim}\npersisted={p}"
            )


def write_review(rebuilt):
    total = len(rebuilt)
    by_diff = Counter(q["difficulty"] for q in rebuilt)
    unique_franchises = len(set(q["franchise_id"] for q in rebuilt))
    seasons = [q["season"] for q in rebuilt]

    lines = []
    lines.append("# Quiz Engine Championship/Award Pilot -- Human Review Package")
    lines.append("")
    lines.append(
        "Regenerated from the same deterministic pipeline as "
        "`tools/export_quiz_engine_championship_award_pilot.py` (seed `" + SEED + "`) and "
        "verified byte-identical, field-by-field, against the already-written "
        "`data/quiz-engine-championship-award-pilot.js` before this document was produced "
        "-- this is the real output with its audit trail re-attached, not a separate "
        "approximation of the pipeline. No question text, option, or answer was altered "
        "to produce this report."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total questions: **{total}**")
    lines.append(f"- Difficulty split: " + ", ".join(f"{k} {v}" for k, v in sorted(by_diff.items())))
    lines.append(f"- Unique franchises represented: **{unique_franchises}** / 32")
    lines.append(f"- Season range: **{min(seasons)}-{max(seasons)}**")
    lines.append(f"- Category: {CATEGORY} (all {total})")
    lines.append(f"- Underlying Engine source/domain: `season_standings.playoff_result` (source `NFLVERSE_DATA`); difficulty sourced from Engine's own pre-existing `playoff_result` `puzzle_catalog` mode")
    lines.append("")
    lines.append("---")
    lines.append("")

    for q in rebuilt:
        lines.append(f"## #{q['id']} -- {q['question']}")
        lines.append("")
        lines.append(f"- **Category:** {q['category']}")
        lines.append(f"- **Difficulty:** {q['difficulty']} (Engine band `{q['difficulty_band']}`, score {round(q['difficulty_score'], 4)})")
        lines.append(f"- **Options:**")
        for i, opt in enumerate(q["options"]):
            marker = " **<- CORRECT**" if i == q["correctIndex"] else ""
            lines.append(f"  {i}. {opt}{marker}")
        lines.append(f"- **Season/year:** {q['season']}")
        lines.append(f"- **Team/context:** raw team code `{q['team_code']}`, resolved franchise `{q['franchise_id']}` (\"{q['options'][q['correctIndex']]}\" for {q['season']}), regular-season record {q['record']}, raw outcome code `{q['playoff_result']}`")
        lines.append(f"- **Engine source/domain:** `season_standings` row, verification_status `{q['verification_status']}`, source_id `{q['source_id']}`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode")
        lines.append("")

    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rebuilt = rebuild()
    persisted = load_persisted_js()
    verify_match(rebuilt, persisted)
    write_review(rebuilt)
    print(f"Verified {len(rebuilt)} questions match data/quiz-engine-championship-award-pilot.js exactly.")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
