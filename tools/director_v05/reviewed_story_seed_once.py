"""Ultrafast production seed from the manually reviewed Story corpus."""
from __future__ import annotations
import hashlib
import json

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.reviewed_story_corpus import REVIEWED_CORPUS, ingest_reviewed_corpus
from tools.director_v05.story_to_trivia_factory import _ensure_schema, _persist_question
from tools.director_v05.lore_mechanics import compile_progressive_identity, compile_fact_or_fake


def _ordered_options(question_id, answer, peers):
    ranked = sorted(
        peers,
        key=lambda x: hashlib.sha256((str(question_id) + "|" + str(x)).encode()).hexdigest(),
    )
    chosen = ranked[:3]
    options = [answer] + chosen
    return sorted(
        options,
        key=lambda x: hashlib.sha256((str(question_id) + "|option|" + str(x)).encode()).hexdigest(),
    )


def main():
    c = engine_bootstrap.connect()
    c.execute("PRAGMA busy_timeout=120000")
    _ensure_schema(c)

    result = ingest_reviewed_corpus(c)

    progressive = {}
    meta = {}
    peer_labels = {}

    # Compile the lightweight story-first artifact once for every successfully
    # ingested reviewed event, and build a same-league/same-type peer pool.
    for story in REVIEWED_CORPUS:
        eid = story["event_id"]
        if not c.execute("SELECT 1 FROM universal_event WHERE event_id=?", (eid,)).fetchone():
            continue
        try:
            q = compile_progressive_identity(c, eid)
        except ValueError:
            continue
        label = str((q.get("answer") or {}).get("label") or "").strip()
        atype = str((q.get("answer") or {}).get("type") or "")
        if not label or not atype:
            continue
        progressive[eid] = q
        meta[eid] = {
            "league": story["league"],
            "subject_type": atype,
            "subject_id": str(q["answer"]["id"]),
        }
        peer_labels.setdefault((story["league"], atype), set()).add(label)

    generated_mcq = 0
    generated_progressive = 0
    generated_fact_fake = 0
    per_event = []

    for story in REVIEWED_CORPUS:
        eid = story["event_id"]
        q = progressive.get(eid)
        if not q:
            per_event.append({"event_id": eid, "status": "NO_PROGRESSIVE"})
            continue

        info = meta[eid]
        subject_obj = {
            "entity_type": info["subject_type"],
            "entity_id": info["subject_id"],
        }
        event_counts = {"mcq": 0, "progressive": 0, "fact_fake": 0}
        errors = []

        answer = str(q["answer"]["label"])
        peers = sorted(
            x for x in peer_labels.get((info["league"], info["subject_type"]), set())
            if x != answer
        )

        if len(peers) >= 3:
            mcq = dict(q)
            mcq["mechanic"] = "MULTIPLE_CHOICE"
            mcq["question"] = "Who am I?"
            mcq["options"] = _ordered_options(q["question_id"], answer, peers)
            mcq["difficulty_band"] = "HARD"
            mcq["distractor_source"] = "REVIEWED_STORY_PEERS"
            _persist_question(c, "reviewed-seed:" + eid, eid, subject_obj, mcq)
            generated_mcq += 1
            event_counts["mcq"] += 1
        else:
            q = dict(q)
            q["difficulty_band"] = "HARD"
            _persist_question(c, "reviewed-seed:" + eid, eid, subject_obj, q)
            generated_progressive += 1
            event_counts["progressive"] += 1
            errors.append("MCQ:INSUFFICIENT_REVIEWED_SAME_LEAGUE_PEERS")

        event = c.execute(
            "SELECT sensitive FROM universal_event WHERE event_id=?", (eid,)
        ).fetchone()
        if event and not int(event["sensitive"] or 0):
            for fake in (False, True):
                try:
                    fq = compile_fact_or_fake(c, eid, fake=fake)
                    fq["difficulty_band"] = "HARD"
                    _persist_question(c, "reviewed-seed:" + eid, eid, subject_obj, fq)
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
        "generated_progressive": generated_progressive,
        "generated_fact_fake": generated_fact_fake,
        "generated_total": generated_mcq + generated_progressive + generated_fact_fake,
        "question_status": [
            {"status": str(r["status"]), "mechanic": str(r["mechanic"]), "count": int(r["n"])}
            for r in ready
        ],
        "events": per_event,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
