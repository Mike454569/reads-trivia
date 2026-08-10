"""Duplicate tracking.

The framework does not impose a global uniqueness rule -- it only tracks
whatever an adapter asks it to. Question-text tracking is used by all three
domains (every original script deduped on exact question text). Entity
tracking (e.g. player_key / qb_source_id) is opt-in per adapter: Draft and
QB both want unique-entity-per-export; Championship deliberately does not
(each team-season is an independently distinct fact -- see
QUIZ_ENGINE_CHAMPIONSHIP_AWARD_PILOT_REPORT.md).
"""
from __future__ import annotations

from collections import Counter


class DuplicateGuard:
    def __init__(self, track_entity: bool = True):
        self.track_entity = track_entity
        self.seen_questions: set = set()
        self.seen_entities: set = set()

    def entity_seen(self, entity_key) -> bool:
        return self.track_entity and entity_key is not None and entity_key in self.seen_entities

    def question_seen(self, question: str) -> bool:
        return question in self.seen_questions

    def record(self, question: str, entity_key=None) -> None:
        self.seen_questions.add(question)
        if self.track_entity and entity_key is not None:
            self.seen_entities.add(entity_key)


def find_duplicates(records: list, key_fn) -> list:
    counts = Counter(key_fn(r) for r in records)
    return [k for k, n in counts.items() if n > 1]
