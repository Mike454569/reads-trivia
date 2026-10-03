"""Adapters from story-generated MCQs into reusable game-shell contracts."""
from __future__ import annotations

import json


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def load_story_mcqs(conn, *, limit=50, league=None):
    if "story_generated_questions" not in _tables(conn):
        return []
    rows = conn.execute(
        """SELECT g.question_json,g.subject_type,g.event_id,u.league
           FROM story_generated_questions g
           LEFT JOIN universal_event u ON u.event_id=g.event_id
           WHERE g.status='READY_FOR_BANK'
             AND g.mechanic='MULTIPLE_CHOICE'
           ORDER BY g.created_at DESC,g.question_id
           LIMIT ?""",
        (max(1, min(int(limit) * 5, 500)),),
    ).fetchall()
    out = []
    for row in rows:
        try:
            q = json.loads(row["question_json"])
        except Exception:
            continue
        answer = q.get("answer") or {}
        options = list(q.get("options") or [])
        if len(options) != 4:
            continue
        label = str(answer.get("label") or "")
        if options.count(label) != 1:
            continue
        subject_type = str(answer.get("type") or row["subject_type"] or "")
        event_league = str(row["league"] or "").upper() or None
        inferred = event_league or (
            "CFB" if subject_type == "CFB_PLAYER" else (
                "NFL" if subject_type in {"NFL_PLAYER","NFL_TEAM"} else None
            )
        )
        if league and inferred != str(league).upper():
            continue
        out.append(q)
        if len(out) >= int(limit):
            break
    return out


def to_deep_round(q):
    answer = q["answer"]["label"]
    options = list(q["options"])
    return {
        "category": "Football Lore",
        "prompt": q["question"],
        "correct_label": answer,
        "decoy_labels": [x for x in options if x != answer],
        "notes": "Verified story-backed Reads lore question.",
        "difficulty": q.get("difficulty_band") or q.get("difficulty") or "Hard",
        "depth_source": "STORY_FACTORY",
        "bucket": "Football Lore",
        "_story_question_id": q.get("question_id"),
    }


def to_team_question(q):
    """Shape used by Risk/Three Strikes/Double or Nothing shells."""
    answer = q["answer"]["label"]
    options = list(q["options"])
    return {
        "prompt": q["question"],
        "correct_team": answer,
        "decoy_teams": [x for x in options if x != answer],
        "notes": "Verified story-backed Reads lore question.",
        "_story_question_id": q.get("question_id"),
    }


def to_generation_question(q, *, category="Football Lore"):
    """Shape used by generic generated-question shells such as Drive."""
    answer = q["answer"]["label"]
    options = list(q["options"])
    return {
        "id": q.get("question_id"),
        "question": q["question"],
        "options": options,
        "correctIndex": options.index(answer),
        "answer": answer,
        "difficulty": q.get("difficulty_band") or q.get("difficulty") or "Hard",
        "content_category": category,
        "notes": "Verified story-backed Reads lore question.",
        "_story_question_id": q.get("question_id"),
    }
