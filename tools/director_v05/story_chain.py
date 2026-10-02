"""Fuse verified football events with source-backed career chains.

This bridges the v0.5 universal event layer and deep relationship chains.
It emits structured game material with explicit provenance and legal-state
precision instead of free-form accusations or unsourced prose.
"""
from __future__ import annotations

from .chain_engine import Chain, chain_payload

_SUPPORTED_MECHANICS = {
    "WHO_AM_I", "THREE_CLUES", "MULTIPLE_CHOICE", "COMMON_LINK",
    "SURVIVAL", "DAILY", "ENDLESS",
}
_STRONG_EVIDENCE = {"PRIMARY", "AUTHORITATIVE", "REPUTABLE_MEDIA"}
_SENSITIVE_TYPES = {
    "LEGAL_EVENT", "ARREST", "CHARGE", "CONVICTION", "ACQUITTAL",
    "DISMISSAL", "INVESTIGATION",
}


def _event_subject_ids(event: dict) -> set[str]:
    ids = set()
    for subject in event.get("subjects") or ():
        sid = subject.get("subject_id")
        if sid is not None:
            ids.add(str(sid))
    sid = event.get("subject_id")
    if sid is not None:
        ids.add(str(sid))
    return ids


def _validate_event(event: dict) -> None:
    if event.get("verification_status") != "VERIFIED":
        raise ValueError("story event must be VERIFIED")
    for field in ("event_id", "event_type", "source_url", "source_publisher", "evidence_tier"):
        if not event.get(field):
            raise ValueError("story event missing required provenance field: " + field)

    event_type = str(event.get("event_type") or "").upper()
    sensitive = bool(event.get("sensitive")) or event_type in _SENSITIVE_TYPES
    if sensitive:
        if event.get("evidence_tier") not in _STRONG_EVIDENCE:
            raise ValueError("sensitive story requires strong evidence")
        if not event.get("legal_stage"):
            raise ValueError("sensitive legal story requires precise legal_stage")


def compile_story_chain(event: dict, chain: Chain, mechanic: str) -> dict:
    """Compile a verified event plus a verified career chain.

    Event title/summary remain reveal-only because either may contain the
    answer. Pre-answer clues are independently sourced career hops plus
    non-identifying event metadata.
    """
    mechanic = mechanic.upper()
    if mechanic not in _SUPPORTED_MECHANICS:
        raise ValueError("mechanic cannot consume story-chain material")
    _validate_event(event)
    if not chain.provenance_complete:
        raise ValueError("story chain requires complete career provenance")

    subjects = _event_subject_ids(event)
    if str(chain.anchor_id) not in subjects:
        raise ValueError("event subject does not match chain anchor")

    event_type = str(event["event_type"]).upper()
    sensitive = bool(event.get("sensitive")) or event_type in _SENSITIVE_TYPES

    clues = [
        {
            "kind": "career",
            "relation": hop.relation,
            "object_id": hop.object_id,
            "season": hop.season,
            "source_id": hop.source_id,
            "verification_status": hop.verification_status,
        }
        for hop in chain.hops
    ]
    clues.append({
        "kind": "event_context",
        "event_type": event_type,
        "event_date": event.get("event_date"),
        "league": event.get("league"),
        "legal_stage": event.get("legal_stage") if sensitive else None,
        "evidence_tier": event.get("evidence_tier"),
    })

    return {
        "compiler_version": "1.0.0",
        "material_type": "STORY_CHAIN",
        "mechanic": mechanic,
        "answer": {"type": chain.anchor_type, "id": chain.anchor_id},
        "clues": clues,
        "story": {
            "event_id": event["event_id"],
            "event_type": event_type,
            "sensitive": sensitive,
            "legal_stage": event.get("legal_stage") if sensitive else None,
        },
        "reveal": {
            "title": event.get("title"),
            "neutral_summary": event.get("neutral_summary"),
            "source_url": event["source_url"],
            "source_publisher": event["source_publisher"],
            "source_date": event.get("source_date"),
        },
        "provenance": {
            "event": {
                "event_id": event["event_id"],
                "source_url": event["source_url"],
                "source_publisher": event["source_publisher"],
                "evidence_tier": event["evidence_tier"],
                "verification_status": event["verification_status"],
            },
            "career_chain": chain_payload(chain),
        },
        "answer_provenance_required": True,
        "requires_precise_legal_language": sensitive,
        "no_guilt_inference": sensitive,
    }
