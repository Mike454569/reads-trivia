"""Question-writer intelligence for deep lore chains.

Selects the strongest human-readable clues, controls reveal order by difficulty,
and generates deterministic alternate versions without changing the underlying facts.
"""
from __future__ import annotations

import hashlib

BANDS = {
    "CASUAL": {"count": 3, "event_bonus": 4.0, "structure_bonus": 2.0, "target": 35},
    "HARD": {"count": 3, "event_bonus": 3.0, "structure_bonus": 3.0, "target": 65},
    "SICKO": {"count": 3, "event_bonus": 2.0, "structure_bonus": 4.0, "target": 88},
}

RELATION_VALUE = {
    "SUBJECT_OF_EVENT": 8.0,
    "DRAFTED_BY": 6.5,
    "ALL_PRO": 7.0,
    "PRO_BOWL": 6.0,
    "TRANSFERRED_TO": 6.0,
    "STARTED_AT": 5.0,
    "COACHED": 5.5,
    "ROSTERED_BY": 4.5,
    "DRAFTED_PLAYER": 5.5,
    "ROSTERED_PLAYER": 4.5,
    "SCHOOL_PLAYER": 5.0,
    "RANKED": 5.0,
}

WEAK_PHRASES = (
    "career data stands out",
    "notable bust-score profile",
    "notable steal-score profile",
    "unusual draft-value profile",
)


def _score_clue(clue, band):
    cfg = BANDS[band]
    relation = str(clue.get("relation") or "")
    text = str(clue.get("text") or "")
    score = RELATION_VALUE.get(relation, 3.0)

    if relation == "SUBJECT_OF_EVENT":
        score += cfg["event_bonus"]
        if len(text.split()) >= 10:
            score += 1.0
        if any(ch.isdigit() for ch in text):
            score += 0.5
    else:
        score += cfg["structure_bonus"]

    if relation.startswith("DERIVED_"):
        score -= 2.0
    if any(phrase in text.casefold() for phrase in WEAK_PHRASES):
        score -= 2.5
    if len(text.split()) < 5:
        score -= 1.0
    return round(score, 3)


def _semantic_key(clue):
    relation = str(clue.get("relation") or "")
    text = str(clue.get("text") or "").casefold()
    if relation in {"ALL_PRO", "PRO_BOWL"}:
        return "HONOR"
    if relation in {"ROSTERED_BY", "DRAFTED_BY", "DRAFTED_PLAYER", "ROSTERED_PLAYER"}:
        return "NFL_TEAM_HISTORY"
    if relation in {"STARTED_AT", "TRANSFERRED_TO", "SCHOOL_PLAYER"}:
        return "CFB_PATH"
    if relation.startswith("DERIVED_"):
        return "DERIVED"
    if relation == "SUBJECT_OF_EVENT":
        return "LORE_EVENT"
    return relation or text


def select_clues(clues, band="HARD", *, variant=0):
    """Select distinct, high-value clues from already-safe natural-language copy."""
    band = str(band).upper()
    if band not in BANDS:
        raise ValueError("UNKNOWN_WRITER_DIFFICULTY_BAND")
    if not clues:
        raise ValueError("NO_WRITER_CLUES")

    scored = []
    for index, clue in enumerate(clues):
        scored.append({
            **clue,
            "writer_score": _score_clue(clue, band),
            "_index": index,
            "_semantic": _semantic_key(clue),
        })

    # Deterministic variant rotation among similarly valuable clues.
    scored.sort(key=lambda c: (-c["writer_score"], c["_semantic"], c["text"]))
    if variant:
        groups = {}
        for clue in scored:
            groups.setdefault(clue["_semantic"], []).append(clue)
        rotated = []
        for key in sorted(groups):
            group = groups[key]
            shift = int(variant) % len(group)
            rotated.extend(group[shift:] + group[:shift])
        scored = sorted(rotated, key=lambda c: (-c["writer_score"], c["_semantic"], c["text"]))

    picked = []
    used_semantics = set()
    for clue in scored:
        if clue["_semantic"] in used_semantics:
            continue
        picked.append(clue)
        used_semantics.add(clue["_semantic"])
        if len(picked) >= BANDS[band]["count"]:
            break

    if len(picked) < 3:
        for clue in scored:
            if clue in picked:
                continue
            picked.append(clue)
            if len(picked) >= 3:
                break

    if len(picked) < 3:
        raise ValueError("INSUFFICIENT_DISTINCT_WRITER_CLUES")

    # Reveal order: casual gives the story sooner; harder bands save it.
    event = [c for c in picked if c["relation"] == "SUBJECT_OF_EVENT"]
    other = [c for c in picked if c["relation"] != "SUBJECT_OF_EVENT"]
    ordered = (event + other) if band == "CASUAL" else (other + event)

    out = []
    for clue in ordered:
        out.append({
            "relation": clue["relation"],
            "text": clue["text"],
            "source_kind": clue.get("source_kind"),
            "writer_score": clue["writer_score"],
        })
    return out


def variant_id(chain_id, band, variant, clues):
    seed = "|".join(
        [str(chain_id), str(band), str(variant)] + [str(c["text"]) for c in clues]
    )
    return "qwrite_" + hashlib.sha256(seed.encode()).hexdigest()[:24]


def writer_quality(clues):
    """Reject copy that is repetitive, vague, or too structurally homogeneous."""
    if len(clues) < 3:
        return {"status": "FAILED", "errors": ["TOO_FEW_WRITER_CLUES"]}

    errors = []
    texts = [str(c.get("text") or "").strip() for c in clues]
    folded = [t.casefold() for t in texts]
    if len(set(folded)) != len(folded):
        errors.append("DUPLICATE_WRITER_CLUES")

    semantics = {_semantic_key(c) for c in clues}
    if len(semantics) < 2:
        errors.append("LOW_CLUE_VARIETY")

    for text in folded:
        if any(term in text for term in (
            "verified chain", "structured fact", "subject of event",
            "event subject", "selected by rarity rules",
        )):
            errors.append("ROBOTIC_WRITER_COPY")
            break

    if all(len(t.split()) < 6 for t in texts):
        errors.append("CLUES_TOO_THIN")

    return {"status": "PASSED" if not errors else "FAILED", "errors": errors}
