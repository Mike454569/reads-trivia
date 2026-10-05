"""Read story-generated non-identity formats into the mixed lore format bank."""
from __future__ import annotations

import json


FORMAT_KEY_BY_FAMILY = {
    "LORE_COMMON_LINK": "COMMON_LINK",
    "LORE_BEFORE_AFTER": "BEFORE_AFTER",
    "LORE_TIMELINE": "TIMELINE",
    "LORE_MATCHING": "MATCHING",
    "LORE_EVENT": "FACT_OR_FAKE",
}


def _player_facing_fact_fake(q):
    """Reject stale Story Factory rows that expose internal metadata."""
    text = " ".join(str(q.get("question") or "").split()).strip()
    if not text:
        return False
    lowered = text.casefold()
    blocked = (
        "classified as a ",
        "verified football event occurred in",
        "event type",
        "taxonomy",
    )
    if any(token in lowered for token in blocked):
        return False
    return True


def load_ready_story_formats(
    conn,
    *,
    recent_question_ids=(),
    limit_per_format=25,
):
    tables = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "story_generated_questions" not in tables:
        return {}

    recent = {str(x) for x in recent_question_ids}
    rows = conn.execute(
        """SELECT question_id,question_json
           FROM story_generated_questions
           WHERE status IN ('READY_FOR_FORMAT_BANK','READY_FOR_BANK')
           ORDER BY created_at DESC,question_id"""
    ).fetchall()

    out = {
        "COMMON_LINK": [],
        "BEFORE_AFTER": [],
        "TIMELINE": [],
        "MATCHING": [],
        "FACT_OR_FAKE": [],
    }
    seen = set()

    for row in rows:
        qid = str(row["question_id"])
        if not qid or qid in recent or qid in seen:
            continue
        try:
            q = json.loads(row["question_json"])
        except Exception:
            continue

        family = str(q.get("question_family") or "")
        key = FORMAT_KEY_BY_FAMILY.get(family)
        if not key:
            continue

        if key == "FACT_OR_FAKE" and not _player_facing_fact_fake(q):
            continue
        if len(out[key]) >= int(limit_per_format):
            continue
        out[key].append(q)
        seen.add(qid)

    return out
