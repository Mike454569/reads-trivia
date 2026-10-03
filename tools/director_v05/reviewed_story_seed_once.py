"""Fast one-off production seed from the manually reviewed Story corpus."""
from __future__ import annotations
import json

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.reviewed_story_corpus import REVIEWED_CORPUS, ingest_reviewed_corpus
from tools.director_v05.story_to_trivia_factory import _ensure_schema, _persist_question
from tools.director_v05.lore_mechanics import compile_progressive_identity, compile_fact_or_fake
from tools.director_v05.lore_distractors import attach_deep_lore_options


def main():
    c = engine_bootstrap.connect()
    c.execute("PRAGMA busy_timeout=120000")
    _ensure_schema(c)

    result = ingest_reviewed_corpus(c)
    generated_mcq = 0
    generated_fact_fake = 0
    per_event = []

    for story in REVIEWED_CORPUS:
        eid = story["event_id"]
        event = c.execute(
            "SELECT event_id,sensitive FROM universal_event WHERE event_id=?",
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
        event_counts = {"mcq": 0, "fact_fake": 0}
        errors = []

        try:
            q = compile_progressive_identity(c, eid)
            q = attach_deep_lore_options(c, q, difficulty_band="HARD")
            _persist_question(c, "reviewed-seed:" + eid, eid, subject_obj, q)
            generated_mcq += 1
            event_counts["mcq"] += 1
        except ValueError as exc:
            errors.append("MCQ:" + str(exc))

        if not int(event["sensitive"] or 0):
            for fake in (False, True):
                try:
                    q = compile_fact_or_fake(c, eid, fake=fake)
                    _persist_question(c, "reviewed-seed:" + eid, eid, subject_obj, q)
                    generated_fact_fake += 1
                    event_counts["fact_fake"] += 1
                except ValueError as exc:
                    errors.append(("FAKE:" if fake else "FACT:") + str(exc))

        c.commit()
        per_event.append({
            "event_id": eid,
            "status": "SEEDED",
            "generated": event_counts,
            "errors": errors,
        })

    ready = c.execute(
        "SELECT status,mechanic,COUNT(*) n FROM story_generated_questions GROUP BY status,mechanic"
    ).fetchall()
    c.close()

    print(json.dumps({
        "ingest": result,
        "generated_mcq": generated_mcq,
        "generated_fact_fake": generated_fact_fake,
        "generated_total": generated_mcq + generated_fact_fake,
        "question_status": [
            {"status": str(r["status"]), "mechanic": str(r["mechanic"]), "count": int(r["n"])}
            for r in ready
        ],
        "events": per_event,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
