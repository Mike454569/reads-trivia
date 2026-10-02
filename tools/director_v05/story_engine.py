"""Discover Creator-ready story-chain material from verified universal events."""
from __future__ import annotations

from .chain_quality import eligible_chains
from .query_engine import query_events
from .story_chain import compile_story_chain


def _subjects_for_event(conn, event_id: str) -> list[dict]:
    cur = conn.execute(
        "SELECT subject_type,subject_id,role FROM universal_event_subject "
        "WHERE event_id=? ORDER BY subject_type,subject_id,role",
        (event_id,),
    )
    return [
        {"subject_type": row[0], "subject_id": str(row[1]), "role": row[2]}
        for row in cur.fetchall()
    ]


def compile_story_candidates(
    conn,
    concept: str,
    mechanic: str,
    *,
    chain_provider,
    league: str | None = None,
    limit: int = 20,
    recent_event_ids=(),
    recent_anchor_ids=(),
) -> list[dict]:
    """Return deterministic, verified story material ready for Creator.

    chain_provider(conn, subject_id) is intentionally injected so this
    orchestrator can work across NFL, CFB, coaches, teams, and future entity
    families without hard-coding one relationship universe here.
    """
    wanted = max(1, min(int(limit), 100))
    recent_events = {str(x) for x in recent_event_ids}
    recent_anchors = {str(x) for x in recent_anchor_ids}

    events = query_events(conn, concept, league=league, limit=min(100, wanted * 4))
    out = []
    seen_material = set()

    for event in events:
        if str(event["event_id"]) in recent_events:
            continue

        subjects = _subjects_for_event(conn, event["event_id"])
        if not subjects:
            continue
        event = dict(event)
        event["subjects"] = subjects

        for subject in subjects:
            subject_id = str(subject["subject_id"])
            if subject_id in recent_anchors:
                continue

            chains = list(chain_provider(conn, subject_id) or ())
            eligible = eligible_chains(
                chains,
                recent_anchor_ids=recent_anchors,
                min_depth=2,
            )
            for chain in eligible:
                if str(chain.anchor_id) != subject_id:
                    continue
                material = compile_story_chain(event, chain, mechanic)
                signature = (
                    material["story"]["event_id"],
                    material["answer"]["id"],
                    tuple(
                        (clue.get("relation"), clue.get("object_id"), clue.get("season"))
                        for clue in material["clues"]
                        if clue.get("kind") == "career"
                    ),
                )
                if signature in seen_material:
                    continue
                seen_material.add(signature)
                out.append(material)
                break

            if len(out) >= wanted:
                return out

    return out
