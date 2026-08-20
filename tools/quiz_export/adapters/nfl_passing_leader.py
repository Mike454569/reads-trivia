"""NFL game passing leader -- objective "top offensive performer" (passing
category). See _nfl_game_leader_common.py for the real, shared logic.
"""
from __future__ import annotations

from . import _nfl_game_leader_common as common

OUT_PATH = None
CATEGORY = "NFL Game Passing Leader"
TRACK_ENTITY = True
STAT_COLUMN = "pass_yards"
ATTEMPT_COLUMN = "pass_attempts"
STAT_LABEL = "passing yards"


def safety_check(c) -> dict:
    return common.safety_check(c, attempt_column=ATTEMPT_COLUMN)


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, stat_column=STAT_COLUMN, attempt_column=ATTEMPT_COLUMN)


def evaluate(c, row, rng, guard):
    return common.evaluate(c, row, rng, guard, stat_column=STAT_COLUMN, stat_label=STAT_LABEL, category=CATEGORY, entity_prefix="nfl_pass_ldr")


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, stat_label=STAT_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return ["// Director-pipeline-only domain.", "// tools/quiz_export/adapters/nfl_passing_leader.py.", f"// Deterministic seed: \"{seed}\"."]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, stat_label=STAT_LABEL)
