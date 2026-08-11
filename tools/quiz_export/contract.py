"""Reads Quiz window.QUIZ_DATA contract validation.

This is the QB/Championship pilots' contract check -- a strict superset of
the original Draft-v2 check, which lacked the category-match and
notes-is-string checks. Applying the stronger version uniformly to all
domains only adds checks; it never changes what gets written to a .js file
(contract validation is read-only diagnostics), so this is safe with
respect to the byte-identical-output requirement.

v1.8, Part D/E (mechanic/visual-template separation): OPTIONAL_KEYS adds two
new, genuinely optional fields -- `visual_template` and `visual_payload` --
that a candidate MAY carry alongside the required CONTRACT_KEYS. Additive
only: any candidate that never sets them (every Draft/Championship candidate
today) has a key-set identical to before, so this changes nothing about
existing behavior. See tools/director_v02/visual_templates.py.
"""
from __future__ import annotations

CONTRACT_KEYS = {"id", "category", "difficulty", "question", "options", "correctIndex", "notes"}
OPTIONAL_KEYS = {"visual_template", "visual_payload"}
VALID_DIFFICULTIES = ("Easy", "Medium", "Hard")


def validate_contract(record: dict, allowed_category: str) -> list[tuple]:
    failures = []
    keys = set(record.keys()) - {"_audit"}
    if keys - OPTIONAL_KEYS != CONTRACT_KEYS:
        failures.append((record.get("id"), "unexpected key set"))
        return failures
    if "visual_template" in record and not isinstance(record["visual_template"], str):
        failures.append((record.get("id"), "visual_template not a string"))
    if "visual_payload" in record and record["visual_payload"] is not None and not isinstance(record["visual_payload"], dict):
        failures.append((record.get("id"), "visual_payload not a dict"))
    if not isinstance(record["id"], int):
        failures.append((record["id"], "id not int"))
    if record["category"] != allowed_category:
        failures.append((record["id"], "category not the approved existing category"))
    if record["difficulty"] not in VALID_DIFFICULTIES:
        failures.append((record["id"], "difficulty not in Easy/Medium/Hard"))
    if not isinstance(record["question"], str) or not record["question"].strip():
        failures.append((record["id"], "empty question"))
    if not isinstance(record["options"], list) or len(record["options"]) != 4 or len(set(record["options"])) != 4:
        failures.append((record["id"], "options not exactly 4 unique strings"))
    if not (isinstance(record["correctIndex"], int) and 0 <= record["correctIndex"] <= 3):
        failures.append((record["id"], "correctIndex out of range"))
    else:
        expected = record.get("_audit", {}).get("correct_answer_text")
        if expected is not None and record["options"][record["correctIndex"]] != expected:
            failures.append((record["id"], "correctIndex does not point at the verified correct answer"))
    if not isinstance(record["notes"], str):
        failures.append((record["id"], "notes not a string"))
    return failures


def validate_all(records: list[dict], allowed_category: str) -> list[tuple]:
    out = []
    for r in records:
        out.extend(validate_contract(r, allowed_category))
    return out
