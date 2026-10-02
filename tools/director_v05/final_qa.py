"""Final QA for assembled v0.5 questions. Fail closed."""
from __future__ import annotations

def validate_question(q,*,valid_answer_ids=None,recent_question_ids=(),recent_answer_ids=()):
    errors=[]
    answer=q.get("answer") or {}
    aid=str(answer.get("id",""))
    label=str(answer.get("label","")).strip()
    if not aid or not label: errors.append("MISSING_ANSWER")
    if q.get("question_id") in {str(x) for x in recent_question_ids}: errors.append("RECENT_QUESTION_REPEAT")
    if aid in {str(x) for x in recent_answer_ids}: errors.append("RECENT_ANSWER_REPEAT")
    clues=q.get("clues") or []
    if len(clues)<2: errors.append("TOO_FEW_CLUES")
    combined=" ".join([q.get("question","")]+clues).casefold()
    if label and label.casefold() in combined: errors.append("ANSWER_LEAKAGE")
    options=q.get("options") or []
    if options:
        folded=[str(x).strip().casefold() for x in options]
        if len(folded)!=len(set(folded)): errors.append("DUPLICATE_OPTIONS")
        if folded.count(label.casefold())!=1: errors.append("ANSWER_OPTION_COUNT_INVALID")
    if valid_answer_ids is not None:
        valid={str(x) for x in valid_answer_ids}
        if aid not in valid: errors.append("ANSWER_NOT_IN_VALID_SET")
        if len(valid)!=1: errors.append("AMBIGUOUS_FINAL_ANSWER_SET")
    prov=q.get("provenance")
    if not prov or not prov.get("provenance_complete"): errors.append("INCOMPLETE_PROVENANCE")
    return {"status":"PASSED" if not errors else "FAILED","errors":errors}

def assert_playable(q,**kwargs):
    result=validate_question(q,**kwargs)
    if result["status"]!="PASSED":
        raise ValueError("QUESTION_QA_FAILED:"+",".join(result["errors"]))
    return q
