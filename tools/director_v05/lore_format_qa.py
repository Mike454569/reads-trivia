"""QA for multi-format Deep Lore questions."""
from __future__ import annotations

import re


def _norm(text):
    return " ".join(str(text or "").casefold().split())


def validate_multiformat_question(question):
    errors = []
    mechanic = str(question.get("mechanic") or "")
    prompt = str(question.get("question") or "").strip()
    if not prompt:
        errors.append("BLANK_PROMPT")

    if mechanic == "MULTIPLE_CHOICE":
        options = list(question.get("options") or [])
        answer = str((question.get("answer") or {}).get("label") or "")
        if len(options) < 2:
            errors.append("TOO_FEW_OPTIONS")
        normalized = [_norm(x) for x in options]
        if len(set(normalized)) != len(normalized):
            errors.append("DUPLICATE_OPTIONS")
        if answer and normalized.count(_norm(answer)) != 1:
            errors.append("ANSWER_NOT_UNIQUE")
        if "BEFORE_AFTER" in str(question.get("question_family") or ""):
            # Event titles shown as choices must not include a four-digit year,
            # otherwise the ordering question answers itself.
            if any(re.search(r"\b(?:19|20)\d{2}\b", str(x)) for x in options):
                errors.append("DATE_LEAK_IN_EVENT_OPTION")

    elif mechanic == "SORTING_TIMELINE":
        items = list(question.get("items") or [])
        answer_order = list(question.get("answer_order") or [])
        ids = [str(x.get("id") or "") for x in items]
        labels = [str(x.get("label") or "") for x in items]
        if len(items) < 4:
            errors.append("TIMELINE_TOO_SHORT")
        if len(set(ids)) != len(ids):
            errors.append("TIMELINE_DUPLICATE_IDS")
        if set(ids) != set(str(x) for x in answer_order):
            errors.append("TIMELINE_SOLUTION_MISMATCH")
        if any(re.search(r"\b(?:19|20)\d{2}\b", x) for x in labels):
            errors.append("DATE_LEAK_IN_TIMELINE_LABEL")
    else:
        errors.append("UNSUPPORTED_MULTI_FORMAT_MECHANIC")

    copy = " ".join([
        prompt,
        *[str(c.get("text") or c) for c in question.get("clues") or []],
    ]).casefold()
    for term in ("verified chain", "structured fact", "subject of event", "event subject"):
        if term in copy:
            errors.append("ROBOTIC_COPY")
            break

    return {"status": "PASSED" if not errors else "FAILED", "errors": errors}
