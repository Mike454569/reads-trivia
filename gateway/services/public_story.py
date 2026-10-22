"""Read-only, fail-closed bridge from certified Story Factory MCQs to public rounds."""
from __future__ import annotations

import json
import secrets
import threading
from collections import deque

from gateway.errors import GatewayError
from gateway.services import game_state
from tools.quiz_export import engine as engine_bootstrap

_recent_lock = threading.Lock()
_recent_by_client = {}

MODES = {
    "story_lore_nfl": "NFL",
    "story_lore_cfb": "CFB",
}


def _eligible(question, event_id):
    if not isinstance(question, dict) or question.get("mechanic") != "MULTIPLE_CHOICE":
        return False
    if str(question.get("event_id")) != str(event_id) or question.get("sensitive") is True:
        return False
    opts = question.get("options")
    answer = question.get("answer")
    if not isinstance(opts, list) or len(opts) != 4 or not all(isinstance(x, str) and x.strip() for x in opts):
        return False
    if len({s.strip().casefold() for s in opts}) != 4:
        return False
    if not isinstance(answer, dict) or not isinstance(answer.get("label"), str):
        return False
    if sum(x.strip().casefold() == answer["label"].strip().casefold() for x in opts) != 1:
        return False
    provenance = question.get("provenance") or {}
    if not isinstance(provenance, dict) or provenance.get("provenance_complete") is not True or not provenance.get("evidence"):
        return False
    if str(event_id) not in set(map(str, provenance.get("event_ids") or [])):
        return False
    return isinstance(question.get("question"), str) and bool(question["question"].strip())


def start_story_round(mode: str, *, client_id=None, exclude_question_ids=()):
    league = MODES.get(mode)
    if league is None:
        raise GatewayError("INVALID_MODE", "Unknown story mode.")
    db = engine_bootstrap.connect()
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"story_generated_questions", "universal_event"}.issubset(tables):
            raise GatewayError("CONTENT_UNAVAILABLE", "Certified story questions are not available yet.")
        rows = db.execute(
            """SELECT q.question_json,q.event_id
               FROM story_generated_questions q
               JOIN universal_event e ON e.event_id=q.event_id
               WHERE q.status='READY_FOR_BANK'
                 AND q.mechanic='MULTIPLE_CHOICE'
                 AND e.verification_status='VERIFIED'
                 AND COALESCE(e.sensitive,0)=0
                 AND UPPER(e.league)=?
               ORDER BY RANDOM() LIMIT 60""",
            (league,),
        ).fetchall()
    finally:
        db.close()
    excluded = {str(v) for v in exclude_question_ids}
    if client_id:
        with _recent_lock:
            excluded.update(_recent_by_client.get((client_id, mode), ()))
    for row in rows:
        try:
            question = json.loads(row["question_json"])
        except (ValueError, TypeError):
            continue
        if not _eligible(question, row["event_id"]):
            continue
        if str(question.get("question_id") or "") in excluded:
            continue
        if client_id:
            with _recent_lock:
                _recent_by_client.setdefault((client_id, mode), deque(maxlen=32)).append(str(question["question_id"]))
        round_id = "GGP4:" + secrets.token_hex(12)
        correct = question["answer"]["label"].strip()
        game_state.create_state(round_id, {
            "story_bank_mode": mode, "answer": correct,
            "notes": str(question.get("explanation") or "")[:500],
            "question_id": str(question.get("question_id") or ""),
        })
        return {
            "round_id": round_id, "mode": mode, "engine_kind": "story",
            "kind": "multiple_choice", "title": "Football Story Room",
            "instructions": "Choose the answer to this verified football story.",
            "competition": league,
            "view": {"prompt": question["question"], "options": question["options"],
                     "completed": False},
            "metadata": {"source": "certified_story_bank"},
        }
    raise GatewayError("CONTENT_UNAVAILABLE", "No certified playable stories are available for this league.")


def submit_story_round(round_id: str, submission: dict):
    try:
        state = game_state.load_state(round_id)
    except game_state.StateIdInvalid:
        state = None
    if not state or state.get("story_bank_mode") not in MODES:
        raise GatewayError("INVALID_GAME_ID", "Story round not found.")
    answer = submission.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise GatewayError("INVALID_REQUEST", "A nonempty answer is required.")
    correct = state["answer"]
    return {
        "round_id": round_id, "mode": state["story_bank_mode"],
        "engine_kind": "story",
        "result": {"correct": answer.strip().casefold() == correct.casefold(),
                   "canonical_answer": correct, "notes": state.get("notes")},
        "view": {"completed": True},
    }


