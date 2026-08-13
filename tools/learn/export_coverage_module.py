"""Exports the Defensive Coverages Learn module from the Engine's
structured storage (knowledge_nodes/knowledge_edges + learn_lessons/
learn_exercises -- see build_coverage_module.py) into a static
`data/learn-coverages.js` file, the same pregenerated-content pattern
every other content type in this app already uses (quiz banks, Grid
pools, Legends teams) -- the frontend never queries the Engine DB live
for this, matching this project's own established "do not make users
wait on expensive generation between questions / avoid DB scans in
ordinary gameplay" discipline.

This is a pure export -- run build_coverage_module.py first to populate
the source tables. Re-running this script re-derives the file from
whatever's currently in the DB, so it stays a real reflection of the
structured source of truth, not a hand-maintained duplicate of it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402

MODULE = "defensive_coverages"
OUT_PATH = REPO_ROOT / "data" / "learn-coverages.js"


def export() -> dict:
    c = engine.connect()

    concept_rows = c.execute(
        "SELECT node_id, canonical_id, label, payload_json, verification_status "
        "FROM knowledge_nodes WHERE node_type='FB_CONCEPT'"
    ).fetchall()
    node_id_to_canonical = {r["node_id"]: r["canonical_id"] for r in concept_rows}
    concepts = {}
    for r in concept_rows:
        payload = json.loads(r["payload_json"])
        payload["canonical_id"] = r["canonical_id"]
        payload["label"] = r["label"]
        payload["verification_status"] = r["verification_status"]
        concepts[r["canonical_id"]] = payload

    edge_rows = c.execute(
        "SELECT source_node_id, predicate, target_node_id FROM knowledge_edges "
        "WHERE source_node_id LIKE 'KN|FB_CONCEPT|%'"
    ).fetchall()
    relationships = [
        {"source": node_id_to_canonical[r["source_node_id"]], "predicate": r["predicate"],
         "target": node_id_to_canonical[r["target_node_id"]]}
        for r in edge_rows if r["source_node_id"] in node_id_to_canonical and r["target_node_id"] in node_id_to_canonical
    ]

    lesson_rows = c.execute(
        "SELECT ll.lesson_id, ll.title, ll.summary, ll.difficulty, ll.order_index, "
        "ll.prerequisites_json, ll.steps_json, kn.canonical_id "
        "FROM learn_lessons ll JOIN knowledge_nodes kn ON kn.node_id = ll.concept_node_id "
        "WHERE ll.module=? ORDER BY ll.order_index", (MODULE,)
    ).fetchall()
    lessons = []
    for r in lesson_rows:
        lessons.append({
            "lesson_id": r["lesson_id"], "concept": r["canonical_id"], "title": r["title"],
            "summary": r["summary"], "difficulty": r["difficulty"], "order_index": r["order_index"],
            "prerequisites": json.loads(r["prerequisites_json"]), "steps": json.loads(r["steps_json"]),
        })

    exercise_rows = c.execute(
        "SELECT le.exercise_id, le.exercise_type, le.difficulty, le.prompt, le.structured_data_json, "
        "le.options_json, le.correct_option_index, le.explanation, kn.canonical_id "
        "FROM learn_exercises le JOIN knowledge_nodes kn ON kn.node_id = le.concept_node_id "
        "WHERE le.module=?", (MODULE,)
    ).fetchall()
    exercises = {}
    for r in exercise_rows:
        exercises[r["exercise_id"]] = {
            "concept": r["canonical_id"], "type": r["exercise_type"], "difficulty": r["difficulty"],
            "prompt": r["prompt"], "structured": json.loads(r["structured_data_json"]),
            "options": json.loads(r["options_json"]), "correctIndex": r["correct_option_index"],
            "explanation": r["explanation"],
        }

    c.close()

    payload = {
        "module": MODULE, "concepts": concepts, "relationships": relationships,
        "lessons": lessons, "exercises": exercises,
    }

    header = (
        "// Defensive Coverages Learn module -- structured concepts, relationships, lessons, and\n"
        "// interactive exercises, exported from the Engine's knowledge graph (knowledge_nodes/\n"
        "// knowledge_edges) + learn_lessons/learn_exercises tables. Source: the user's Football 101\n"
        "// Encyclopedia / 700 Question Master workbook (see tools/learn/build_coverage_module.py for\n"
        "// full provenance and the real workbook row citations for every concept below). Not hand-\n"
        "// maintained -- re-run tools/learn/export_coverage_module.py to regenerate from the DB.\n"
    )
    js = header + "window.LEARN_COVERAGE_MODULE = " + json.dumps(payload, indent=2) + ";\n"
    OUT_PATH.write_text(js)

    return {
        "out_path": str(OUT_PATH), "concepts": len(concepts), "relationships": len(relationships),
        "lessons": len(lessons), "exercises": len(exercises), "bytes": len(js),
    }


if __name__ == "__main__":
    result = export()
    print(json.dumps(result, indent=2))
