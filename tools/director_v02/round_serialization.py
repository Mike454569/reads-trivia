"""Server-private vs client-safe round serialization -- Phase 2.

Real discovery made before writing anything new here: a mature, real,
already-proven private/public separation already exists for the multiple-
choice mechanic -- `gateway/services/public_game.py`'s `_public_view()`
(an ALLOW-list, not a deny-list -- see that module's own docstring) and
`validate_public_answer()` (server-side answer evaluation; the correct
answer is only ever revealed to a client AFTER a real guess is submitted).
`game_id` there is already an opaque round id (`stored["package_id"]`, a
real SHA-256-derived id, never a raw index).

This module does NOT reimplement or fork that system -- doing so would
create two competing sources of truth for the exact thing this reliability
design exists to make trustworthy. Instead it:
  1. Names, in one place, the exact fields that must never appear in a
     client-safe payload (the literal list requested: correct_index,
     correct_entity, correct_pairing_map, correct_order, correct_higher,
     is_member, accepted-answer arrays, internal answer-normalization
     fields -- plus this Engine's own real equivalents, correctIndex/
     answer/notes/_audit).
  2. Provides a real, recursive assertion helper so both tests AND the
     Tier-1 health probe (health_probe.py) can verify a served payload
     against that list mechanically, not by manual inspection each time.

Scope note: `identify_player_from_clues` packages are NOT currently served
through any public route at all (`public_game.py`'s own
`KNOWN_NOT_YET_PUBLIC_MODES`) -- a real, pre-existing, honest scope
boundary, not something Phase 2 expands. This module still defines that
mechanic's own private-only field names (`correct_entity`) so the leakage
check is ready the moment that mechanic does get a public route, and so its
RAW package generation can be checked for a different, real leak class in
the meantime: clue text that spoils its own answer.
"""
from __future__ import annotations

# The literal field-name list from the approved design, plus this Engine's
# own real field names for the two mechanics that exist today.
SERVER_PRIVATE_ONLY_FIELDS = frozenset({
    "correctIndex", "correct_index",
    "answer", "correct_entity", "correct_answer_text",
    "correct_pairing_map", "correct_order", "correct_higher", "is_member",
    "accepted_answers", "accepted_answer", "accepted_answer_texts",
    "notes", "_audit",
    "normalized_answer", "answer_normalization",
})

# Fields that ARE allowed to carry the correct answer text, but only in a
# specific, well-known context: the response to a real answer submission
# (public_game.validate_public_answer's own "canonical_answer" reveal-
# after-guessing field). Never checked against a pre-answer served payload.
POST_ANSWER_REVEAL_FIELDS = frozenset({"canonical_answer", "correct"})


class LeakedFieldError(AssertionError):
    pass


def assert_no_leaked_fields(payload, *, path: str = "$") -> None:
    """Recursively walks a served client payload (dict/list/scalar) and
    raises LeakedFieldError naming the exact key + path if any
    SERVER_PRIVATE_ONLY_FIELDS key is present anywhere in it -- nested
    dicts/lists included, since a leak one level deep is just as real."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in SERVER_PRIVATE_ONLY_FIELDS:
                raise LeakedFieldError(f"leaked field {key!r} at {path}.{key}")
            assert_no_leaked_fields(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for i, item in enumerate(payload):
            assert_no_leaked_fields(item, path=f"{path}[{i}]")
    # scalars: nothing to check


def clue_text_leaks_answer(clue_text: str, answer_name: str) -> bool:
    """The real, mechanic-specific leak class for progressive-clue-reveal:
    a clue whose own text contains the literal answer name substring. Case-
    insensitive, checks the full name and (if it has multiple words) the
    last name alone -- a clue naming "Mahomes" spoils "Patrick Mahomes"
    just as much as the full name would."""
    if not clue_text or not answer_name:
        return False
    clue_lower = clue_text.lower()
    name_lower = answer_name.lower()
    if name_lower in clue_lower:
        return True
    parts = name_lower.split()
    if len(parts) > 1 and parts[-1] in clue_lower:
        return True
    return False
