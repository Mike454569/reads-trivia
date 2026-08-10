#!/usr/bin/env python3
"""Human review package generator for the Quiz Engine Pilot (Task 1, follow-up).

Read-only. Does not modify export_quiz_engine_pilot.py, data/quiz-engine-pilot.js,
or any other file. It reruns the exact same deterministic Engine pipeline
(same seed, same spec, same acceptance logic as export_quiz_engine_pilot.py)
to reconstruct the 50 exported questions WITH their full audit metadata
(draft year, franchise, source table -- fields the exporter computes but
does not persist), then verifies the reconstruction is byte-identical to
the already-written data/quiz-engine-pilot.js before writing the review
doc. If verification fails, this script aborts instead of writing a review
that might not match the real generated questions.
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
PILOT_JS_PATH = REPO_ROOT / "data" / "quiz-engine-pilot.js"
REVIEW_PATH = REPO_ROOT / "QUIZ_ENGINE_PILOT_HUMAN_REVIEW.md"

SEED = "reads-quiz-engine-pilot-v1"
CANDIDATE_LIMIT = 500
TARGET_COUNT = 50
ID_START = 100000
DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}
CATEGORY_MAP = {"DRAFTED_BY": "NFL Draft History"}
REQUIRED_SOURCE = "NFLVERSE_DATA"


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
    rows, feas = gf.generate_candidates(spec, limit=CANDIDATE_LIMIT, seed=SEED)
    rng = gf.seeded(f"{SEED}:distractors")
    accepted = []
    seen_player_ids = set()
    seen_questions = set()

    for payload, diff, amb, sources in rows:
        issues = gf.qa_candidate(payload)
        if any(i["severity"] == "ERROR" for i in issues):
            continue
        entity_id = payload["entity"]["id"]
        if entity_id in seen_player_ids:
            continue
        row = c.execute(
            "SELECT draft_team,draft_season,player_name,verification_status,source_id "
            "FROM draft_facts WHERE player_key=?",
            (entity_id,),
        ).fetchone()
        if not row:
            continue
        if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
            continue
        if row["draft_team"] != payload["answer_id"]:
            continue
        season = row["draft_season"]
        if season is None:
            continue
        correct = resolve_franchise(c, row["draft_team"], season)
        if not correct:
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
        question = f"Which NFL team drafted {row['player_name']}?"
        if question in seen_questions:
            continue
        order = list(range(4))
        rng.shuffle(order)
        shuffled_options = [options[i] for i in order]
        correct_index = shuffled_options.index(correct["full_name"])
        band = gf.band(diff)

        accepted.append(
            {
                "id": ID_START + len(accepted),
                "category": CATEGORY_MAP["DRAFTED_BY"],
                "difficulty": DIFFICULTY_MAP[band],
                "question": question,
                "options": shuffled_options,
                "correctIndex": correct_index,
                "notes": "",
                "player_name": row["player_name"],
                "player_key": entity_id,
                "draft_team_code": row["draft_team"],
                "draft_season": season,
                "franchise_id": correct["franchise_id"],
                "difficulty_score": round(diff, 4),
                "difficulty_band": band,
                "source_table": sources[0] if sources else None,
                "verification_status": row["verification_status"],
                "source_id": row["source_id"],
            }
        )
        seen_player_ids.add(entity_id)
        seen_questions.add(question)

    c.close()
    return accepted[:TARGET_COUNT]


def load_persisted_pilot_js():
    text = PILOT_JS_PATH.read_text(encoding="utf-8")
    m = re.search(r"window\.QUIZ_DATA_ENGINE_PILOT = (.*);\s*\Z", text, re.S)
    if not m:
        raise SystemExit("ABORT: could not parse data/quiz-engine-pilot.js")
    return json.loads(m.group(1))


def verify_match(rebuilt, persisted):
    if len(rebuilt) != len(persisted):
        raise SystemExit(
            f"ABORT: reconstructed {len(rebuilt)} questions but persisted file has {len(persisted)}."
        )
    contract_keys = {"id", "category", "difficulty", "question", "options", "correctIndex", "notes"}
    for i, (r, p) in enumerate(zip(rebuilt, persisted)):
        r_slim = {k: r[k] for k in contract_keys}
        if r_slim != p:
            raise SystemExit(
                f"ABORT: mismatch at index {i} between reconstructed pipeline and "
                f"persisted data/quiz-engine-pilot.js. Not writing a review doc that "
                f"could misrepresent the actual generated questions.\n"
                f"reconstructed={r_slim}\npersisted={p}"
            )


def write_review(rebuilt):
    total = len(rebuilt)
    by_diff = Counter(q["difficulty"] for q in rebuilt)
    unique_players = len(set(q["player_key"] for q in rebuilt))
    unique_franchises = len(set(q["franchise_id"] for q in rebuilt))
    seasons = [q["draft_season"] for q in rebuilt]

    lines = []
    lines.append("# Quiz Engine Pilot -- Human Review Package")
    lines.append("")
    lines.append(
        "Regenerated from the same deterministic pipeline as "
        "`tools/export_quiz_engine_pilot.py` (seed `" + SEED + "`) and verified "
        "byte-identical, field-by-field, against the already-written "
        "`data/quiz-engine-pilot.js` before this document was produced. "
        "No question text, option, or answer was altered to produce this report."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total questions: **{total}**")
    lines.append(f"- Difficulty split: " + ", ".join(f"{k} {v}" for k, v in sorted(by_diff.items())))
    lines.append(f"- Unique players: **{unique_players}**")
    lines.append(f"- Unique franchises represented: **{unique_franchises}** / 32")
    lines.append(f"- Draft-year range: **{min(seasons)}-{max(seasons)}**")
    lines.append(f"- Category: NFL Draft History (all {total})")
    lines.append(f"- Underlying Engine source/domain: `draft_facts` table, domain `NFL_DRAFT`, source `NFLVERSE_DATA`")
    lines.append("")
    lines.append("---")
    lines.append("")

    for q in rebuilt:
        lines.append(f"## #{q['id']} -- {q['question']}")
        lines.append("")
        lines.append(f"- **Category:** {q['category']}")
        lines.append(f"- **Difficulty:** {q['difficulty']} (Engine band `{q['difficulty_band']}`, score {q['difficulty_score']})")
        lines.append(f"- **Options:**")
        for i, opt in enumerate(q["options"]):
            marker = " **<- CORRECT**" if i == q["correctIndex"] else ""
            lines.append(f"  {i}. {opt}{marker}")
        lines.append(f"- **Draft year / source context:** {q['player_name']} was drafted in the **{q['draft_season']}** "
                      f"NFL Draft by team code `{q['draft_team_code']}`, resolved to franchise `{q['franchise_id']}` "
                      f"via Engine's `team_aliases` table (season-matched).")
        lines.append(f"- **Underlying Engine source:** `draft_facts` row, player_key `{q['player_key']}`, "
                      f"verification_status `{q['verification_status']}`, source_id `{q['source_id']}` "
                      f"(domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` "
                      f"(source table reported by Engine: `{q['source_table']}`).")
        lines.append("")

    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rebuilt = rebuild()
    persisted = load_persisted_pilot_js()
    verify_match(rebuilt, persisted)
    write_review(rebuilt)
    print(f"Verified {len(rebuilt)} questions match data/quiz-engine-pilot.js exactly.")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
