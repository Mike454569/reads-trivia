"""Read-only Story Factory readiness audit. No harvesting, triage, or writes.

Usage: python -m tools.director_v05.audit_story_inventory --db /data/engine/reads_football_v4.0.sqlite
Output: JSON counts and per-mode readiness. Default thresholds: 200 distinct
verified, source-backed questions per league/compatible mechanic, and 3000
verified events / 20000 playable variants across the entire corpus.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from collections import Counter, defaultdict

TARGET_EVENTS = 3000
TARGET_QUESTIONS = 20000
MODE_MINIMUM = 200
MODE_MAP = {
    ("NFL", "MULTIPLE_CHOICE"): "story_lore_nfl",
    ("CFB", "MULTIPLE_CHOICE"): "story_lore_cfb",
    ("NFL", "PROGRESSIVE_CLUE"): "who_am_i_nfl",
}

def audit(path):
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"story_generated_questions", "universal_event"}.issubset(tables):
            return {"ready": False, "blockers": ["STORY_TABLES_MISSING"], "tables": sorted(tables)}
        events = conn.execute(
            "SELECT COUNT(*) FROM universal_event WHERE verification_status='VERIFIED' AND COALESCE(sensitive,0)=0"
        ).fetchone()[0]
        columns = {r[1] for r in conn.execute("PRAGMA table_info(story_generated_questions)")}
        if not {"question_json", "event_id", "mechanic", "status", "question_id"}.issubset(columns):
            return {"ready": False, "blockers": ["STORY_QUESTION_SCHEMA_INCOMPATIBLE"]}
        rows = conn.execute(
            """SELECT q.question_id,q.question_json,q.event_id,q.mechanic,q.status,
                      UPPER(e.league) AS league,e.verification_status,e.sensitive
               FROM story_generated_questions q
               JOIN universal_event e ON e.event_id=q.event_id"""
        )
        status_counts = Counter()
        mechanic_counts = Counter()
        mode_ids = defaultdict(set)
        rejected = Counter()
        distinct = set()
        for row in rows:
            status_counts[row["status"]] += 1
            if row["status"] not in ("READY_FOR_BANK", "READY_FOR_FORMAT_BANK"):
                rejected["NOT_READY"] += 1
                continue
            if row["verification_status"] != "VERIFIED" or row["sensitive"]:
                rejected["EVENT_NOT_SAFE_VERIFIED"] += 1
                continue
            try:
                q = json.loads(row["question_json"])
                provenance = q.get("provenance") or {}
                answer = q.get("answer") or {}
                if (q.get("event_id") != row["event_id"]
                    or q.get("question_id") != row["question_id"]
                    or q.get("mechanic") != row["mechanic"]
                    or not q.get("question")
                    or q.get("sensitive") is True
                    or not isinstance(provenance, dict)
                    or provenance.get("provenance_complete") is not True
                    or not provenance.get("evidence")
                    or str(row["event_id"]) not in {str(x) for x in provenance.get("event_ids", [])}):
                    rejected["CONTENT_OR_PROVENANCE_INVALID"] += 1
                    continue
                if row["mechanic"] == "MULTIPLE_CHOICE":
                    opts = q.get("options")
                    label = answer.get("label")
                    if (row["status"] != "READY_FOR_BANK"
                        or not isinstance(opts, list) or len(opts) != 4
                        or not all(isinstance(x, str) and x.strip() for x in opts)
                        or len({x.casefold().strip() for x in opts}) != 4
                        or not isinstance(label, str)
                        or sum(x.casefold().strip() == label.casefold().strip() for x in opts) != 1):
                        rejected["INVALID_MULTIPLE_CHOICE"] += 1
                        continue
                elif row["mechanic"] == "PROGRESSIVE_CLUE":
                    clues = q.get("clues")
                    label = answer.get("label")
                    if (not isinstance(clues, list) or not 3 <= len(clues) <= 5
                        or not isinstance(label, str) or not label.strip()
                        or not all(isinstance(x, dict) and isinstance(x.get("text"), str)
                                   and x["text"].strip() and label.casefold() not in x["text"].casefold()
                                   for x in clues)):
                        rejected["INVALID_CLUE_ROUND"] += 1
                        continue
                distinct.add(row["question_id"])
                mechanic_counts[row["mechanic"]] += 1
                mode = MODE_MAP.get((row["league"], row["mechanic"]))
                if mode:
                    mode_ids[mode].add(row["question_id"])
            except (ValueError, TypeError, KeyError, AttributeError):
                rejected["MALFORMED_JSON"] += 1
        modes = {mode: {"eligible": len(mode_ids[mode]),
                         "minimum": MODE_MINIMUM,
                         "ready": len(mode_ids[mode]) >= MODE_MINIMUM}
                 for mode in MODE_MAP.values()}
        blockers = []
        if events < TARGET_EVENTS:
            blockers.append("VERIFIED_EVENTS_BELOW_TARGET")
        if len(distinct) < TARGET_QUESTIONS:
            blockers.append("PLAYABLE_QUESTIONS_BELOW_TARGET")
        for mode, item in modes.items():
            if not item["ready"]:
                blockers.append(f"MODE_INVENTORY_LOW:{mode}")
        return {"ready": not blockers, "verified_non_sensitive_events": events,
                "eligible_distinct_questions": len(distinct),
                "targets": {"events": TARGET_EVENTS, "questions": TARGET_QUESTIONS},
                "modes": modes, "status_counts": dict(status_counts),
                "eligible_mechanics": dict(mechanic_counts),
                "rejection_reasons": dict(rejected), "blockers": blockers}
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.db), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
