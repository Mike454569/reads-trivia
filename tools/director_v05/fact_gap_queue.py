"""Prioritize remaining football-fact gaps by gameplay impact."""
from __future__ import annotations

from .lore_coverage import coverage

GAMEPLAY_UNLOCKS = {
    "TRANSFER": ["Deep Lore", "Career Path", "Common Link", "Before/After"],
    "RECRUITING": ["Deep Lore", "Common Link", "CFB career questions"],
    "CONTRACT": ["Deep Lore", "Timeline", "Before/After", "Common Link"],
    "WEATHER_CHAOS": ["Deep Lore", "Timeline", "Fact or Fake"],
    "RULE_ODDITY": ["Deep Lore", "Fact or Fake", "Timeline"],
    "OFF_FIELD_ODDITY": ["Deep Lore", "Common Link", "Timeline"],
    "PRESS_CONFERENCE": ["Deep Lore", "Common Link", "Timeline"],
    "LEAGUE_DISCIPLINE": ["Deep Lore", "Timeline"],
    "LEGAL_EVENT": ["Deep Lore", "Timeline"],
    "COACHING_MOVE": ["Deep Lore", "Common Link", "Before/After"],
    "HISTORICAL_MILESTONE": ["Timeline", "Before/After", "Common Link"],
}

WEIGHTS = {
    "TRANSFER": 1.4,
    "RECRUITING": 1.4,
    "CONTRACT": 1.3,
    "WEATHER_CHAOS": 1.15,
    "RULE_ODDITY": 1.25,
    "OFF_FIELD_ODDITY": 1.3,
    "PRESS_CONFERENCE": 1.2,
    "COACHING_MOVE": 1.2,
    "HISTORICAL_MILESTONE": 1.15,
    "LEAGUE_DISCIPLINE": 0.8,
    "LEGAL_EVENT": 0.7,
}


def fact_gap_queue(conn):
    cov = coverage(conn)
    queue = []
    for item in cov["priority_gaps"]:
        family = item["family"]
        gap = int(item["gap"])
        if gap <= 0:
            continue
        unlocks = GAMEPLAY_UNLOCKS.get(family, ["Deep Lore"])
        weight = WEIGHTS.get(family, 1.0)
        score = round(gap * weight * (1 + 0.1 * len(unlocks)), 2)
        queue.append({
            "family": family,
            "verified": item["verified"],
            "target": item["target"],
            "gap": gap,
            "coverage": item["coverage"],
            "gameplay_unlocks": unlocks,
            "priority_score": score,
        })
    queue.sort(key=lambda x: (-x["priority_score"], x["family"]))
    return {
        "remaining_families": len(queue),
        "queue": queue,
        "top_five": queue[:5],
    }
