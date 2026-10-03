"""Compile verified lore into multiple human-playable trivia formats."""
from __future__ import annotations

import hashlib
import random

from .entity_labels import resolve_label
from .lore_mechanics import compile_common_link, compile_timeline
from .lore_trivia import _season, gameplay_eligibility
from .lore_format_qa import validate_multiformat_question


def _qid(kind, parts):
    seed = "|".join([kind] + [str(x) for x in parts])
    return "qlorefmt_" + hashlib.sha256(seed.encode()).hexdigest()[:24]


def _event(conn, event_id):
    row = conn.execute("SELECT * FROM universal_event WHERE event_id=?", (str(event_id),)).fetchone()
    if not row:
        raise ValueError("UNKNOWN_EVENT")
    event = dict(row)
    gate = gameplay_eligibility(conn, event)
    if not gate["eligible"]:
        raise ValueError("LORE_NOT_GAMEPLAY_ELIGIBLE")
    return event


def compile_common_link_mcq(conn, subject_type, subject_id, *, seed="lore-common-link"):
    base = compile_common_link(conn, subject_type, subject_id, min_events=3, limit=4)
    label = resolve_label(conn, subject_type, subject_id)
    if not label or label == str(subject_id):
        raise ValueError("UNRESOLVED_COMMON_LINK_LABEL")

    rows = conn.execute(
        """SELECT subject_id,COUNT(DISTINCT event_id) n
           FROM universal_event_subject
           WHERE subject_type=? AND subject_id<>?
           GROUP BY subject_id HAVING n>=3
           ORDER BY n DESC,subject_id
           LIMIT 40""",
        (str(subject_type), str(subject_id)),
    ).fetchall()

    distractors = []
    for row in rows:
        other = str(row["subject_id"])
        other_label = resolve_label(conn, subject_type, other)
        if not other_label or other_label == other:
            continue
        # Reject another subject shared by all clue events.
        placeholders = ",".join("?" for _ in base["event_ids"])
        count = conn.execute(
            f"""SELECT COUNT(DISTINCT event_id)
                FROM universal_event_subject
                WHERE subject_type=? AND subject_id=?
                  AND event_id IN ({placeholders})""",
            (str(subject_type), other, *base["event_ids"]),
        ).fetchone()[0]
        if count == len(base["event_ids"]):
            continue
        if other_label.casefold() == label.casefold():
            continue
        distractors.append(other_label)
        if len(distractors) >= 3:
            break

    if len(distractors) < 3:
        raise ValueError("INSUFFICIENT_COMMON_LINK_DISTRACTORS")

    options = [label] + distractors[:3]
    rng = random.Random(str(seed) + "|" + str(subject_type) + "|" + str(subject_id))
    rng.shuffle(options)

    out = {
        "question_id": _qid("COMMON_LINK_MCQ", [subject_type, subject_id] + base["event_ids"]),
        "mechanic": "MULTIPLE_CHOICE",
        "question_family": "LORE_COMMON_LINK",
        "question": "What connects all of these football stories?",
        "clues": [{"text": c} for c in base["clues"]],
        "answer": {"id": str(subject_id), "label": label, "type": str(subject_type)},
        "options": options,
        "event_ids": base["event_ids"],
        "provenance": base["provenance"],
    }
    qa = validate_multiformat_question(out)
    if qa["status"] != "PASSED":
        raise ValueError("MULTIFORMAT_QA_FAILED:" + ",".join(qa["errors"]))
    out["qa"] = qa
    return out