def start_story_identity(*, client_id=None):
    """Optional source-backed Who Am I round; None means use legacy generator."""
    db = engine_bootstrap.connect()
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"story_generated_questions", "universal_event"}.issubset(tables):
            return None
        rows = db.execute(
            """SELECT q.question_json,q.event_id FROM story_generated_questions q
               JOIN universal_event e ON e.event_id=q.event_id
               WHERE q.status IN ('READY_FOR_BANK','READY_FOR_FORMAT_BANK')
                 AND q.mechanic='PROGRESSIVE_CLUE'
                 AND e.verification_status='VERIFIED' AND COALESCE(e.sensitive,0)=0
                 AND UPPER(e.league)='NFL' AND UPPER(q.subject_type) IN ('PLAYER','NFL_PLAYER')
               ORDER BY RANDOM() LIMIT 60"""
        ).fetchall()
    except Exception:
        # Read failures must not take the currently playable Who Am I down.
        return None
    finally:
        db.close()
    mode = "who_am_i_nfl"
    with _recent_lock:
        seen = set(_recent_by_client.get((client_id, mode), ())) if client_id else set()
    for row in rows:
        try:
            q = json.loads(row["question_json"])
            label = q["answer"]["label"].strip()
            clues = [x["text"].strip() for x in q["clues"]]
            prov = q["provenance"]
            qid = str(q["question_id"])
            if q.get("mechanic") != "PROGRESSIVE_CLUE" or q.get("question_family") != "LORE_IDENTITY":
                continue
            if str(q.get("event_id")) != str(row["event_id"]) or q.get("sensitive") is True:
                continue
            if q["answer"].get("type", "").upper() not in ("PLAYER", "NFL_PLAYER"):
                continue
            if not (3 <= len(clues) <= 5) or not label or any(not x or label.casefold() in x.casefold() for x in clues):
                continue
            if not prov.get("provenance_complete") or not prov.get("evidence") or str(row["event_id"]) not in list(map(str, prov.get("event_ids", []))):
                continue
            if qid in seen:
                continue
        except (TypeError, KeyError, ValueError, AttributeError):
            continue
        round_id = "GGP4:" + secrets.token_hex(12)
        game_state.create_state(round_id, {
            "story_identity_mode": mode, "answer": label, "clues": clues,
            "clues_revealed": 1, "completed": False,
        })
        if client_id:
            with _recent_lock:
                _recent_by_client.setdefault((client_id, mode), deque(maxlen=32)).append(qid)
        return {"round_id": round_id, "mode": mode, "kind": "progressive_clue",
                "title": "Who Am I?", "instructions": "Identify the NFL player from verified clues.",
                "view": _identity_view(clues, 1, completed=False)}
    return None


def _identity_view(clues, count, *, completed):
    if completed:
        return {"round_index": 1, "round_count": 1, "completed": True}
    return {"round_index": 0, "round_count": 1, "completed": False,
            "clues_revealed_count": count, "total_clues": len(clues),
            "clues": [{"clue_index": i, "display_text": clue} for i, clue in enumerate(clues[:count])],
            "can_reveal_more": count < len(clues)}


def submit_story_identity(round_id, submission):
    try:
        state = game_state.load_state(round_id)
    except game_state.StateIdInvalid:
        state = None
    if not state or state.get("story_identity_mode") != "who_am_i_nfl":
        raise GatewayError("INVALID_GAME_ID", "Who Am I round not found.")
    if state.get("completed"):
        raise GatewayError("INVALID_REQUEST", "This round is already complete.")
    clues = state["clues"]
    count = state["clues_revealed"]
    if submission.get("action") == "reveal_next_clue":
        count = min(len(clues), count + 1)
        state["clues_revealed"] = count
        game_state.save_state(round_id, state)
        result = {"revealed": True}
    else:
        guess = str(submission.get("guess_name") or "").strip()
        correct = bool(guess) and guess.casefold() == state["answer"].casefold()
        result = {"correct": correct, "canonical_answer": state["answer"],
                  "clues_used": count, "score": max(1, len(clues)-count+1) if correct else 0}
        if not correct and count < len(clues):
            count += 1
            state["clues_revealed"] = count
            result["retry_with_more_clue"] = True
        else:
            state["completed"] = True
        game_state.save_state(round_id, state)
    return {"round_id": round_id, "mode": "who_am_i_nfl", "result": result,
            "view": _identity_view(clues, count, completed=state["completed"])}
