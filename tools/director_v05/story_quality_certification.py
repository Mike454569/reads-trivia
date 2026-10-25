"""Fail-closed certification for sourced football-story question artifacts.

This module audits stored artifacts, not article headlines. A rejected question
is quarantined and never counted as certified playable inventory.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter

PLAYABLE = frozenset(("READY_FOR_BANK", "READY_FOR_FORMAT_BANK"))
ROBOTIC = (
    "documented off-field football story", "event label:",
    "classified as a", "verified football event occurred",
    "subject of a documented", "taxonomy", "event type:",
    "verified chain", "structured fact", "this documented football event",
)
SUPPORTED_MECHANICS = frozenset((
    "MULTIPLE_CHOICE", "FACT_OR_FAKE", "PROGRESSIVE_CLUE",
    "SORTING_TIMELINE", "MATCHING", "BEFORE_AFTER",
))


def _normalize(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _strings(question):
    values = [question.get("question"), question.get("explanation")]
    values += question.get("context_clues") or []
    for clue in question.get("clues") or []:
        values.append(clue.get("text") if isinstance(clue, dict) else clue)
    for entry in question.get("items") or []:
        values.append(entry.get("label") if isinstance(entry, dict) else entry)
    return [_normalize(v) for v in values if isinstance(v, str) and v.strip()]


def certify_question(question, *, expected_event_id=None):
    """Return a stable list of defects. No guesses or automated rewrites."""
    defects = []
    if not isinstance(question, dict):
        return ["INVALID_QUESTION_JSON"]
    mechanic = str(question.get("mechanic") or "")
    if mechanic not in SUPPORTED_MECHANICS:
        defects.append("UNSUPPORTED_MECHANIC")
    if not question.get("question_id") or not question.get("event_id"):
        defects.append("MISSING_IDENTIFIERS")
    if expected_event_id and str(question.get("event_id")) != str(expected_event_id):
        defects.append("WRONG_EVENT_ID")
    if question.get("sensitive") is True:
        defects.append("SENSITIVE_QUESTION")
    if not isinstance(question.get("answer"), dict) or not question["answer"].get("id"):
        defects.append("MISSING_ANSWER")
    provenance = question.get("provenance")
    if not (isinstance(provenance, dict)
            and provenance.get("provenance_complete") is True
            and provenance.get("evidence")
            and str(question.get("event_id")) in set(map(str, provenance.get("event_ids") or []))):
        defects.append("INCOMPLETE_SOURCE_PROVENANCE")
    texts = _strings(question)
    if not texts or not _normalize(question.get("question")):
        defects.append("MISSING_PLAYER_COPY")
    if any(token in text for text in texts for token in ROBOTIC):
        defects.append("ROBOTIC_COPY")
    if any(len(text) > 500 for text in texts):
        defects.append("OVERLONG_COPY")

    answer = question.get("answer") or {}
    answer_label = _normalize(answer.get("label")) if isinstance(answer, dict) else ""
    options = question.get("options")
    if mechanic == "MULTIPLE_CHOICE":
        if not isinstance(options, list) or len(options) != 4:
            defects.append("MCQ_NEEDS_FOUR_OPTIONS")
        elif len({_normalize(x) for x in options}) != 4:
            defects.append("DUPLICATE_OPTIONS")
        elif answer_label not in {_normalize(x) for x in options}:
            defects.append("ANSWER_NOT_IN_OPTIONS")
        if question.get("question_family") == "LORE_IDENTITY":
            clues = question.get("clues") or []
            if len(clues) < 3:
                defects.append("INSUFFICIENT_CLUES")
            elif any(not _normalize(c.get("text") if isinstance(c, dict) else c) for c in clues):
                defects.append("EMPTY_CLUE")
            elif answer_label and any(
                answer_label in _normalize(c.get("text") if isinstance(c, dict) else c)
                for c in clues
            ):
                defects.append("ANSWER_LEAK_IN_CLUES")
    elif mechanic == "PROGRESSIVE_CLUE":
        clues = question.get("clues") or []
        bodies = [_normalize(x.get("text") if isinstance(x, dict) else x) for x in clues]
        specific = [x for x in bodies if x and not x.startswith(("league:", "season:"))]
        if len(bodies) < 3 or len(specific) < 2:
            defects.append("INSUFFICIENT_DISTINCT_IDENTITY_FACTS")
        if len(set(bodies)) != len(bodies):
            defects.append("DUPLICATE_IDENTITY_CLUES")
        if not all(bodies):
            defects.append("EMPTY_CLUE")
        if answer_label and any(answer_label in x for x in bodies):
            defects.append("ANSWER_LEAK_IN_CLUES")
    elif mechanic == "FACT_OR_FAKE":
        if answer.get("id") not in ("FACT", "FAKE"):
            defects.append("INVALID_BOOLEAN_ANSWER")
        if question.get("mutation") is None and answer.get("id") == "FAKE":
            defects.append("FAKE_WITHOUT_PROVEN_MUTATION")
    return sorted(set(defects))


def certify_event_questions(c, event_id, *, quarantine=True):
    """Audit all stored questions for one event; fail closed per artifact."""
    rows = c.execute(
        "SELECT question_id,status,question_json FROM story_generated_questions WHERE event_id=?",
        (str(event_id),),
    ).fetchall()
    seen = {}
    details = []
    counts = Counter()
    for row in rows:
        qid = str(row["question_id"])
        try:
            q = json.loads(row["question_json"])
            defects = certify_question(q, expected_event_id=event_id)
        except (TypeError, ValueError, KeyError):
            q = None
            defects = ["INVALID_QUESTION_JSON"]
        if isinstance(q, dict):
            if str(q.get("question_id")) != qid:
                defects.append("QUESTION_ID_MISMATCH")
            fingerprint = hashlib.sha256(
                (_normalize(q.get("question")) + "|" +
                 json.dumps(q.get("answer"), sort_keys=True, default=str)).encode()
            ).hexdigest()
            if fingerprint in seen:
                defects.append("DUPLICATE_QUESTION_STEM_AND_ANSWER")
            else:
                seen[fingerprint] = qid
        defects = sorted(set(defects))
        if defects:
            counts["rejected"] += 1
            for defect in defects:
                counts["reason_" + defect] += 1
            if quarantine:
                c.execute(
                    "UPDATE story_generated_questions SET status='NEEDS_EDITORIAL_REVIEW' WHERE question_id=?",
                    (qid,),
                )
        else:
            counts["passed"] += 1
        details.append({"question_id": qid, "passed": not defects, "reasons": defects})
    if quarantine:
        c.commit()
    return {"passed": counts["passed"], "rejected": counts["rejected"],
            "rejection_reasons": {k[7:]: v for k, v in counts.items() if k.startswith("reason_")},
            "questions": details}
