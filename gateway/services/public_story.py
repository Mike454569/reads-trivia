"""Read-only, fail-closed bridge from certified Story Factory MCQs to public rounds."""
from __future__ import annotations

import json
import secrets

from gateway.errors import GatewayError
from gateway.services import game_state
from tools.quiz_export import engine as engine_bootstrap

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


def start_story_round(mode: str):
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
    for row in rows:
        try:
            question = json.loads(row["question_json"])
        except (ValueError, TypeError):
            continue
        if not _eligible(question, row["event_id"]):
            continue
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
