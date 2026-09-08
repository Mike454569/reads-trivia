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

Creator/Game Quality Correction pass: VALID_OPTION_COUNTS widens the
options-count check from a hardcoded 4 to {2, 4} -- true head-to-head
comparisons (nfl_game_result.py/cfb_game_result.py's "who won", the CFB
stat-comparison adapters' "who had more") are genuine 2-option questions,
not 4-way multiple choice padded with unrelated distractors. Deliberately
NOT opened to arbitrary N: every adapter in this codebase emits either the
standard 4-way guess or a true binary comparison via
serializer.finalize_binary_options() -- nothing else -- so this stays a
real, closed check, not a loosened one.
"""
from __future__ import annotations

import re

CONTRACT_KEYS = {"id", "category", "difficulty", "question", "options", "correctIndex", "notes"}
OPTIONAL_KEYS = {"visual_template", "visual_payload"}
VALID_DIFFICULTIES = ("Easy", "Medium", "Hard")
VALID_OPTION_COUNTS = (2, 4)

# Player Experience pass (Part 2A): a real, confirmed-live failure class --
# "Which school is Ole Miss's rival in the game known as?" reached
# production because a template unconditionally appended a connective
# phrase ("in the game known as") that only makes grammatical sense when a
# real value follows it. This is a GENERIC template-completeness bug shape
# (a per-adapter string built by conditionally omitting one piece without
# also removing the connective word introducing it), not unique to
# Rivalries -- so the check belongs in this shared, global contract
# validator every adapter's output already passes through
# (game_director_v01.py's `contract.validate_all()`), not bolted onto one
# adapter.
#
# Deliberately NARROW: real English questions routinely end in a stranded
# preposition ("What team does he play for?", "What is this known as?",
# "What position is he at?") -- those are grammatical, not bugs, so a broad
# "any preposition before '?'" check would false-positive across many
# legitimate real adapters. Only words that can NEVER grammatically end an
# English sentence on their own -- bare determiners and coordinating
# conjunctions, which always require a following noun/clause -- are safe
# to flag with zero ambiguity.
_DANGLING_CONNECTOR_WORDS = frozenset({"the", "a", "an", "and", "or"})
_TRAILING_WORD_BEFORE_QUESTION_MARK = re.compile(r"(\w+)\s*\?\s*$")
# A quoted empty string ("" / '' / "" / '' -- straight or curly, with only
# whitespace inside, optionally wrapped in parens) embedded in rendered
# text is exactly what an interpolated-but-blank field looks like once
# it's been wrapped in quotes by an f-string template (e.g. the now-fixed
# 'in the game known as ("-")' shape one of these adapters actually
# produced in production before nickname normalization stripped the "-"
# placeholder down to an empty string).
_EMPTY_QUOTED_STRING = re.compile(r'(\(\s*)?(""|\'\'|“”|‘’)(\s*\))?')
_DOUBLE_SPACE = re.compile(r"  +")
_LITERAL_NONE_OR_NULL = re.compile(r"\b(None|null|undefined|NaN)\b")
_UNRESOLVED_PLACEHOLDER = re.compile(r"\{\{?\s*\}?\}|\{[a-zA-Z_][a-zA-Z0-9_]*\}")


def _malformed_text_reason(text: str, *, is_short_answer_value: bool = False) -> str | None:
    """Returns a short, specific reason string if `text` shows a known
    template-completeness failure shape, else None. Deliberately pattern-
    based (real, reproduced failure shapes), not a general grammar
    checker -- this catches the SPECIFIC class of bug this pass exists to
    eliminate, not every possible awkward sentence.

    `is_short_answer_value=True` for multiple-choice OPTIONS (as opposed to
    a full question/notes sentence): this codebase's own real, legitimately
    curated trivia content uses short answers like "None" or "None clear"
    (meaning "no real trophy/consensus exists for this fact") -- confirmed
    live in the CFB Rivalry Trivia bank -- so the None/null/undefined/NaN
    literal-leak check, which is genuinely useful for a full SENTENCE where
    a bare "None" mid-text is a real bug signature, is skipped for short
    answer values where it's a real, common, valid word instead."""
    if not text:
        return None
    m = _TRAILING_WORD_BEFORE_QUESTION_MARK.search(text)
    if m and m.group(1).lower() in _DANGLING_CONNECTOR_WORDS:
        return f"dangling connector word {m.group(1)!r} immediately before the final '?' -- a value was never interpolated"
    if _EMPTY_QUOTED_STRING.search(text):
        return "an empty quoted string is embedded in the text -- a field rendered blank instead of being omitted"
    if _DOUBLE_SPACE.search(text):
        return "double space found -- likely a missing interpolated value left an empty gap"
    if not is_short_answer_value and _LITERAL_NONE_OR_NULL.search(text):
        return "the literal word None/null/undefined/NaN is visible in player-facing text"
    if _UNRESOLVED_PLACEHOLDER.search(text):
        return "an unresolved {placeholder} or empty {} is visible in player-facing text"
    return None


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
    elif (reason := _malformed_text_reason(record["question"])) is not None:
        failures.append((record["id"], f"malformed question text: {reason}"))
    n = len(record["options"]) if isinstance(record["options"], list) else -1
    if n not in VALID_OPTION_COUNTS or len(set(record["options"])) != n:
        failures.append((record["id"], f"options not exactly {VALID_OPTION_COUNTS} unique strings"))
    elif any(not isinstance(o, str) or not o.strip() for o in record["options"]):
        failures.append((record["id"], "an option is empty or not a real string"))
    else:
        for o in record["options"]:
            reason = _malformed_text_reason(o, is_short_answer_value=True)
            if reason is not None:
                failures.append((record["id"], f"malformed option text {o!r}: {reason}"))
                break
    if not (isinstance(record["correctIndex"], int) and 0 <= record["correctIndex"] < max(n, 0)):
        failures.append((record["id"], "correctIndex out of range"))
    else:
        expected = record.get("_audit", {}).get("correct_answer_text")
        if expected is not None and record["options"][record["correctIndex"]] != expected:
            failures.append((record["id"], "correctIndex does not point at the verified correct answer"))
    if not isinstance(record["notes"], str):
        failures.append((record["id"], "notes not a string"))
    elif record["notes"].strip():
        reason = _malformed_text_reason(record["notes"])
        if reason is not None:
            failures.append((record["id"], f"malformed notes text: {reason}"))
    return failures


def validate_all(records: list[dict], allowed_category: str) -> list[tuple]:
    out = []
    for r in records:
        out.extend(validate_contract(r, allowed_category))
    return out
