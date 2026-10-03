"""Generate multiple gameplay formats from promoted story lore.

Chronology formats only use events with real event_date values already stored on
universal_event. Auto-promoted article publication dates are never substituted.
"""
from __future__ import annotations

import json

from .lore_formats import (
    compile_before_after,
    compile_common_link_mcq,
    compile_timeline_round,
)
from .lore_mechanics import compile_fact_or_fake, compile_matching


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _persist(conn, candidate_id, event_id, subject_type, subject_id, question, *, status):
    if "story_generated_questions" not in _tables(conn):
        raise ValueError("STORY_QUESTION_TABLE_MISSING")
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    conn.execute(
        """INSERT OR REPLACE INTO story_generated_questions(
           question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
           difficulty_band,question_json,status,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (
            str(question["question_id"]),
            str(candidate_id),
            str(event_id),
            str(subject_type),
            str(subject_id),
            str(question.get("mechanic") or ""),
            str(question.get("difficulty_band") or "") or None,
            json.dumps(question, sort_keys=True, ensure_ascii=False),
            status,
            now,
        ),
    )


def _dated_subject_events(conn, subject_type, subject_id, *, exclude=(), limit=12):
    exclude = {str(x) for x in exclude}
    rows = conn.execute(
        """SELECT e.event_id
           FROM universal_event e
           JOIN universal_event_subject s ON s.event_id=e.event_id
           WHERE s.subject_type=? AND s.subject_id=?
             AND e.verification_status='VERIFIED'
             AND e.event_date IS NOT NULL
             AND e.sensitive=0
           ORDER BY e.event_date,e.event_id""",
        (str(subject_type), str(subject_id)),
    ).fetchall()
    return [str(r["event_id"]) for r in rows if str(r["event_id"]) not in exclude][:int(limit)]


def generate_story_formats_for_event(
    conn,
    *,
    candidate_id,
    event_id,
    subject_type,
    subject_id,
    max_formats=8,
):
    generated = []
    rejected = []

    # Safe binary event format: only non-sensitive lore reaches this function.
    for fake in (False, True):
        try:
            q = compile_fact_or_fake(conn, event_id, fake=fake)
            _persist(
                conn, candidate_id, event_id, subject_type, subject_id, q,
                status="READY_FOR_FORMAT_BANK",
            )
            generated.append(q)
        except ValueError as exc:
            rejected.append({"format":"FACT_OR_FAKE","reason":str(exc)})

    try:
        q = compile_common_link_mcq(conn, subject_type, subject_id)
        _persist(
            conn, candidate_id, event_id, subject_type, subject_id, q,
            status="READY_FOR_BANK",
        )
        generated.append(q)
    except ValueError as exc:
        rejected.append({"format":"COMMON_LINK","reason":str(exc)})

    dated = _dated_subject_events(conn, subject_type, subject_id, exclude={event_id}, limit=10)
    event_row = conn.execute(
        "SELECT event_date FROM universal_event WHERE event_id=?",
        (str(event_id),),
    ).fetchone()
    story_is_dated = bool(event_row and event_row["event_date"])

    # A reviewed event date unlocks chronology formats containing this story.
    if story_is_dated:
        for other in dated:
            try:
                q = compile_before_after(conn, event_id, other)
                _persist(
                    conn, candidate_id, event_id, subject_type, subject_id, q,
                    status="READY_FOR_FORMAT_BANK",
                )
                generated.append(q)
                break
            except ValueError as exc:
                rejected.append({"format":"BEFORE_AFTER","reason":str(exc)})

        timeline_ids = [event_id] + dated[:6]
        if len(timeline_ids) >= 4:
            # Try small deterministic windows until unique-season QA passes.
            built = False
            for i in range(0, len(timeline_ids) - 3):
                ids = timeline_ids[i:i+4]
                try:
                    q = compile_timeline_round(conn, ids)
                    _persist(
                        conn, candidate_id, event_id, subject_type, subject_id, q,
                        status="READY_FOR_FORMAT_BANK",
                    )
                    generated.append(q)
                    built = True
                    break
                except ValueError as exc:
                    rejected.append({"format":"TIMELINE","reason":str(exc)})
            if not built:
                rejected.append({"format":"TIMELINE","reason":"NO_VALID_DATED_WINDOW"})
    else:
        rejected.append({"format":"BEFORE_AFTER","reason":"STORY_EVENT_DATE_NOT_REVIEWED"})
        rejected.append({"format":"TIMELINE","reason":"STORY_EVENT_DATE_NOT_REVIEWED"})

    conn.commit()
    return {
        "generated": generated[:max(1, int(max_formats))],
        "generated_count": min(len(generated), max(1, int(max_formats))),
        "rejected": rejected,
        "story_event_dated": story_is_dated,
    }


def generate_story_matching_round(conn, *, limit=4):
    """Build a matching round from distinct promoted story subjects."""
    if "football_story_enrichment" not in _tables(conn):
        return {"generated": None, "reason": "ENRICHMENT_TABLE_MISSING"}

    rows = conn.execute(
        """SELECT e.candidate_id,e.promoted_event_id,e.subject_type,e.subject_id
           FROM football_story_enrichment e
           JOIN universal_event u ON u.event_id=e.promoted_event_id
           WHERE e.decision='AUTO_PROMOTED'
             AND e.promoted_event_id IS NOT NULL
             AND u.sensitive=0
           ORDER BY e.processed_at DESC,e.candidate_id"""
    ).fetchall()

    chosen = []
    subjects = set()
    for row in rows:
        key = (str(row["subject_type"]), str(row["subject_id"]))
        if key in subjects:
            continue
        chosen.append(row)
        subjects.add(key)
        if len(chosen) >= max(3, min(int(limit), 8)):
            break

    if len(chosen) < 3:
        return {"generated": None, "reason": "MATCHING_NEEDS_THREE_DISTINCT_STORY_SUBJECTS"}

    ids = [str(r["promoted_event_id"]) for r in chosen]
    try:
        q = compile_matching(conn, ids)
    except ValueError as exc:
        return {"generated": None, "reason": str(exc)}

    first = chosen[0]
    _persist(
        conn,
        first["candidate_id"],
        first["promoted_event_id"],
        first["subject_type"],
        first["subject_id"],
        q,
        status="READY_FOR_FORMAT_BANK",
    )
    conn.commit()
    return {"generated": q, "reason": None}