def compile_before_after(conn, first_event_id, second_event_id):
    first = _event(conn, first_event_id)
    second = _event(conn, second_event_id)
    s1 = _season(first.get("event_date"))
    s2 = _season(second.get("event_date"))
    if not s1 or not s2 or s1 == s2:
        raise ValueError("BEFORE_AFTER_NEEDS_DISTINCT_SEASONS")

    earlier, later = (first, second) if int(s1) < int(s2) else (second, first)
    earlier_season = min(int(s1), int(s2))
    later_season = max(int(s1), int(s2))

    earlier_title = str(earlier.get("title") or "").strip()
    later_title = str(later.get("title") or "").strip()
    if not earlier_title or not later_title:
        raise ValueError("BEFORE_AFTER_MISSING_EVENT_TITLE")

    out = {
        "question_id": _qid("BEFORE_AFTER", [earlier["event_id"], later["event_id"]]),
        "mechanic": "MULTIPLE_CHOICE",
        "question_family": "LORE_BEFORE_AFTER",
        "question": "Which of these football stories happened first?",
        "clues": [
            {"text": earlier_title},
            {"text": later_title},
        ],
        "answer": {
            "id": str(earlier["event_id"]),
            "label": earlier_title,
            "type": "EVENT",
        },
        "options": [earlier_title, later_title],
        "explanation": f"{earlier_title} happened in {earlier_season}; {later_title} happened in {later_season}.",
        "provenance": {
            "provenance_complete": True,
            "event_ids": [str(earlier["event_id"]), str(later["event_id"])],
        },
    }
    qa = validate_multiformat_question(out)
    if qa["status"] != "PASSED":
        raise ValueError("MULTIFORMAT_QA_FAILED:" + ",".join(qa["errors"]))
    out["qa"] = qa
    return out


def compile_timeline_round(conn, event_ids):
    base = compile_timeline(conn, event_ids)
    items = []
    for item in base["items"]:
        event = _event(conn, item["id"])
        label = str(event.get("title") or "").strip()
        if not label:
            raise ValueError("TIMELINE_MISSING_HUMAN_LABEL")
        items.append({"id": item["id"], "label": label})

    out = {
        "question_id": base["question_id"],
        "mechanic": "SORTING_TIMELINE",
        "question_family": "LORE_TIMELINE",
        "question": "Put these football stories in order from earliest to latest.",
        "items": items,
        "answer_order": base["answer_order"],
        "explanation": base["explanation"],
        "provenance": base["provenance"],
    }
    qa = validate_multiformat_question(out)
    if qa["status"] != "PASSED":
        raise ValueError("MULTIFORMAT_QA_FAILED:" + ",".join(qa["errors"]))
    out["qa"] = qa
    return out


def discover_multiformat_candidates(conn, *, limit=200):
    """Return buildable Common Link, Before/After, and Timeline candidates."""
    out = {"COMMON_LINK": [], "BEFORE_AFTER": [], "TIMELINE": []}

    subjects = conn.execute(
        """SELECT subject_type,subject_id,COUNT(DISTINCT event_id) n
           FROM universal_event_subject
           WHERE subject_type IN ('NFL_PLAYER','CFB_PLAYER','COACH','NFL_TEAM','SCHOOL')
           GROUP BY subject_type,subject_id HAVING n>=3
           ORDER BY n DESC,subject_type,subject_id
           LIMIT ?""",
        (int(limit),),
    ).fetchall()
    for row in subjects:
        try:
            out["COMMON_LINK"].append(
                compile_common_link_mcq(conn, row["subject_type"], row["subject_id"])
            )
        except ValueError:
            pass

    rows = [
        str(r["event_id"]) for r in conn.execute(
            """SELECT event_id FROM universal_event
               WHERE verification_status='VERIFIED' AND event_date IS NOT NULL
               ORDER BY event_date,event_id LIMIT ?""",
            (int(limit),),
        )
    ]

    for i in range(len(rows) - 1):
        try:
            out["BEFORE_AFTER"].append(compile_before_after(conn, rows[i], rows[i+1]))
        except ValueError:
            pass

    for i in range(0, len(rows) - 3, 4):
        try:
            out["TIMELINE"].append(compile_timeline_round(conn, rows[i:i+4]))
        except ValueError:
            pass

    return out
