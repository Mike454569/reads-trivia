"""Bounded backfill for already VERIFIED sourced story events.

Dry-run by default. Never harvests articles, changes event facts, or invents
a missing event date. Explicit --apply is required to write questions.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

from tools.quiz_export import engine
from .story_to_trivia_factory import _ensure_schema as ensure_factory_schema
from .story_multiformat import generate_story_formats_for_event
from .story_quality_certification import certify_event_questions


def candidates(conn, *, limit=50):
    """Only sourced non-sensitive verified stories with a real candidate link."""
    return conn.execute(
        """SELECT e.event_id, q.candidate_id, s.subject_type, s.subject_id,
                         e.league
           FROM universal_event e
           JOIN universal_event_subject s ON s.event_id=e.event_id
           JOIN football_story_enrichment q ON q.promoted_event_id=e.event_id
           WHERE e.verification_status='VERIFIED' AND COALESCE(e.sensitive,0)=0
             AND UPPER(e.league) IN ('NFL','CFB')
             AND q.decision='AUTO_PROMOTED'
             AND (SELECT COUNT(*) FROM story_generated_questions g
                  WHERE g.event_id=e.event_id AND
                        g.status IN ('READY_FOR_BANK','READY_FOR_FORMAT_BANK')) < 5
           GROUP BY e.event_id
           ORDER BY e.event_id
           LIMIT ?""",
        (max(1, min(int(limit), 500)),)
    ).fetchall()


def backfill(conn, *, limit=50, apply=False):
    rows = candidates(conn, limit=limit)
    summary = Counter()
    summary["eligible_events"] = len(rows)
    if not apply:
        return {"dry_run": True, "counts": dict(summary)}
    for row in rows:
        eid = str(row["event_id"])
        try:
            with conn:
                outcome = generate_story_formats_for_event(
                    conn,
                    candidate_id=row["candidate_id"],
                    event_id=eid,
                    subject_type=row["subject_type"],
                    subject_id=row["subject_id"],
                )
                certified = certify_event_questions(conn, eid, quarantine=True)
            summary["events_processed"] += 1
            summary["questions_generated"] += int(outcome["generated_count"])
            summary["questions_certified"] += int(certified["passed"])
            summary["questions_rejected"] += int(certified["rejected"])
        except Exception:
            # Keep batch checkpoints and report failures; never count a draft
            # as certified or weaken the source/answer safety gates.
            conn.rollback()
            summary["events_failed"] += 1
    return {"dry_run": False, "counts": dict(summary)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    conn = engine.connect()
    try:
        if args.apply:
            ensure_factory_schema(conn)
        print(json.dumps(backfill(conn, limit=args.limit, apply=args.apply), sort_keys=True))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
