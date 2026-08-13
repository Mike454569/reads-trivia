"""Exports the full Football Learning Encyclopedia (concepts across every
domain, team scheme profiles, historical statistical leaders, and worked
film-study examples -- see build_encyclopedia_module.py) from the Engine's
structured storage into a static data/learn-encyclopedia.js file, the same
pregenerated-content pattern every other content type in this app uses.

Deliberately a SEPARATE export from export_coverage_module.py / data/
learn-coverages.js -- that module and its lessons/exercises are untouched;
this one adds the broader encyclopedia alongside it. The frontend merges
the two (coverage concepts appear in both files -- learn-coverages.js still
owns their lesson/exercise content, learn-encyclopedia.js additionally
carries their `encyclopedia_fields`/`encyclopedia_source_rows` enrichment
and every other domain's concepts).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402
from tools.learn.build_encyclopedia_module import LEARN_DOMAINS  # noqa: E402

OUT_PATH = REPO_ROOT / "data" / "learn-encyclopedia.js"


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

    team_profile_rows = c.execute(
        "SELECT canonical_id, label, competition_id, payload_json, verification_status "
        "FROM knowledge_nodes WHERE node_type='FB_TEAM_SCHEME_PROFILE'"
    ).fetchall()
    team_scheme_profiles = {}
    for r in team_profile_rows:
        payload = json.loads(r["payload_json"])
        payload["canonical_id"] = r["canonical_id"]
        payload["label"] = r["label"]
        payload["verification_status"] = r["verification_status"]
        team_scheme_profiles[r["canonical_id"]] = payload

    historical_rows = c.execute(
        "SELECT canonical_id, label, payload_json, verification_status "
        "FROM knowledge_nodes WHERE node_type='FB_HISTORICAL_RECORD'"
    ).fetchall()
    historical_records = {}
    for r in historical_rows:
        payload = json.loads(r["payload_json"])
        payload["canonical_id"] = r["canonical_id"]
        payload["label"] = r["label"]
        payload["verification_status"] = r["verification_status"]
        historical_records[r["canonical_id"]] = payload

    film_example_rows = c.execute(
        "SELECT canonical_id, label, payload_json, verification_status "
        "FROM knowledge_nodes WHERE node_type='FB_FILM_EXAMPLE'"
    ).fetchall()
    film_examples = {}
    for r in film_example_rows:
        payload = json.loads(r["payload_json"])
        payload["canonical_id"] = r["canonical_id"]
        payload["label"] = r["label"]
        payload["verification_status"] = r["verification_status"]
        film_examples[r["canonical_id"]] = payload

    c.close()

    payload = {
        "domains": LEARN_DOMAINS,
        "concepts": concepts,
        "relationships": relationships,
        "team_scheme_profiles": team_scheme_profiles,
        "historical_records": historical_records,
        "film_examples": film_examples,
    }

    header = (
        "// Football Learning Encyclopedia -- structured concepts across every football domain\n"
        "// (positions, personnel, formations, route tree, passing concepts, run game, blocking,\n"
        "// pass protection, QB play, defensive fronts/personnel/pressures/philosophy, special teams,\n"
        "// situational football, play calling, scouting, film study, history, geometry, coaching,\n"
        "// officiating, rules, offensive systems), plus NFL/CFB team scheme profiles (lineage-\n"
        "// projected, not confirmed film evidence -- see verification_status on each) and real,\n"
        "// source-cited historical statistical-leader seasons. Exported from the Engine's knowledge\n"
        "// graph -- see tools/learn/build_encyclopedia_module.py for full provenance back to the\n"
        "// source workbook's exact (sheet, row) for every field. Not hand-maintained -- re-run\n"
        "// tools/learn/export_encyclopedia_module.py to regenerate from the DB.\n"
    )
    js = header + "window.LEARN_ENCYCLOPEDIA = " + json.dumps(payload, indent=1) + ";\n"
    OUT_PATH.write_text(js)

    return {
        "out_path": str(OUT_PATH), "concepts": len(concepts), "relationships": len(relationships),
        "team_scheme_profiles": len(team_scheme_profiles), "historical_records": len(historical_records),
        "film_examples": len(film_examples), "bytes": len(js),
    }


if __name__ == "__main__":
    result = export()
    print(json.dumps(result, indent=2))
