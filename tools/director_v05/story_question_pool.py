"""Read QA-ready story-generated questions for normal Deep Lore delivery."""
from __future__ import annotations

import json


def load_ready_story_questions(
    conn,
    *,
    recent_question_ids=(),
    recent_answer_ids=(),
    limit=25,
):
    tables = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "story_generated_questions" not in tables:
        return []

    recent_q = {str(x) for x in recent_question_ids}
    recent_a = {str(x) for x in recent_answer_ids}
    rows = conn.execute(
        """SELECT question_json
           FROM story_generated_questions
           WHERE status='READY_FOR_BANK'
           ORDER BY created_at DESC,question_id
           LIMIT ?""",
        (max(1, min(int(limit) * 5, 500)),),
    ).fetchall()

    out = []
    seen_answers = set()
    for row in rows:
        try:
            q = json.loads(row["question_json"])
        except Exception:
            continue

        qid = str(q.get("question_id") or "")
        answer = q.get("answer") or {}
        aid = str(answer.get("id") or "")
        options = list(q.get("options") or [])

        # Public Deep Lore package currently uses the four-choice guess
        # renderer. Progressive-only story artifacts remain available to
        # future Progressive Clue delivery but are not forced into this mode.
        if q.get("mechanic") != "MULTIPLE_CHOICE":
            continue
        if not qid or qid in recent_q or not aid or aid in recent_a:
            continue
        if aid in seen_answers:
            continue
        if len(options) != 4 or len({str(x).casefold() for x in options}) != 4:
            continue
        label = str(answer.get("label") or "")
        if options.count(label) != 1:
            continue
        clues = [
            c for c in q.get("clues") or []
            if str(c.get("text") or "").strip()
        ]
        if len(clues) < 3:
            continue

        out.append(q)
        seen_answers.add(aid)
        if len(out) >= int(limit):
            break
    return out
