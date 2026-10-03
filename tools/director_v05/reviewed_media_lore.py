"""Fail-closed reviewed-media ingestion for press/off-field football lore.

This is deliberately not a web scraper. Every row must already have a reviewed
source URL, publisher, neutral summary and subjects before it can enter universal
lore. The point is to scale these story families without converting search-result
snippets or social posts into facts.
"""
from __future__ import annotations

from urllib.parse import urlparse

from .event_ingest import upsert_event

ALLOWED_EVENT_TYPES = {"PRESS_CONFERENCE", "OFF_FIELD_ODDITY", "CELEBRATION", "MASCOT_FAN_MOMENT"}
ALLOWED_TIERS = {"PRIMARY", "REPUTABLE_MEDIA"}
BLOCKED_HOSTS = {
    "x.com", "twitter.com", "facebook.com", "instagram.com", "tiktok.com",
}


def _host(url):
    return (urlparse(str(url)).hostname or "").casefold().removeprefix("www.")


def validate_reviewed_story(story):
    typ = str(story.get("event_type") or "").upper()
    if typ not in ALLOWED_EVENT_TYPES:
        raise ValueError("UNSUPPORTED_REVIEWED_STORY_TYPE")
    url = str(story.get("source_url") or "").strip()
    if _host(url) in BLOCKED_HOSTS:
        raise ValueError("SOCIAL_POST_NOT_ACCEPTED_AS_STANDALONE_EVIDENCE")
    if str(story.get("evidence_tier") or "").upper() not in ALLOWED_TIERS:
        raise ValueError("REVIEWED_STORY_REQUIRES_PRIMARY_OR_REPUTABLE_MEDIA")
    if not str(story.get("neutral_summary") or "").strip():
        raise ValueError("REVIEWED_STORY_MISSING_NEUTRAL_SUMMARY")
    if not story.get("subjects"):
        raise ValueError("REVIEWED_STORY_REQUIRES_SUBJECT")
    if story.get("quote") and not story.get("quote_context"):
        raise ValueError("QUOTE_REQUIRES_CONTEXT")
    return True


def ingest_reviewed_story(conn, story):
    validate_reviewed_story(story)
    payload = dict(story)
    payload["event_type"] = str(payload["event_type"]).upper()
    payload["evidence_tier"] = str(payload["evidence_tier"]).upper()
    payload["verification_status"] = "VERIFIED"
    payload["sensitive"] = False
    tags = list(payload.get("tags") or [])
    tags.append("reviewed_media")
    payload["tags"] = tags
    payload.pop("quote", None)
    payload.pop("quote_context", None)
    return upsert_event(conn, payload)


def ingest_reviewed_stories(conn, stories):
    inserted = 0
    rejected = []
    for index, story in enumerate(stories):
        try:
            ingest_reviewed_story(conn, story)
            inserted += 1
        except (ValueError, KeyError) as exc:
            rejected.append({"index": index, "reason": str(exc)})
    conn.commit()
    return {"inserted": inserted, "rejected": rejected}
