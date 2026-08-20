"""NFL Fumble Recovery -- "who recovered the fumble in this real game". See
_defensive_event_common.py for the real, shared logic this file
parameterizes with fumble_recovery_1_player_id/fumble_recovery_1_player_name_raw.

Deliberately does NOT filter by which team recovered (offense can recover
its own fumble) -- the question asks who recovered it, not which team's
defense did, so this reuses the shared defteam/posteam framing purely for
game context, not as a correctness constraint.
"""
from __future__ import annotations

from . import _defensive_event_common as common

OUT_PATH = None
CATEGORY = "NFL Fumble Recoveries"
REQUIRED_SOURCE_ID = common.REQUIRED_SOURCE_ID
TRACK_ENTITY = True
ID_COLUMN = "fumble_recovery_1_player_id"
NAME_COLUMN = "fumble_recovery_1_player_name_raw"


def safety_check(c) -> dict:
    return common.safety_check(c)


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, id_column=ID_COLUMN, name_column=NAME_COLUMN)


def _question(franchise_def, franchise_off, season):
    return f"In this {season} NFL game between the {franchise_def['full_name']} and the {franchise_off['full_name']}, who recovered a fumble?"


def _notes(name, franchise_def, franchise_off, season):
    return f"{name} recovered a fumble in this {season} game between the {franchise_def['full_name']} and the {franchise_off['full_name']}."


def evaluate(c, row, rng, guard):
    return common.evaluate(
        c, row, rng, guard, question_fn=_question, notes_fn=_notes, category=CATEGORY,
        entity_prefix="nfl_fr", name_column=NAME_COLUMN,
    )


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, event_label="fumble recovery")


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_fumble_recovery.py -- NFL Fumble Recoveries.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, event_label="fumble recovery")
