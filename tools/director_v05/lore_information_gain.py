"""Empirical clue-reveal calibration using the actual answer-choice set."""
from __future__ import annotations

from .lore_answer_uniqueness import clue_fit_report


def _candidate_match_map(conn, question, candidate_ids):
    reports = {
        str(cid): clue_fit_report(conn, question, cid)
        for cid in candidate_ids
    }
    out = {}
    for relation_index, clue in enumerate(question.get("clues") or []):
        relation = str(clue.get("relation") or "")
        matched = 0
        checked = 0
        for report in reports.values():
            checks = report.get("checks") or []
            # Checks are emitted in selected-clue order.
            if relation_index >= len(checks):
                continue
            check = checks[relation_index]
            if str(check.get("relation") or "") != relation:
                continue
            checked += 1
            if check.get("matched"):
                matched += 1
        out[relation_index] = {
            "relation": relation,
            "distractors_checked": checked,
            "distractors_still_plausible": matched,
            "survival_rate": (matched / checked) if checked else 0.0,
            "information_gain": 1.0 - ((matched / checked) if checked else 0.0),
        }
    return out


def calibrate_reveal_order(conn, question, *, difficulty_band=None):
    """Order clues by observed discriminating power against current distractors."""
    clues = [dict(c) for c in (question.get("clues") or [])]
    if len(clues) < 2:
        return dict(question)

    distractors = question.get("distractors") or []
    ids = [str(d.get("entity_id")) for d in distractors if d.get("entity_id")]
    if not ids:
        return dict(question)

    metrics = _candidate_match_map(conn, question, ids)
    enriched = []
    for i, clue in enumerate(clues):
        metric = metrics.get(i, {
            "survival_rate": 0.0,
            "information_gain": 1.0,
            "distractors_checked": 0,
            "distractors_still_plausible": 0,
        })
        enriched.append({**clue, **metric, "_original_index": i})

    band = str(difficulty_band or question.get("difficulty_band") or "HARD").upper()
    if band == "CASUAL":
        # Most discriminating first.
        enriched.sort(key=lambda c: (-c["information_gain"], c["_original_index"]))
    elif band == "SICKO":
        # Least discriminating first, reveal the giveaway last.
        enriched.sort(key=lambda c: (c["information_gain"], c["_original_index"]))
    elif band == "HARD":
        # Start murky, then ramp toward the strongest clue.
        enriched.sort(key=lambda c: (c["information_gain"], c["_original_index"]))
    else:
        raise ValueError("UNKNOWN_REVEAL_DIFFICULTY_BAND")

    for i, clue in enumerate(enriched):
        clue.pop("_original_index", None)
        clue["reveal_step"] = i + 1

    out = dict(question)
    out["clues"] = enriched
    out["reveal_calibration"] = {
        "method": "DISTRACTOR_SURVIVAL",
        "difficulty_band": band,
        "calibrated": True,
    }
    return out
