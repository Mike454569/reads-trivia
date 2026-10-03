"""Human-sounding phrasing for deep lore chains.

This module turns graph relations into football-trivia copy. It never invents
facts: every clue is rendered only from stored event text or sourced structured
relationships.
"""
from __future__ import annotations

import re

from .entity_labels import resolve_label


def _event_detail(conn, event_id):
    row = conn.execute(
        """SELECT event_type,event_date,title,neutral_summary,league
           FROM universal_event WHERE event_id=? AND verification_status='VERIFIED'""",
        (str(event_id),),
    ).fetchone()
    if not row:
        return None
    event = dict(row)
    event["tags"] = [
        str(r[0]) for r in conn.execute(
            "SELECT tag FROM universal_event_tag WHERE event_id=? ORDER BY tag",
            (str(event_id),),
        ).fetchall()
    ]
    return event


def _season_phrase(season):
    return (" in " + str(season)) if season is not None else ""


def _sentence(text):
    text = str(text or "").strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    return text if text.endswith((".", "!", "?")) else text + "."


def _strip_engine_language(text):
    """Remove known ingestion/reporting phrases that sound like database output."""
    replacements = (
        (" in verified play-by-play", ""),
        ("a verified game result selected by rarity rules", "an unusual final score"),
        ("Verified historical NFL contract record.", "A notable NFL contract."),
        ("Verified multi-school career path", "A college career that included multiple stops"),
    )
    out = str(text or "").strip()
    for old, new in replacements:
        out = out.replace(old, new)
    return out


def _mask_answer(text, answer_label, answer_type):
    """Hide an exact answer label without changing the underlying factual claim."""
    text = str(text)
    label = str(answer_label or "").strip()
    if not label or label.casefold() not in text.casefold():
        return text

    if answer_type in {"NFL_PLAYER", "CFB_PLAYER", "COACH"}:
        replacement = "I"
    elif answer_type == "NFL_TEAM":
        replacement = "my team"
    elif answer_type == "SCHOOL":
        replacement = "my school"
    else:
        replacement = "the answer"

    return re.sub(re.escape(label), replacement, text, flags=re.IGNORECASE)


def question_stem(anchor_type):
    """Natural stem matched to the thing the player is trying to identify."""
    return {
        "NFL_PLAYER": "Who am I?",
        "CFB_PLAYER": "Who am I?",
        "COACH": "Who am I?",
        "NFL_TEAM": "Which NFL team am I?",
        "SCHOOL": "Which college program am I?",
    }.get(str(anchor_type), "What am I?")


def render_hop(conn, hop, *, anchor_type=None, answer_label=None):
    """Render one graph hop as a concrete football clue."""
    relation = str(hop.relation)
    obj_label = resolve_label(conn, hop.object_type, hop.object_id)
    season = _season_phrase(hop.season)

    if relation == "DRAFTED_BY":
        return "I was drafted by " + obj_label + season + "."
    if relation == "ROSTERED_BY":
        return "I suited up for " + obj_label + season + "."
    if relation == "ALL_PRO":
        honor = str(hop.object_id).replace("_", " ").title()
        return "I earned " + honor + " All-Pro honors" + season + "."
    if relation == "PRO_BOWL":
        return "I made the Pro Bowl" + season + "."
    if relation == "COACHED":
        return "I coached " + obj_label + season + "."
    if relation == "DRAFTED_PLAYER":
        subject_label = resolve_label(conn, hop.subject_type, hop.subject_id)
        return subject_label + " also drafted " + obj_label + season + "."
    if relation == "ROSTERED_PLAYER":
        subject_label = resolve_label(conn, hop.subject_type, hop.subject_id)
        return obj_label + " was also on " + subject_label + "'s roster" + season + "."
    if relation == "TEAM_COACH":
        subject_label = resolve_label(conn, hop.subject_type, hop.subject_id)
        return obj_label + " also coached " + subject_label + season + "."
    if relation == "SCHOOL_PLAYER":
        subject_label = resolve_label(conn, hop.subject_type, hop.subject_id)
        return obj_label + " also played at " + subject_label + season + "."
    if relation == "STARTED_AT":
        return "I started my college career at " + obj_label + season + "."
    if relation == "TRANSFERRED_TO":
        return "I later transferred to " + obj_label + season + "."
    if relation == "RANKED":
        return "My program reached No. " + str(hop.object_id) + season + "."
    if relation.startswith("DERIVED_"):
        metric = relation.removeprefix("DERIVED_").replace("_", " ").lower()
        if metric == "bust score":
            return "My draft slot and career production give me a notable bust-score profile."
        if metric == "steal score":
            return "My draft slot and career production give me a notable steal-score profile."
        if metric == "draft value":
            return "My draft position and career production create an unusual draft-value profile."
        return "My career data stands out in " + metric + "."

    if relation == "SUBJECT_OF_EVENT":
        event = _event_detail(conn, hop.object_id)
        if not event:
            raise ValueError("MISSING_EVENT_DETAIL")
        detail = _strip_engine_language(event.get("neutral_summary"))
        if not detail:
            raise ValueError("MISSING_EVENT_SUMMARY")
        detail = _mask_answer(detail, answer_label, anchor_type)
        season_text = str(hop.season) if hop.season is not None else None
        # Add time context only when it is not already present.
        if season_text and season_text not in detail:
            detail = "In " + season_text + ", " + detail[0].lower() + detail[1:]
        return _sentence(detail)

    if relation == "EVENT_SUBJECT":
        # The paired SUBJECT_OF_EVENT hop already supplies the actual story.
        return None

    return None


def render_chain_clues(conn, chain):
    """Render informative, human clues and reject vague/engine-like output."""
    answer_label = resolve_label(conn, chain.anchor_type, chain.anchor_id)
    rendered = []
    seen = set()

    for hop in chain.hops:
        text = render_hop(
            conn,
            hop,
            anchor_type=chain.anchor_type,
            answer_label=answer_label,
        )
        if not text:
            continue

        lowered = text.casefold()
        banned = (
            "verified chain",
            "subject of event",
            "event subject",
            "source backed",
            "structured fact",
            "selected by rarity rules",
        )
        if any(term in lowered for term in banned):
            raise ValueError("ROBOTIC_CLUE_TEXT")

        if answer_label and answer_label.casefold() in lowered:
            raise ValueError("CHAIN_ANSWER_LEAKAGE")

        normalized = text.strip().casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        rendered.append({
            "relation": hop.relation,
            "text": text.strip(),
            "source_kind": hop.source_kind,
        })

    if len(rendered) < 3:
        raise ValueError("INSUFFICIENT_NATURAL_CLUES")
    return rendered


def order_clues(clues, difficulty_score):
    """Hard questions save the most distinctive story clue for later."""
    event = [c for c in clues if c["relation"] == "SUBJECT_OF_EVENT"]
    structured = [c for c in clues if c["relation"] != "SUBJECT_OF_EVENT"]

    if float(difficulty_score or 0) >= 70:
        return structured + event
    return event + structured
