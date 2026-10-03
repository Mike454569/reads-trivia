"""One-off production seed from the manually reviewed Story Factory corpus."""
from __future__ import annotations
import json

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.reviewed_story_corpus import REVIEWED_CORPUS, ingest_reviewed_corpus
from tools.director_v05.story_to_trivia_factory import _ensure_schema, generate_questions_for_event
from tools.director_v05.story_multiformat import generate_story_formats_for_event

def main():
    c = engine_bootstrap.connect()
    c.execute("PRAGMA busy_timeout=120000")
    _ensure_schema(c)

    result = ingest_reviewed_corpus(c)
    generated_identity = 0
    generated_formats = 0
    per_event = []

    for story in REVIEWED_CORPUS:
        eid = story["event_id"]
        event = c.execute(
            "SELECT event_id FROM universal_event WHERE event_id=?",
            (eid,),
        ).fetchone()
        if not event:
            per_event.append({"event_id": eid, "status": "NOT_INGESTED"})
            continue

        subject = c.execute(
            """SELECT subject_type,subject_id
               FROM universal_event_subject
               WHERE event_id=?
               ORDER BY subject_type,subject_id
               LIMIT 1""",
            (eid,),
        ).fetchone()
        if not subject:
            per_event.append({"event_id": eid, "status": "NO_SUBJECT"})
            continue

        subject_obj = {
            "entity_type": str(subject["subject_type"]),
            "entity_id": str(subject["subject_id"]),
        }

        qs = generate_questions_for_event(
            c,
            "reviewed-seed:" + eid,
            eid,
            subject_obj,
            max_questions=4,
        )
        fmts = generate_story_formats_for_event(
            c,
            candidate_id="reviewed-seed:" + eid,
            event_id=eid,
            subject_type=subject_obj["entity_type"],
            subject_id=subject_obj["entity_id"],
            max_formats=8,
        )
        generated_identity += len(qs)
        generated_formats += int(fmts.get("generated_count") or 0)
        per_event.append({
            "event_id": eid,
            "status": "SEEDED",
            "identity_questions": len(qs),
            "format_questions": int(fmts.get("generated_count") or 0),
        })

    ready = c.execute(
        "SELECT status,COUNT(*) n FROM story_generated_questions GROUP BY status"
    ).fetchall()
    c.close()
    print(json.dumps({
        "ingest": result,
        "generated_identity": generated_identity,
        "generated_formats": generated_formats,
        "question_status": {str(r["status"]): int(r["n"]) for r in ready},
        "events": per_event,
    }, sort_keys=True))

if __name__ == "__main__":
    main()
