"""Natural-language phrasing for deep lore chains.

Never replaces missing knowledge with invented prose. Event clues use the stored
neutral summary; structured clues use schema-backed labels.
"""
from __future__ import annotations

from .entity_labels import resolve_label


def _event_detail(conn, event_id):
    row = conn.execute(
        """SELECT event_type,event_date,title,neutral_summary,league
           FROM universal_event WHERE event_id=? AND verification_status='VERIFIED'""",
        (str(event_id),),
    ).fetchone()
    if not row:
        return None
    return dict(row)


def _season_phrase(season):
    return (" in " + str(season)) if season is not None else ""


def render_hop(conn, hop):
    """Render one graph hop as a concrete football clue."""
    relation = str(hop.relation)
    obj_label = resolve_label(conn, hop.object_type, hop.object_id)
    season = _season_phrase(hop.season)

    if relation == "DRAFTED_BY":
        return "I was drafted by " + obj_label + season + "."
    if relation == "ROSTERED_BY":
        return "I was on " + obj_label + "'s roster" + season + "."
    if relation == "ALL_PRO":
        honor = str(hop.object_id).replace("_", " ").title()
        return "I earned " + honor + " All-Pro honors" + season + "."
    if relation == "PRO_BOWL":
        return "I was selected to the Pro Bowl" + season + "."
    if relation == "COACHED":
        return "I coached " + obj_label + season + "."
    if relation == "STARTED_AT":
        return "My college career began at " + obj_label + season + "."
    if relation == "TRANSFERRED_TO":
        return "I later transferred to " + obj_label + season + "."
    if relation == "RANKED":
        return obj_label + " was ranked No. " + str(hop.object_id) + season + "."
    if relation.startswith("DERIVED_"):
        metric = relation.removeprefix("DERIVED_").replace("_", " ").lower()
        return "My verified career data produced a " + metric + " profile."

    if relation == "SUBJECT_OF_EVENT":
        event = _event_detail(conn, hop.object_id)
        if not event:
            raise ValueError("MISSING_EVENT_DETAIL")
        detail = str(event.get("neutral_summary") or "").strip()
        if not detail:
            raise ValueError("MISSING_EVENT_SUMMARY")
        return detail if detail.endswith((".", "!", "?")) else detail + "."

    if relation == "EVENT_SUBJECT":
        # The paired SUBJECT_OF_EVENT hop already supplies the actual story.
        # Avoid generic filler like "was involved in a verified event."
        return None

    return None


def render_chain_clues(conn, chain):
    """Render only informative clues and reject vague/empty chains."""
    rendered = []
    seen = set()
    for hop in chain.hops:
        text = render_hop(conn, hop)
        if not text:
            continue
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
    """Easy starts concrete; hard starts broader and saves event detail for later."""
    event = [c for c in clues if c["relation"] == "SUBJECT_OF_EVENT"]
    structured = [c for c in clues if c["relation"] != "SUBJECT_OF_EVENT"]

    if float(difficulty_score or 0) >= 70:
        ordered = structured + event
    else:
        ordered = event + structured
    return ordered
