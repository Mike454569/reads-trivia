"""Format-by-format certification for story-generated trivia.

Read-only certification over persisted Story Factory question artifacts. This is
intentionally stricter than "JSON parses": it validates the actual gameplay
contract each mechanic needs, checks event provenance, rejects sensitive Fact/
Fake, and reports failure reasons by format.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from tools.quiz_export import engine as engine_bootstrap
from .lore_format_qa import validate_multiformat_question


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _event_ok(conn, event_id):
    row = conn.execute(
        "SELECT verification_status,sensitive FROM universal_event WHERE event_id=?",
        (str(event_id),),
    ).fetchone()
    if not row:
        return False, "EVENT_MISSING"
    if str(row["verification_status"]) != "VERIFIED":
        return False, "EVENT_NOT_VERIFIED"
    evidence = conn.execute(
        "SELECT COUNT(*) FROM universal_event_evidence WHERE event_id=?",
        (str(event_id),),
    ).fetchone()[0]
    if int(evidence or 0) < 1:
        return False, "EVENT_HAS_NO_EVIDENCE"
    return True, None


def _provenance_event_ids(q, fallback_event_id=None):
    ids = set()
    prov = q.get("provenance") or {}
    for eid in prov.get("event_ids") or []:
        ids.add(str(eid))
    chain = prov.get("chain") or {}
    for hop in chain.get("hops") or []:
        if hop.get("object_type") == "EVENT":
            ids.add(str(hop.get("object_id")))
    if q.get("event_id"):
        ids.add(str(q["event_id"]))
    if fallback_event_id:
        ids.add(str(fallback_event_id))
    return {x for x in ids if x and x != "None"}


def _validate_mcq(q):
    errors = []
    options = list(q.get("options") or [])
    answer = q.get("answer") or {}
    label = str(answer.get("label") or "")
    if len(options) != 4:
        errors.append("MCQ_REQUIRES_FOUR_OPTIONS")
    if len({str(x).casefold().strip() for x in options}) != len(options):
        errors.append("MCQ_DUPLICATE_OPTIONS")
    if not label or options.count(label) != 1:
        errors.append("MCQ_ANSWER_NOT_UNIQUE")
    clues = q.get("clues") or []
    if q.get("question_family") == "LORE_IDENTITY" and len(clues) < 3:
        errors.append("IDENTITY_NEEDS_THREE_CLUES")
    return errors


def _validate_fact_fake(q):
    errors = []
    aid = str((q.get("answer") or {}).get("id") or "")
    if aid not in {"FACT", "FAKE"}:
        errors.append("FACT_FAKE_BAD_ANSWER")
    if not str(q.get("question") or "").strip():
        errors.append("FACT_FAKE_BLANK_STATEMENT")
    return errors


def _validate_matching(q):
    errors = []
    prompts = list(q.get("prompts") or [])
    answers = list(q.get("answers") or [])
    if len(prompts) < 3 or len(answers) < 3:
        errors.append("MATCHING_NEEDS_THREE_PAIRS")
    if len({str(x.get("id")) for x in prompts}) != len(prompts):
        errors.append("MATCHING_DUPLICATE_PROMPTS")
    if len({str(x.get("id")) for x in answers}) != len(answers):
        errors.append("MATCHING_DUPLICATE_ANSWERS")
    solution = q.get("solution") or {}
    if solution and set(map(str, solution.keys())) != {str(x.get("id")) for x in prompts}:
        errors.append("MATCHING_SOLUTION_MISMATCH")
    return errors


def validate_story_question(conn, row):
    try:
        q = json.loads(row["question_json"])
    except Exception:
        return ["QUESTION_JSON_INVALID"]

    errors = []
    mechanic = str(q.get("mechanic") or row["mechanic"] or "")
    if not str(q.get("question_id") or "").strip():
        errors.append("MISSING_QUESTION_ID")
    if not str(q.get("question") or "").strip():
        errors.append("MISSING_QUESTION_TEXT")

    if mechanic == "MULTIPLE_CHOICE":
        errors.extend(_validate_mcq(q))
    elif mechanic == "FACT_OR_FAKE":
        errors.extend(_validate_fact_fake(q))
    elif mechanic == "MATCHING":
        errors.extend(_validate_matching(q))
    elif mechanic in {"SORTING_TIMELINE"} or q.get("question_family") in {
        "LORE_COMMON_LINK", "LORE_BEFORE_AFTER", "LORE_TIMELINE"
    }:
        qa = validate_multiformat_question(q)
        errors.extend(qa.get("errors") or [])
    else:
        errors.append("UNSUPPORTED_STORY_MECHANIC")

    event_ids = _provenance_event_ids(q, row["event_id"])
    if not event_ids:
        errors.append("NO_EVENT_PROVENANCE")
    for eid in event_ids:
        ok, reason = _event_ok(conn, eid)
        if not ok:
            errors.append(reason + ":" + eid)

    if mechanic == "FACT_OR_FAKE":
        for eid in event_ids:
            erow = conn.execute(
                "SELECT sensitive FROM universal_event WHERE event_id=?",
                (eid,),
            ).fetchone()
            if erow and int(erow["sensitive"] or 0):
                errors.append("SENSITIVE_FACT_FAKE")

    copy = " ".join([
        str(q.get("question") or ""),
        *[
            str(c.get("text") if isinstance(c, dict) else c)
            for c in (q.get("clues") or [])
        ],
    ]).casefold()
    for bad in ("verified chain", "structured fact", "subject of event", "event subject"):
        if bad in copy:
            errors.append("ROBOTIC_COPY")
            break

    return sorted(set(errors))


def certify_story_question_quality(conn=None, *, failure_sample_limit=25):
    owns = conn is None
    if owns:
        conn = engine_bootstrap.connect()
    try:
        if "story_generated_questions" not in _tables(conn):
            return {
                "status": "NO_DATA",
                "question_count": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "by_mechanic": {},
                "failure_reasons": {},
                "failure_samples": [],
                "promotion_ready": False,
            }

        rows = conn.execute(
            """SELECT question_id,event_id,mechanic,status,question_json
               FROM story_generated_questions
               ORDER BY created_at,question_id"""
        ).fetchall()

        by_mechanic = defaultdict(lambda: {"total":0,"passed":0,"failed":0})
        reasons = Counter()
        samples = []
        passed = failed = 0

        for row in rows:
            mechanic = str(row["mechanic"] or "UNKNOWN")
            by_mechanic[mechanic]["total"] += 1
            errors = validate_story_question(conn, row)
            if errors:
                failed += 1
                by_mechanic[mechanic]["failed"] += 1
                reasons.update(errors)
                if len(samples) < int(failure_sample_limit):
                    samples.append({
                        "question_id": row["question_id"],
                        "mechanic": mechanic,
                        "errors": errors,
                    })
            else:
                passed += 1
                by_mechanic[mechanic]["passed"] += 1

        total = passed + failed
        return {
            "status": "PASSED" if total and failed == 0 else ("FAILED" if total else "NO_DATA"),
            "question_count": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / max(1, total), 4),
            "by_mechanic": dict(by_mechanic),
            "failure_reasons": dict(reasons),
            "failure_samples": samples,
            "promotion_ready": total >= 25 and failed == 0,
        }
    finally:
        if owns:
            conn.close()


def main():
    print(json.dumps(certify_story_question_quality(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
