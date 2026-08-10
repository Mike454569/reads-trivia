"""Difficulty normalization.

DIFFICULTY_MAP was identical, byte-for-byte, across all three original
exporters. difficulty_from_puzzle_catalog() is the QB/Championship pattern
of cross-referencing Engine's own pre-existing puzzle_catalog mode for a
difficulty score rather than inventing one -- shared here since the query
shape is identical, only the mode_id/entity match key differ per domain.
Draft sources its difficulty differently (Game Factory's own returned
score via engine.band()) and does not use this helper.
"""
from __future__ import annotations

import json

DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "EXPERT": "Hard"}


def map_band(band: str) -> str:
    return DIFFICULTY_MAP[band]


def difficulty_from_puzzle_catalog(
    c, mode_id: str, entity_id, season: int, required_source: str, expected_answer=None
):
    """Returns {"difficulty_score":..., "difficulty_band":...} or None if no
    matching eligible row exists. If expected_answer is given, the matched
    row's stored answer must equal it exactly, or this returns None."""
    row = c.execute(
        "SELECT difficulty_score, difficulty_band, payload_json FROM puzzle_catalog "
        "WHERE mode_id=? AND source_entity_id=? AND season=? "
        "AND eligible=1 AND verification_status='SOURCE_BACKED' AND source_id=?",
        (mode_id, entity_id, season, required_source),
    ).fetchone()
    if not row:
        return None
    if expected_answer is not None:
        if json.loads(row["payload_json"]).get("answer") != expected_answer:
            return None
    return {"difficulty_score": row["difficulty_score"], "difficulty_band": row["difficulty_band"]}
