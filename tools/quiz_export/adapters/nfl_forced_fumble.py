"""NFL Forced Fumble -- "who forced the fumble in this real game". See
_defensive_event_common.py for the real, shared logic this file
parameterizes with forced_fumble_player_1_id/forced_fumble_player_1_name_raw
(the primary forcer -- a real second forcer field exists for rare
multi-player strip situations, not used here to keep one clear answer).
"""
from __future__ import annotations

from . import _defensive_event_common as common

OUT_PATH = None
CATEGORY = "NFL Forced Fumbles"
REQUIRED_SOURCE_ID = common.REQUIRED_SOURCE_ID
TRACK_ENTITY = True
ID_COLUMN = "forced_fumble_player_1_id"
NAME_COLUMN = "forced_fumble_player_1_name_raw"


def safety_check(c) -> dict:
    return common.safety_check(c)


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, id_column=ID_COLUMN, name_column=NAME_COLUMN)


def _question(franchise_def, franchise_off, season):
    return f"In this {season} NFL game, the {franchise_def['full_name']} defense faced the {franchise_off['full_name']}. Who forced a fumble?"


def _notes(name, franchise_def, franchise_off, season):
    return f"{name} forced a fumble for the {franchise_def['full_name']} in this {season} game."


def evaluate(c, row, rng, guard):
    return common.evaluate(
        c, row, rng, guard, question_fn=_question, notes_fn=_notes, category=CATEGORY,
        entity_prefix="nfl_ff", name_column=NAME_COLUMN,
    )


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, event_label="forced fumble")


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_forced_fumble.py -- NFL Forced Fumbles.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, event_label="forced fumble")
