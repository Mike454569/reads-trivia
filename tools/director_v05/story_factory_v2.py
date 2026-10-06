"""Shared Story Factory 2.0 player-facing quality and transformation helpers."""
from __future__ import annotations

import hashlib
from typing import Any

from tools.director_v04 import question_intelligence

_BLOCKED_COPY = (
    "classified as a ",
    "verified football event occurred in",
    "event type",
    "taxonomy",
    "verified chain",
    "structured fact",
    "subject of event",
    "event subject",
)


def _text_parts(q: dict) -> list[str]:
    parts = [str(q.get("question") or "")]
    parts.extend(str(x) for x in q.get("context_clues") or [])
    for clue in q.get("clues") or []:
        parts.append(str(clue.get("text") if isinstance(clue, dict) else clue))
    for item in q.get("prompts") or []:
        parts.append(str(item.get("text") if isinstance(item, dict) else item))
    for item in q.get("items") or []:
        parts.append(str(item.get("label") if isinstance(item, dict) else item))
    return [" ".join(x.split()).strip() for x in parts if str(x).strip()]


def story_quality(q: dict) -> dict:
    parts = _text_parts(q)
    combined = " ".join(parts)
    lowered = combined.casefold()
    robotic = [token for token in _BLOCKED_COPY if token in lowered]
    score_input = {
        "question": combined,
        "options": q.get("options") or [
            x.get("label") for x in (q.get("answers") or []) if isinstance(x, dict)
        ],
        "answer": (q.get("answer") or {}).get("label") if isinstance(q.get("answer"), dict) else q.get("answer"),
        "depth_source": "STORY_FACTORY_V2",
    }
    intelligence = question_intelligence.score_question(score_input, source="STORY_FACTORY_V2")
    # Story mechanics often use intentionally terse shell prompts such as
    # "What happened next?" while the real depth is in items/clues. The
    # combined copy above lets the scorer see that context.
    return {
        "version": 2,
        "score": intelligence["score"],
        "tier": intelligence["tier"],
        "fingerprint": intelligence["fingerprint"],
        "semantic_fingerprint": intelligence["semantic_fingerprint"],
        "robotic_copy": robotic,
        "text_part_count": len(parts),
    }


def prepare_story_question(q: dict, *, min_score: int = 38) -> dict:
    quality = story_quality(q)
    if quality["robotic_copy"]:
        raise ValueError("STORY_V2_ROBOTIC_COPY:" + quality["robotic_copy"][0])
    if quality["score"] < int(min_score):
        raise ValueError(f"STORY_V2_QUALITY_BELOW_THRESHOLD:{quality['score']}<{int(min_score)}")
    out = dict(q)
    out["story_factory_v2"] = quality
    return out


def stable_question_id(family: str, parts) -> str:
    payload = "|".join([str(family), *[str(x) for x in parts]])
    return "storyv2_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
