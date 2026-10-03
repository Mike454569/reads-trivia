"""Build diverse multi-format Deep Lore rounds."""
from __future__ import annotations

from collections import Counter

from .lore_formats import discover_multiformat_candidates


DEFAULT_FORMAT_ORDER = ("COMMON_LINK", "BEFORE_AFTER", "TIMELINE")


def _event_ids(question):
    prov = question.get("provenance") or {}
    ids = prov.get("event_ids")
    if ids:
        return {str(x) for x in ids}
    return {
        str(h.get("object_id"))
        for h in ((prov.get("chain") or {}).get("hops") or [])
        if h.get("object_type") == "EVENT"
    }


def build_multiformat_bank(
    conn,
    *,
    target=12,
    recent_question_ids=(),
    recent_formats=(),
    max_per_format=None,
    discovery_limit=250,
):
    target = max(1, min(int(target), 100))
    max_per_format = max_per_format or max(2, (target + 2) // 3)
    recent_q = {str(x) for x in recent_question_ids}
    recent_formats = [str(x).upper() for x in recent_formats]

    discovered = discover_multiformat_candidates(conn, limit=discovery_limit)
    pools = {
        key: [
            q for q in discovered.get(key, [])
            if str(q.get("question_id")) not in recent_q
        ]
        for key in DEFAULT_FORMAT_ORDER
    }

    selected = []
    counts = Counter()
    seen_events = set()

    # Round-robin across formats. Recently seen formats go later.
    order = sorted(
        DEFAULT_FORMAT_ORDER,
        key=lambda fmt: (fmt in recent_formats, recent_formats.count(fmt), DEFAULT_FORMAT_ORDER.index(fmt)),
    )

    made_progress = True
    while made_progress and len(selected) < target:
        made_progress = False
        for fmt in order:
            if len(selected) >= target:
                break
            if counts[fmt] >= max_per_format:
                continue
            pool = pools.get(fmt) or []
            while pool:
                q = pool.pop(0)
                ids = _event_ids(q)
                if ids and ids & seen_events:
                    continue
                selected.append(q)
                counts[fmt] += 1
                seen_events.update(ids)
                made_progress = True
                break

    return {
        "target": target,
        "selected": selected,
        "selected_count": len(selected),
        "format_counts": dict(counts),
        "available_counts": {k: len(v) for k, v in discovered.items()},
        "unique_events": len(seen_events),
        "max_per_format": max_per_format,
    }
