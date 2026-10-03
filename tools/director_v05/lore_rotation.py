"""Diversity and rotation policy for Deep Lore question banks."""
from __future__ import annotations

from collections import Counter

from .lore_coverage import TYPE_MAP
from .lore_taxonomy import EVENT_FAMILIES

EVENT_TO_FAMILY = {}
for _family, _types in TYPE_MAP.items():
    for _typ in _types:
        EVENT_TO_FAMILY[_typ] = _family
for _family in EVENT_FAMILIES:
    EVENT_TO_FAMILY.setdefault(_family, _family)

SENSITIVE_FAMILIES = {
    name for name, cfg in EVENT_FAMILIES.items() if cfg.get("sensitive")
}


def event_family(event_type):
    return EVENT_TO_FAMILY.get(str(event_type or "").upper(), str(event_type or "UNKNOWN").upper())


def question_lore_profile(conn, question):
    """Describe the lore families/leagues represented by a compiled chain question."""
    chain = ((question.get("provenance") or {}).get("chain") or {})
    event_ids = [
        str(h.get("object_id"))
        for h in chain.get("hops") or []
        if h.get("object_type") == "EVENT" and h.get("object_id") is not None
    ]
    if not event_ids:
        return {
            "event_ids": [],
            "families": [],
            "leagues": [],
            "sensitive": False,
            "primary_family": "STRUCTURED_ONLY",
        }

    placeholders = ",".join("?" for _ in event_ids)
    rows = conn.execute(
        f"""SELECT event_id,event_type,league
            FROM universal_event
            WHERE event_id IN ({placeholders})
            ORDER BY event_id""",
        event_ids,
    ).fetchall()
    families = []
    leagues = []
    for row in rows:
        fam = event_family(row["event_type"])
        if fam not in families:
            families.append(fam)
        league = str(row["league"] or "UNKNOWN")
        if league not in leagues:
            leagues.append(league)

    return {
        "event_ids": event_ids,
        "families": families,
        "leagues": leagues,
        "sensitive": any(f in SENSITIVE_FAMILIES for f in families),
        "primary_family": families[0] if families else "UNKNOWN",
    }


def rotation_score(
    question,
    profile,
    *,
    family_counts,
    league_counts,
    recent_families=(),
    family_targets=None,
):
    """Higher means the question improves bank variety more."""
    family_targets = family_targets or {}
    score = float(question.get("rarity_score") or 0) * 1.5
    score += float(question.get("difficulty_score") or 0) / 25.0

    for family in profile["families"]:
        current = family_counts.get(family, 0)
        target = max(1, int(family_targets.get(family, 1)))
        # Strong first-use bonus, then diminishing returns.
        score += max(0.0, 7.0 * (1.0 - current / target))
        if family in recent_families:
            score -= 5.0

    for league in profile["leagues"]:
        # Push the currently under-served league upward.
        score += max(0.0, 3.0 - float(league_counts.get(league, 0)))

    if len(profile["families"]) > 1:
        score += 1.5
    if profile["sensitive"]:
        # Sensitive lore can appear, but never wins only because it is rare.
        score -= 2.0
    return round(score, 4)


def select_rotated_questions(
    conn,
    candidates,
    *,
    target,
    recent_families=(),
    max_per_family=None,
    max_sensitive=1,
    require_league_balance=True,
    max_per_answer=1,
    max_per_signature=3,
    no_repeat_events=True,
):
    """Greedy diversity scheduler with explicit family and sensitive-content caps."""
    target = max(1, int(target))
    recent_families = tuple(str(x) for x in recent_families)
    max_per_family = max_per_family or max(2, (target + 3) // 4)

    prepared = []
    all_families = Counter()
    for q in candidates:
        profile = question_lore_profile(conn, q)
        for family in profile["families"]:
            all_families[family] += 1
        prepared.append((q, profile))

    # Aim for at least one from every available family before repeats dominate.
    family_targets = {
        family: min(max_per_family, max(1, target // max(1, len(all_families))))
        for family in all_families
    }

    selected = []
    family_counts = Counter()
    league_counts = Counter()
    answer_counts = Counter()
    signature_counts = Counter()
    selected_events = set()
    sensitive_count = 0
    remaining = list(prepared)

    while remaining and len(selected) < target:
        ranked = []
        for q, profile in remaining:
            if profile["sensitive"] and sensitive_count >= max_sensitive:
                continue
            if profile["families"] and any(
                family_counts[f] >= max_per_family for f in profile["families"]
            ):
                continue

            answer_id = str((q.get("answer") or {}).get("id") or "")
            if not answer_id or answer_counts[answer_id] >= max_per_answer:
                continue
            signature = tuple(sorted(
                str(c.get("relation") or "")
                for c in (q.get("clues") or [])
            ))
            if signature_counts[signature] >= max_per_signature:
                continue
            event_ids = set(profile.get("event_ids") or [])
            if no_repeat_events and event_ids and event_ids & selected_events:
                continue

            score = rotation_score(
                q,
                profile,
                family_counts=family_counts,
                league_counts=league_counts if require_league_balance else {},
                recent_families=recent_families,
                family_targets=family_targets,
            )
            ranked.append((score, q["question_id"], q, profile))

        if not ranked:
            break
        _, _, chosen, profile = max(ranked, key=lambda x: (x[0], x[1]))
        selected.append(chosen)
        answer_id = str((chosen.get("answer") or {}).get("id") or "")
        signature = tuple(sorted(
            str(c.get("relation") or "")
            for c in (chosen.get("clues") or [])
        ))
        answer_counts[answer_id] += 1
        signature_counts[signature] += 1
        selected_events.update(profile.get("event_ids") or [])
        for family in profile["families"]:
            family_counts[family] += 1
        for league in profile["leagues"]:
            league_counts[league] += 1
        if profile["sensitive"]:
            sensitive_count += 1
        remaining = [(q, p) for q, p in remaining if q["question_id"] != chosen["question_id"]]

    return {
        "selected": selected,
        "family_counts": dict(family_counts),
        "league_counts": dict(league_counts),
        "sensitive_count": sensitive_count,
        "available_family_counts": dict(all_families),
        "max_per_family": max_per_family,
        "max_sensitive": max_sensitive,
        "answer_counts": dict(answer_counts),
        "signature_counts": {str(k): v for k, v in signature_counts.items()},
        "selected_event_count": len(selected_events),
    }
