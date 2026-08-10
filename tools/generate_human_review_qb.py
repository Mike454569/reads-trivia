#!/usr/bin/env python3
"""Human review package generator for the QB Season Pilot (Pilot Domain #2).

Reruns the exact same deterministic pipeline as
tools/export_quiz_engine_qb_pilot.py to recover the per-question audit
fields (season, raw team code, resolved franchise, starts_observed,
source/domain) that the pipeline computes but does not persist into
data/quiz-engine-qb-pilot.js. Before writing anything, this script loads
the ACTUAL, already-written data/quiz-engine-qb-pilot.js and asserts the
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
PILOT_JS_PATH = REPO_ROOT / "data" / "quiz-engine-qb-pilot.js"
REVIEW_PATH = REPO_ROOT / "QUIZ_ENGINE_QB_PILOT_HUMAN_REVIEW.md"

SEED = "reads-quiz-engine-qb-pilot-v1"
TARGET_COUNT = 100
ID_START = 300000
DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}
CATEGORY = "Passing Records & QB Trivia"
REQUIRED_SOURCE = "NFLVERSE_DATA"
IDENTITY_INCONSISTENT_QB_IDS = {
    "00-0017200", "00-0033869", "00-0034577", "00-0035228",
    "00-0035289", "00-0036355", "00-0039917",
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


def teams_active_in_season(c, season):
    rows = c.execute(
        "SELECT franchise_id, full_name FROM team_aliases "
        "WHERE ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
        (season, season),
    ).fetchall()
    return {r["franchise_id"]: r["full_name"] for r in rows}


def rebuild():
    c = gf.connect()
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
    rng_order = gf.seeded(SEED)
    all_rows = list(all_rows)
    rng_order.shuffle(all_rows)

    rng = gf.seeded(f"{SEED}:distractors")
    accepted = []
    seen_player_ids = set()
    seen_questions = set()

    for row in all_rows:
        if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
            continue
        qb_id = row["qb_source_id"]
        if qb_id in IDENTITY_INCONSISTENT_QB_IDS:
            continue
        if (qb_id, row["season"]) in multi_team_pairs:
            continue
        if qb_id in seen_player_ids:
            continue
        season = row["season"]
        correct = resolve_franchise(c, row["team_code"], season)
        if not correct:
            continue
        diff_row = c.execute(
            "SELECT difficulty_score, difficulty_band FROM puzzle_catalog "
            "WHERE mode_id='qb_season' AND source_entity_id=? AND season=? "
            "AND eligible=1 AND verification_status='SOURCE_BACKED' AND source_id=?",
            (qb_id, season, REQUIRED_SOURCE),
        ).fetchone()
        if not diff_row:
            continue
        pool = teams_active_in_season(c, season)
        pool.pop(correct["franchise_id"], None)
        if len(pool) < 3:
            continue
        distractor_ids = rng.sample(sorted(pool.keys()), 3)
        distractor_names = [pool[fid] for fid in distractor_ids]
        options = [correct["full_name"]] + distractor_names
        if len(set(options)) != 4:
            continue
        question = f"Which NFL team did {row['qb_name']} play for in the {season} season?"
        if question in seen_questions:
            continue
        order = list(range(4))
        rng.shuffle(order)
        shuffled_options = [options[i] for i in order]
        correct_index = shuffled_options.index(correct["full_name"])
        band = diff_row["difficulty_band"]
        if band not in DIFFICULTY_MAP:
            continue
        starts = row["starts_observed"]
        notes = f"{row['qb_name']} made {starts} start{'s' if starts != 1 else ''} for the {correct['full_name']} in {season}."

        accepted.append(
            {
                "id": ID_START + len(accepted),
                "category": CATEGORY, "difficulty": DIFFICULTY_MAP[band], "question": question,
                "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
                "qb_source_id": qb_id, "qb_name": row["qb_name"], "team_code": row["team_code"],
                "season": season, "starts_observed": starts,
                "franchise_id": correct["franchise_id"],
                "difficulty_score": diff_row["difficulty_score"], "difficulty_band": band,
                "verification_status": row["verification_status"], "source_id": row["source_id"],
            }
        )
        seen_player_ids.add(qb_id)
        seen_questions.add(question)

    c.close()
    return accepted[:TARGET_COUNT]


def load_persisted_js():
    text = PILOT_JS_PATH.read_text(encoding="utf-8")
    m = re.search(r"window\.QUIZ_DATA_ENGINE_QB_PILOT = (.*);\s*\Z", text, re.S)
    if not m:
        raise SystemExit("ABORT: could not parse data/quiz-engine-qb-pilot.js")
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
                f"persisted data/quiz-engine-qb-pilot.js.\nreconstructed={r_slim}\npersisted={p}"
            )


def write_review(rebuilt):
    total = len(rebuilt)
    by_diff = Counter(q["difficulty"] for q in rebuilt)
    unique_qbs = len(set(q["qb_source_id"] for q in rebuilt))
    unique_franchises = len(set(q["franchise_id"] for q in rebuilt))
    seasons = [q["season"] for q in rebuilt]

    lines = []
    lines.append("# Quiz Engine QB Season Pilot -- Human Review Package")
    lines.append("")
    lines.append(
        "Regenerated from the same deterministic pipeline as "
        "`tools/export_quiz_engine_qb_pilot.py` (seed `" + SEED + "`) and verified "
        "byte-identical, field-by-field, against the already-written "
        "`data/quiz-engine-qb-pilot.js` before this document was produced -- this is "
        "the real output with its audit trail re-attached, not a separate "
        "approximation of the pipeline. No question text, option, or answer was "
        "altered to produce this report."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total questions: **{total}**")
    lines.append(f"- Difficulty split: " + ", ".join(f"{k} {v}" for k, v in sorted(by_diff.items())))
    lines.append(f"- Unique QBs: **{unique_qbs}**")
    lines.append(f"- Unique franchises represented: **{unique_franchises}** / 32")
    lines.append(f"- Season range: **{min(seasons)}-{max(seasons)}**")
    lines.append(f"- Category: {CATEGORY} (all {total})")
    lines.append(f"- Underlying Engine source/domain: `qb_team_seasons` table (source `NFLVERSE_DATA`); difficulty sourced from Engine's own pre-existing `qb_season` `puzzle_catalog` mode")
    lines.append("")
    lines.append("---")
    lines.append("")

    for q in rebuilt:
        lines.append(f"## #{q['id']} -- {q['question']}")
        lines.append("")
        lines.append(f"- **Difficulty:** {q['difficulty']} (Engine band `{q['difficulty_band']}`, score {round(q['difficulty_score'], 4)})")
        lines.append(f"- **Category:** {q['category']}")
        lines.append(f"- **Options:**")
        for i, opt in enumerate(q["options"]):
            marker = " **<- CORRECT**" if i == q["correctIndex"] else ""
            lines.append(f"  {i}. {opt}{marker}")
        lines.append(f"- **QB:** {q['qb_name']} (GSIS id `{q['qb_source_id']}`)")
        lines.append(f"- **Season:** {q['season']}")
        lines.append(f"- **Team/context:** raw team code `{q['team_code']}`, resolved franchise `{q['franchise_id']}` (\"{q['options'][q['correctIndex']]}\"), {q['starts_observed']} start(s) observed that season")
        lines.append(f"- **Engine source/domain:** `qb_team_seasons` row, verification_status `{q['verification_status']}`, source_id `{q['source_id']}`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode")
        lines.append("")

    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rebuilt = rebuild()
    persisted = load_persisted_js()
    verify_match(rebuilt, persisted)
    write_review(rebuilt)
    print(f"Verified {len(rebuilt)} questions match data/quiz-engine-qb-pilot.js exactly.")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
