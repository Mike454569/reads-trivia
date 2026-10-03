"""Audit human-label coverage for entities used by Deep Lore."""
from __future__ import annotations

from collections import defaultdict

from .entity_labels import resolve_label


ENTITY_TYPES = ("NFL_PLAYER", "CFB_PLAYER", "COACH", "NFL_TEAM", "SCHOOL")


def label_coverage_report(conn, *, sample_limit=25):
    report = {}
    for entity_type in ENTITY_TYPES:
        rows = conn.execute(
            """SELECT subject_id,COUNT(DISTINCT event_id) n
               FROM universal_event_subject
               WHERE subject_type=?
               GROUP BY subject_id
               ORDER BY n DESC,subject_id""",
            (entity_type,),
        ).fetchall()

        resolved = 0
        unresolved = []
        for row in rows:
            sid = str(row["subject_id"])
            label = resolve_label(conn, entity_type, sid)
            if label and str(label).strip() != sid:
                resolved += 1
            elif len(unresolved) < int(sample_limit):
                unresolved.append({
                    "subject_id": sid,
                    "event_count": int(row["n"]),
                })

        total = len(rows)
        report[entity_type] = {
            "total": total,
            "resolved": resolved,
            "unresolved": total - resolved,
            "coverage": round(resolved / max(1, total), 4),
            "unresolved_examples": unresolved,
        }

    total = sum(v["total"] for v in report.values())
    resolved = sum(v["resolved"] for v in report.values())
    return {
        "by_entity_type": report,
        "total_entities": total,
        "resolved_entities": resolved,
        "overall_coverage": round(resolved / max(1, total), 4),
    }
